import pytest
from app.schemas.order_by_generator import OrderByCondition, OrderOperator


@pytest.mark.static
@pytest.mark.parametrize(
    "enum, operator",
    [
        (OrderOperator.asc_, "asc"),
        (OrderOperator.desc_, "desc"),
    ],
)
def test_order_operator(enum, operator):
    """
    Test OrderOperator enum

    GIVEN a valid OrderOperator string value
    WHEN comparing to OrderOperator enum value
    THEN return a true
    """

    assert enum == operator


@pytest.mark.static
@pytest.mark.parametrize(
    "data",
    [
        {"column": "email", "orientation": "asc"},
        {"column": "prediction_payload.something", "orientation": "desc"},
    ],
)
def test_valid_filter_condition(data):
    """
    Test FilterCompoundCondition model

    GIVEN a valid payload
    WHEN calling FilterCompoundCondition.model_validate_json
    THEN return a validated FilterCompoundCondition
    """

    OrderByCondition(**data)
