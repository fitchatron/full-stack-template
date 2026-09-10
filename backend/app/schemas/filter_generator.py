from __future__ import annotations
from enum import Enum
from typing import Any, Optional, Annotated
from pydantic import Field, field_validator
from pydantic_core.core_schema import FieldValidationInfo
from app.schemas.base import BaseSchemaModel


class ComparisonOperator(str, Enum):
    """
    Represents an operator that can be applied to a filter clause
    """

    eq_ = "eq"
    ne_ = "ne"
    lt_ = "lt"
    le_ = "le"
    gt_ = "gt"
    ge_ = "ge"
    like_ = "like"
    ilike_ = "ilike"
    in_ = "in"
    not_in_ = "not_in"
    between_ = "between"


class CompoundOperator(str, Enum):
    """
    Represents an operator that can be applied to a compound clause e.g. and, or
    """

    or_ = "or"
    and_ = "and"


class FilterCondition(BaseSchemaModel):
    """
    Represents a filter condition
    """

    column: Annotated[
        str,
        Field(
            description="the column that you want to filter",
            examples=[
                "prediction_id",
                "email",
                "prediction_payload->mrn",
                "prediction_value.name",
            ],
        ),
    ]
    operator: Annotated[
        ComparisonOperator,
        Field(
            description="The operator to be used in the filter",
            examples=["eq", "nq", "between"],
        ),
    ]
    value: Annotated[
        Optional[str | int | float | bool | list[Any] | bytes],
        Field(
            description="The value that you want to filter on",
            examples=["will", 2, True, [1, 45, 23]],
        ),
    ]

    @field_validator("value")
    @classmethod
    def validate_value_for_operator(cls, v, info: FieldValidationInfo):
        op: ComparisonOperator | None = info.data.get("operator")
        if not op:
            raise ValueError("no operator")

        if op not in ["in", "not_in", "between"] and isinstance(v, list):
            raise ValueError(f"Operator '{op}' requires a single of value")

        if op in ["in", "not_in", "between"]:
            if not isinstance(v, list):
                raise ValueError(f"Operator '{op}' requires a list of values")

            if op == "between":
                if len(v) != 2:
                    raise ValueError("Operator 'between' requires exactly two values")

        return v


class FilterCompoundCondition(BaseSchemaModel):
    """
    Represents a compound filter condition
    """

    operator: Annotated[
        CompoundOperator,
        Field(
            description="The operator to be used in the filter",
            examples=[
                "and",
                "or",
            ],
        ),
    ]
    conditions: Annotated[
        list[FilterCondition | FilterCompoundCondition],
        Field(
            description="Compound filter options. Can be a filter condition or another nested compound condition",
            examples=[
                {"column": "prediction_id", "operator": "eq", "value": 1},
                {
                    "operator": "and",
                    "conditions": [
                        {"column": "id", "operator": "eq", "value": 1},
                        {"column": "status", "operator": "eq", "value": "closed"},
                    ],
                },
            ],
        ),
    ]

    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, v, info: FieldValidationInfo):
        if len(v) < 2:
            raise ValueError("provide at least 2 conditions")

        return v


class FilterPayload(BaseSchemaModel):
    """
    Represents a filter payload from a request
    """

    where: Annotated[
        FilterCondition | FilterCompoundCondition,
        Field(
            description="The where clause in JSON to convert into s sqlalchemy filter",
            examples=[
                {"column": "prediction_id", "operator": "ne", "value": "1"},
                {
                    "operator": "or",
                    "conditions": [
                        {"column": "id", "operator": "eq", "value": 1},
                        {"column": "status", "operator": "eq", "value": "closed"},
                    ],
                },
            ],
        ),
    ]
