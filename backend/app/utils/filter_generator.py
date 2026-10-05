from __future__ import annotations

import json
import math
import re
from decimal import Decimal, InvalidOperation
from typing import Any, TypeVar

from sqlalchemy import and_, between, or_
from sqlalchemy.sql import operators
from sqlalchemy.sql.elements import ColumnElement, KeyedColumnElement

from app.schemas.filter_generator import (
    ComparisonOperator,
    CompoundOperator,
    FilterCompoundCondition,
    FilterCondition,
    FilterPayload,
)
from app.utils.column_path_resolver import ColumnPathResolver

ModelType = TypeVar("ModelType")

_INT_PATTERN = re.compile(r"[+-]?[0-9]+")
_FLOAT_PATTERN = re.compile(r"[+-]?([0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)([eE][+-]?[0-9]+)?")


class SeparatorConfig:
    """Configuration for filter string separators."""

    def __init__(
        self,
        key_value_separator: str = "~",
        item_separator: str = ";",
        array_separator: str = ",",
    ):
        self.key_value_separator = key_value_separator
        self.item_separator = item_separator
        self.array_separator = array_separator


def _val_to_primitive(value: str | None) -> Any:
    """Convert a string value to its primitive type."""
    if not value:
        return None

    try:
        parsed_value = json.loads(value)

        if isinstance(parsed_value, (list)):
            raise ValueError("Arrays are not primitives")

        if isinstance(parsed_value, dict):
            raise ValueError("Dictionaries are not primitives")
    except json.JSONDecodeError, TypeError:
        pass

    # Try parsing as null
    if value.lower() == "null":
        return None

    # Try parsing as boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Try parsing as integer, then float
    if _INT_PATTERN.fullmatch(value):
        return int(value)
    if _FLOAT_PATTERN.fullmatch(value):
        return float(value)

    # Return the value with quotes removed
    return value.replace('"', "")


