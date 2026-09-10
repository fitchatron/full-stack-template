from __future__ import annotations
from typing import Any, Generic, Optional, Type, TypeVar
import json
from sqlalchemy import and_, or_, between
from sqlalchemy.sql import operators
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.elements import KeyedColumnElement
from app.schemas.filter_generator import (
    ComparisonOperator,
    CompoundOperator,
    FilterCompoundCondition,
    FilterCondition,
    FilterPayload,
)
from app.utils.model import ModelAttributeUtils

ModelType = TypeVar("ModelType")
Schema = TypeVar("Schema")


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


def value_to_primitive(value: Optional[str]) -> Any:
    """Convert a string value to its primitive type."""
    if not value:
        return None

    if isinstance(value, list):
        raise ValueError("Arrays are not primitives")

    if isinstance(value, dict):
        raise ValueError("Dictionaries are not primitives")

    # Try parsing as null
    if value.lower() == "null":
        return None

    # Try parsing as boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Try parsing as integer
    try:
        int_value = int(value)
        if str(int_value) == value:
            return int_value
    except ValueError:
        pass

    # Try parsing as float
    try:
        float_value = float(value)
        if str(float_value) == value:
            return float_value
    except ValueError:
        pass

    # Return the value with quotes removed
    return value.replace('"', "")


def type_column_value(value: str, operator: str) -> Any:
    """Convert a string value to the appropriate type based on the operator."""
    if operator in ("between", "in", "not_in"):
        try:
            return json.loads(value)
        except Exception:
            raise ValueError("Error parsing JSON filter value")

    return value_to_primitive(value)


def parse_filter_string_to_filter_condition(
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
        value=type_column_value(value, operator_str),
    )


def parse_filter_string_to_filter_compound_condition(
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
        raise ValueError("Malformed compound Query filter: len of ( does not match )")
    # Don't forget the last item
    if current_item:
        condition_items.append(current_item)

    conditions: list[FilterCondition | FilterCompoundCondition] = []
    for item in condition_items:
        if not item.startswith("and(") and not item.startswith("or("):
            conditions.append(parse_filter_string_to_filter_condition(item, config))
        else:
            conditions.append(
                parse_filter_string_to_filter_compound_condition(item, config)
            )

    return FilterCompoundCondition(
        operator=CompoundOperator(operator_str),
        conditions=conditions,
    )


def parse_param_to_filter_payload(
    filter_string: Optional[str] = None,
    config: SeparatorConfig = SeparatorConfig(),
) -> Optional[FilterPayload]:
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
        filter_condition = parse_filter_string_to_filter_condition(
            filter_string, config
        )
        return FilterPayload(where=filter_condition)

    filter_condition = parse_filter_string_to_filter_compound_condition(
        filter_string, config
    )
    return FilterPayload(where=filter_condition)


class FilterGenerator(Generic[ModelType, Schema]):

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
        model: Type[ModelType],
        column_mapping: dict[str, KeyedColumnElement] = {},
    ) -> None:
        self.model = model
        self.model_attribute_utils = ModelAttributeUtils(model=model)
        self.column_mapping = column_mapping

    def generate_filter(
        self, condition: FilterCondition | FilterCompoundCondition
    ) -> ColumnElement[bool]:
        if isinstance(condition, FilterCondition):
            attr = (
                self.column_mapping.get(condition.column, None)
                if self.column_mapping.get(condition.column, None) is not None
                else self.model_attribute_utils.parse_column_to_attribute(
                    condition.column
                )
            )
            op = condition.operator
            value = condition.value

            if op == "between":
                start = value[0]  # type: ignore
                end = value[1]  # type: ignore

                # if any of the inputs are numeric, cast them to a float so the SQL engine can cast the column reliably to a float
                if (
                    isinstance(start, int)
                    or isinstance(start, float)
                    or isinstance(end, int)
                    or isinstance(end, float)
                ):
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

    def build_filter(self, payload: FilterPayload):
        return self.generate_filter(payload.where)
