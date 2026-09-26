import pytest
from app.schemas.filter_generator import (
    ComparisonOperator,
    FilterCondition,
    FilterCompoundCondition,
    FilterPayload,
)


@pytest.mark.static
@pytest.mark.parametrize(
    "enum, operator",
    [
        (ComparisonOperator.eq_, "eq"),
        (ComparisonOperator.ne_, "ne"),
        (ComparisonOperator.lt_, "lt"),
        (ComparisonOperator.le_, "le"),
        (ComparisonOperator.gt_, "gt"),
        (ComparisonOperator.ge_, "ge"),
        (ComparisonOperator.like_, "like"),
        (ComparisonOperator.ilike_, "ilike"),
        (ComparisonOperator.in_, "in"),
        (ComparisonOperator.not_in_, "not_in"),
        (ComparisonOperator.between_, "between"),
    ],
)
def test_comparision_operator(enum, operator):
    """
    Test ComparisonOperator enum

    GIVEN a valid ComparisonOperator string value
    WHEN comparing to ComparisonOperator enum value
    THEN return a true
    """

    assert enum == operator


@pytest.mark.static
@pytest.mark.parametrize(
    "data",
    [
        {"column": "prediction_id", "operator": "eq", "value": 1},
        {"column": "prediction_id", "operator": "eq", "value": "1"},
        {"column": "model_id", "operator": "eq", "value": 1},
        {"column": "prediction_id", "operator": "eq", "value": 1},
        {"column": "prediction_id", "operator": "eq", "value": 4.23},
        {"column": "prediction_id", "operator": "eq", "value": None},
        {"column": "prediction_id", "operator": "ne", "value": True},
        {"column": "prediction_id", "operator": "lt", "value": 1},
        {"column": "prediction_id", "operator": "le", "value": 1},
        {"column": "prediction_id", "operator": "gt", "value": 1},
        {"column": "prediction_id", "operator": "ge", "value": 1},
        {"column": "prediction_id", "operator": "like", "value": 1},
        {"column": "prediction_id", "operator": "ilike", "value": 1},
        {"column": "prediction_id", "operator": "in", "value": [1, 3, 5, 7, 9]},
        {"column": "prediction_id", "operator": "not_in", "value": [12, 34, 23, 67]},
        {"column": "prediction_id", "operator": "between", "value": [10, 20]},
    ],
)
def test_valid_filter_condition(data):
    """
    Test FilterCompoundCondition model

    GIVEN a valid payload
    WHEN calling FilterCompoundCondition.model_validate_json
    THEN return a validated FilterCompoundCondition
    """

    FilterCondition(**data)


@pytest.mark.static
@pytest.mark.parametrize(
    "data, expected_message",
    [
        (
            {"column": "prediction_id", "conditions": "eq", "value": 1},
            "^\\d+ validation error(?:s)? for \\w+\\b",
        ),
        (
            {"column": "prediction_id", "operator": "or", "value": 1},
            "^\\d+ validation error(?:s)? for \\w+\\b",
        ),
        (
            {"column": "prediction_id", "operator": "and", "value": 1},
            "^\\d+ validation error(?:s)? for \\w+\\b",
        ),
        (
            {"column": "prediction_id", "operator": "and", "value": 1},
            "^\\d+ validation error(?:s)? for \\w+\\b",
        ),
        (
            {"column": "prediction_id", "operator": "hi", "value": 1},
            "^\\d+ validation error(?:s)? for \\w+\\b",
        ),
        (
            {"column": "prediction_id", "operator": "eq", "value": ["1", "3", "6"]},
            "^\\d+ validation error(?:s)? for \\w+\\b",
        ),
        (
            {"column": "prediction_id", "operator": "eq", "value": [1, 5]},
            "^\\d+ validation error(?:s)? for \\w+\\b",
        ),
        (
            {"column": "prediction_id", "operator": "in", "value": 1},
            "^\\d+ validation error(?:s)? for \\w+\\b",
        ),
        (
            {"column": "prediction_id", "operator": "not_in", "value": 1},
            "^\\d+ validation error(?:s)? for \\w+\\b",
        ),
        (
            {"column": "prediction_id", "operator": "between", "value": 1},
            "^\\d+ validation error(?:s)? for \\w+\\b",
        ),
    ],
)
def test_invalid_filter_compo_condition(data, expected_message):
    """
    Test FilterCondition model

    GIVEN an invalid payload
    WHEN calling FilterCondition.model_validate_json
    THEN raise a ValueError
    """
    with pytest.raises(ValueError, match=rf"{expected_message}"):
        FilterCondition(**data)