class FilterGenerator[ModelType]:
    # Map comparison operators to SQLAlchemy expressions
    COMPARISON_OPERATORS = {
        "eq": operators.eq,
        "ne": operators.ne,
        "lt": operators.lt,
        "le": operators.le,
        "gt": operators.gt,
        "ge": operators.ge,
        "like": operators.like_op,
        "ilike": operators.ilike_op,
        "in": operators.in_op,
        "not_in": operators.notin_op,
        "between": between,
    }

    def __init__(
        self,
        model: type[ModelType],
        column_mapping: dict[str, KeyedColumnElement] | None = None,
    ) -> None:
        self.model = model
        self.column_path_resolver = ColumnPathResolver(model=model)
        self.column_mapping = column_mapping or {}

    # Pattern operators compare against a string pattern, never the column's own type
    PATTERN_OPERATORS = ("like", "ilike")

    def _type_col_val(self, value: str, operator: str) -> Any:
        """Split a query-string value into a scalar or list, leaving the typing to the column.

        Scalars stay as raw strings (apart from null and surrounding quotes) and list numbers
        are kept as their original text, so values like "00501" or "0.1" survive until
        _coerce_to_column_type knows what type the column needs.
        """

        if operator in ("between", "in", "not_in"):
            try:
                parsed_value = json.loads(value, parse_int=str, parse_float=str)

                if not isinstance(parsed_value, list):
                    raise ValueError(
                        "Expected a list for operator 'between', 'in', or 'not_in'"
                    )

                return parsed_value
            except json.JSONDecodeError, TypeError:
                raise ValueError(
                    "Expected a list for operator 'between', 'in', or 'not_in'"
                )

        if not value or value.lower() == "null":
            return None

        if len(value) >= 2 and value[0] == value[-1] == '"':
            return value[1:-1]

        return value

    def _parse_filter_str_to_filter_condition(
        self,
        filter_string: str,
        config: SeparatorConfig = SeparatorConfig(),
    ) -> FilterCondition:
        """Parse a simple filter string to a FilterCondition."""

        parts = filter_string.split(config.key_value_separator)
        if len(parts) != 3:
            raise ValueError(
                f"Filter string is malformed. It must contain 3 parts not {len(parts)}"
            )
        column = parts[0]
        operator_str = parts[1]
        value = parts[2]

        return FilterCondition(
            column=column,
            operator=ComparisonOperator(operator_str),
            value=self._type_col_val(value, operator_str),
        )

    def _parse_filter_str_to_filter_compound_condition(
        self,
        filter_string: str,
        config: SeparatorConfig = SeparatorConfig(),
    ) -> FilterCompoundCondition:
        """Parse a compound filter string to a FilterCompoundCondition."""

        start_group_char = "("
        end_group_char = ")"

        start_index = filter_string.index(start_group_char)
        end_index = filter_string.rfind(end_group_char)
        operator_str = filter_string[:start_index]
        conditions_str = filter_string[start_index + 1 : end_index]

        # Split by item_separator but respect parentheses nesting
        condition_items: list[str] = []
        current_item = ""
        depth = 0

        for char in conditions_str:
            if char == start_group_char:
                depth += 1
                current_item += char
            elif char == end_group_char:
                depth -= 1
                if depth < 0:
                    raise ValueError(
                        "Malformed compound Query filter: len of ( does not match )"
                    )
                current_item += char
            elif char == config.item_separator and depth == 0:
                # Only split when at top level (depth 0)
                condition_items.append(current_item)
                current_item = ""
            else:
                current_item += char

        if depth != 0:
            raise ValueError(
                "Malformed compound Query filter: len of ( does not match )"
            )
        # Don't forget the last item
        if current_item:
            condition_items.append(current_item)

        conditions: list[FilterCondition | FilterCompoundCondition] = []
        for item in condition_items:
            if not item.startswith("and(") and not item.startswith("or("):
                conditions.append(
                    self._parse_filter_str_to_filter_condition(item, config)
                )
            else:
                conditions.append(
                    self._parse_filter_str_to_filter_compound_condition(item, config)
                )

        return FilterCompoundCondition(
            operator=CompoundOperator(operator_str),
            conditions=conditions,
        )

    def _is_int_or_float(self, value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _to_number(self, value: Any, python_type: type) -> int | float | Decimal:
        """Convert a value to int, float or Decimal without losing or inventing precision."""
        error = ValueError(f"{value!r} is not a valid {python_type.__name__}")

        # bool is a subclass of int, but True should never quietly become 1
        if isinstance(value, bool):
            raise error

        if python_type is float:
            try:
                result = float(value)
            except ValueError, TypeError:
                raise error
            if not math.isfinite(result):
                raise error
            return result

        # str() first so a float like 0.1 becomes Decimal("0.1"), not its binary expansion
        try:
            number = Decimal(str(value))
        except InvalidOperation:
            raise error
        if not number.is_finite():
            raise error

        if python_type is int:
            # reject 1.5 rather than truncating it to 1
            if number != number.to_integral_value():
                raise error
            return int(number)

        return number

    def _coerce_to_column_type(self, attr: Any, value: Any) -> Any:
        """Convert a parsed filter value to the Python type of the column it's compared against."""
        if value is None:
            return None

        if isinstance(value, list):
            return [self._coerce_to_column_type(attr, v) for v in value]

        try:
            python_type = attr.type.python_type
        except NotImplementedError:
            # e.g. JSON_VALUE(...) has no known type, so fall back to guessing
            return _val_to_primitive(value) if isinstance(value, str) else value

        if python_type is str:
            if isinstance(value, bool):
                return "true" if value else "false"
            return str(value)

        if python_type is bool:
            # bool("false") is True, so don't call bool() on the string
            result = _val_to_primitive(str(value))
            if not isinstance(result, bool):
                raise ValueError(f"{value!r} is not a valid boolean")
            return result

        if python_type in (int, float, Decimal):
            return self._to_number(value, python_type)

        # datetime, UUID, etc.: SQLAlchemy and the driver handle ISO strings and UUID strings
        return value

    def generate_filter(
        self, condition: FilterCondition | FilterCompoundCondition
    ) -> ColumnElement[bool]:
        if isinstance(condition, FilterCondition):
            attr = (
                self.column_mapping.get(condition.column, None)
                if self.column_mapping.get(condition.column, None) is not None
                else self.column_path_resolver.parse_col_to_attr(condition.column)
            )
            op = condition.operator

            if op in self.PATTERN_OPERATORS:
                value = None if condition.value is None else str(condition.value)
            else:
                value = self._coerce_to_column_type(attr, condition.value)

            if op == "between":
                if not isinstance(value, list):
                    raise ValueError("Between needs a list of two values")
                start, end = value[0], value[1]

                # if any of the inputs are numeric, cast them to a float so the SQL engine can cast the column reliably to a float
                if self._is_int_or_float(start) or self._is_int_or_float(end):
                    start = float(start)
                    end = float(end)
                return attr.between(start, end)  # type: ignore

            return self.COMPARISON_OPERATORS[op](attr, value)

        elif isinstance(condition, FilterCompoundCondition):
            op = condition.operator
            compound_conditions = condition.conditions

            if op == "and":
                return and_(*[self.generate_filter(c) for c in compound_conditions])
            elif op == "or":
                return or_(*[self.generate_filter(c) for c in compound_conditions])

        raise ValueError(f"Unsupported logical operator: {op}")

    def parse_param_to_filter_payload(
        self,
        filter_string: str | None = None,
        config: SeparatorConfig = SeparatorConfig(),
    ) -> FilterPayload | None:
        """Parse a filter string parameter to a FilterPayload.

        Args:
            filter_string: The filter string to parse (e.g., "column~eq~value" or "and(col1~eq~val1;col2~gt~val2)")
            config: Optional configuration for separators

        Returns:
            FilterPayload with the parsed filter condition, or None if filter_string is empty
        """
        if not filter_string:
            return None

        if not filter_string.startswith("and(") and not filter_string.startswith("or("):
            filter_condition = self._parse_filter_str_to_filter_condition(
                filter_string, config
            )
            return FilterPayload(where=filter_condition)

        filter_condition = self._parse_filter_str_to_filter_compound_condition(
            filter_string, config
        )
        return FilterPayload(where=filter_condition)

    def build_filter(self, payload: FilterPayload) -> ColumnElement[bool]:
        return self.generate_filter(payload.where)
