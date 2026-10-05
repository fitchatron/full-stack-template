import pytest
from pydantic import TypeAdapter

from app.models.model import Permission, Role, User
from app.schemas.order_by_generator import OrderByCondition, OrderOperator
from app.utils.order_by_generator import (
    OrderByGenerator,
    parse_param_to_order_by_condition,
)


@pytest.mark.parametrize(
    "param, expected_order_by_condition",
    [
        (
            "latest_review.status.name:desc",
            [
                OrderByCondition(
                    column="latest_review.status.name", orientation=OrderOperator.desc_
                )
            ],
        ),
        (
            "predicted_at:desc,prediction_id:asc",
            [
                OrderByCondition(
                    column="predicted_at", orientation=OrderOperator.desc_
                ),
                OrderByCondition(
                    column="prediction_id", orientation=OrderOperator.asc_
                ),
            ],
        ),
        (
            "reviewed_at:desc,prediction_review_id:asc",
            [
                OrderByCondition(column="reviewed_at", orientation=OrderOperator.desc_),
                OrderByCondition(
                    column="prediction_review_id", orientation=OrderOperator.asc_
                ),
            ],
        ),
        (
            "user_id:desc,created_at:asc,modified_by:desc,modified_at:desc",
            [
                OrderByCondition(column="user_id", orientation=OrderOperator.desc_),
                OrderByCondition(column="created_at", orientation=OrderOperator.asc_),
                OrderByCondition(column="modified_by", orientation=OrderOperator.desc_),
                OrderByCondition(column="modified_at", orientation=OrderOperator.desc_),
            ],
        ),
    ],
)
def test_parse_param_to_order_by_condition(param, expected_order_by_condition):
    """
    Test parse_param_to_order_by_condition

    GIVEN a order by query param
    WHEN calling parse_param_to_order_by_condition with a param
    THEN return an array of OrderByCondition
    """

    conditions = parse_param_to_order_by_condition(param=param)
    assert expected_order_by_condition == conditions


@pytest.mark.parametrize(
    "model, data, expected_order_by",
    [
        (
            User,
            {
                "order_by": [
                    {"column": "email", "orientation": "asc"},
                    {"column": "user_id", "orientation": "desc"},
                ]
            },
            [User.email.asc(), User.user_id.desc()],
        ),
        (
            Role,
            {
                "order_by": [
                    {"column": "name", "orientation": "desc"},
                    {"column": "description", "orientation": "asc"},
                ]
            },
            [Role.name.desc(), Role.description.asc()],
        ),
        (
            Permission,
            {"order_by": [{"column": "action", "orientation": "desc"}]},
            [Permission.action.desc()],
        ),
        (
            Permission,
            {"order_by": [{"column": "action", "orientation": "desc"}]},
            [Permission.action.desc()],
        ),
    ],
)
def test_order_by_generator_build_order_conditional(model, data, expected_order_by):
    """
    Test OrderByGenerator.build_order_conditional

    GIVEN a model and a payload
    WHEN calling OrderByGenerator.build_order_conditional
    THEN return a sqlalchemy order_by conditional that matches the input
    """

    payload = TypeAdapter(list[OrderByCondition]).validate_python(data["order_by"])
    generator = OrderByGenerator(model=model)
    generated_order = generator.build_order_conditional(payload)

    assert len(generated_order) == len(expected_order_by)

    for generated, expected in zip(generated_order, expected_order_by, strict=False):
        assert generated.compare(expected), f"{generated} != {expected}"