@pytest.mark.static
@pytest.mark.parametrize(
    "data",
    [
        {
            "operator": "or",
            "conditions": [
                {"column": "id", "operator": "eq", "value": 1},
                {"column": "status", "operator": "eq", "value": "closed"},
            ],
        },
        {
            "operator": "and",
            "conditions": [
                {"column": "id", "operator": "eq", "value": 1},
                {"column": "status", "operator": "eq", "value": "closed"},
            ],
        },
        {
            "operator": "or",
            "conditions": [
                {"column": "id", "operator": "eq", "value": 1},
                {
                    "operator": "and",
                    "conditions": [
                        {
                            "column": "preidcted_at",
                            "operator": "gt",
                            "value": "2025-01-01",
                        },
                        {"column": "status", "operator": "eq", "value": "open"},
                    ],
                },
            ],
        },
        {
            "operator": "or",
            "conditions": [
                {"column": "id", "operator": "eq", "value": 1},
                {
                    "operator": "or",
                    "conditions": [
                        {
                            "column": "preidcted_at",
                            "operator": "gt",
                            "value": "2025-01-01",
                        },
                        {"column": "status", "operator": "eq", "value": "open"},
                    ],
                },
            ],
        },
        {
            "operator": "and",
            "conditions": [
                {
                    "operator": "and",
                    "conditions": [
                        {
                            "column": "preidcted_at",
                            "operator": "gt",
                            "value": "2025-01-01",
                        },
                        {"column": "status", "operator": "eq", "value": "open"},
                    ],
                },
                {
                    "operator": "or",
                    "conditions": [
                        {
                            "column": "status",
                            "operator": "eq",
                            "value": "closed",
                        },
                        {"column": "status", "operator": "eq", "value": "open"},
                    ],
                },
            ],
        },
        {
            "operator": "and",
            "conditions": [
                {
                    "operator": "and",
                    "conditions": [
                        {
                            "column": "preidcted_at",
                            "operator": "gt",
                            "value": "2025-01-01",
                        },
                        {"column": "status", "operator": "eq", "value": "open"},
                    ],
                },
                {
                    "operator": "or",
                    "conditions": [
                        {
                            "column": "status",
                            "operator": "eq",
                            "value": "closed",
                        },
                        {"column": "status", "operator": "eq", "value": "open"},
                    ],
                },
                {"column": "id", "operator": "eq", "value": 1},
                {"column": "status", "operator": "eq", "value": "closed"},
            ],
        },
    ],
)
def test_valid_filter_compound_condition(data):
    """
    Test FilterCompoundCondition model

    GIVEN a valid payload
    WHEN calling FilterCompoundCondition.model_validate_json
    THEN return a validated FilterCompoundCondition
    """
    FilterCompoundCondition(**data)


@pytest.mark.static
@pytest.mark.parametrize(
    "data",
    [
        {
            "operator": "eq",
            "conditions": [
                {"column": "id", "operator": "eq", "value": 1},
                {"column": "status", "operator": "eq", "value": "closed"},
            ],
        },
        {
            "operator": "and",
            "condition": [
                {"column": "id", "operator": "eq", "value": 1},
                {"column": "status", "operator": "eq", "value": "closed"},
            ],
        },
        {
            "operator": "and",
            "conditions": [
                {"column": "id", "operator": "eq", "value": 1},
            ],
        },
        {
            "operator": "and",
            "conditions": [],
        },
        {
            "operator": "or",
            "conditions": {
                "operator": "and",
                "conditions": [
                    {
                        "column": "preidcted_at",
                        "operator": "gt",
                        "value": "2025-01-01",
                    },
                    {"column": "status", "operator": "eq", "value": "open"},
                ],
            },
        },
        {
            "operator": "or",
            "conditions": [
                {"column": "id", "operator": "eq", "value": 1},
                {
                    "operator": "or",
                    "conditions": [
                        {
                            "column": "preidcted_at",
                            "operator": "gt",
                            "value": "2025-01-01",
                        },
                        {"column": "status", "operator": "ops", "value": "open"},
                    ],
                },
            ],
        },
    ],
)
def test_invalid_filter_compound_condition(data):
    """
    Test FilterCompoundCondition model

    GIVEN an invalid payload
    WHEN calling FilterCompoundCondition.model_validate_json
    THEN raise a ValueError
    """
    with pytest.raises(
        ValueError,
        match=r"^\d+ validation error(?:s)? for \w+\b",
    ):
        FilterCompoundCondition(**data)


@pytest.mark.static
@pytest.mark.parametrize(
    "data",
    [
        {"where": {"column": "prediction_id", "operator": "eq", "value": 1}},
        {"where": {"column": "prediction_id", "operator": "ne", "value": "1"}},
        {
            "where": {
                "operator": "or",
                "conditions": [
                    {"column": "id", "operator": "eq", "value": 1},
                    {"column": "status", "operator": "eq", "value": "closed"},
                ],
            }
        },
        {
            "where": {
                "operator": "and",
                "conditions": [
                    {"column": "id", "operator": "eq", "value": 1},
                    {"column": "status", "operator": "eq", "value": "closed"},
                ],
            }
        },
        {
            "where": {
                "operator": "or",
                "conditions": [
                    {"column": "id", "operator": "eq", "value": 1},
                    {
                        "operator": "and",
                        "conditions": [
                            {
                                "column": "preidcted_at",
                                "operator": "gt",
                                "value": "2025-01-01",
                            },
                            {"column": "status", "operator": "eq", "value": "open"},
                        ],
                    },
                ],
            }
        },
    ],
)
def test_valid_filter_payload(data):
    """
    Test FilterPayload model

    GIVEN a valid payload
    WHEN calling FilterPayload.model_validate_json
    THEN return a validated FilterPayload
    """
    FilterPayload(**data)


@pytest.mark.static
@pytest.mark.parametrize(
    "data",
    [
        {
            "where": {"column": "prediction_id", "conditions": "eq", "value": 1},
        },
        {"where": {"column": "prediction_id", "operator": "or", "value": "1"}},
        {
            "where": {
                "operator": "and",
                "conditions": [],
            }
        },
        {
            "where": {
                "operator": "or",
                "conditions": {
                    "operator": "and",
                    "conditions": [
                        {
                            "column": "predicted_at",
                            "operator": "gt",
                            "value": "2025-01-01",
                        },
                        {"column": "status", "operator": "eq", "value": "open"},
                    ],
                },
            },
        },
        {
            "where": {
                "operator": "or",
                "conditions": [
                    {"column": "id", "operator": "eq", "value": 1},
                    {
                        "operator": "or",
                        "conditions": [
                            {
                                "column": "predicted_at",
                                "operator": "gt",
                                "value": "2025-01-01",
                            },
                            {"column": "status", "operator": "ops", "value": "open"},
                        ],
                    },
                ],
            },
        },
    ],
)
def test_invalid_filter_payload(data):
    """
    Test FilterPayload model

    GIVEN an invalid payload
    WHEN calling FilterPayload.model_validate_json
    THEN raise a ValueError
    """
    with pytest.raises(
        ValueError,
        match=r"^\d+ validation error(?:s)? for \w+\b",
    ):
        FilterPayload(**data)
