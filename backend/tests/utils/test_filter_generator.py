from datetime import datetime

import pytest
from sqlalchemy import and_, or_

from app.models.model import User
from app.schemas.filter_generator import (
    ComparisonOperator,
    CompoundOperator,
    FilterCompoundCondition,
    FilterCondition,
    FilterPayload,
)
from app.utils.filter_generator import (
    FilterGenerator,
    _parse_filter_str_to_filter_compound_condition,
    _parse_filter_str_to_filter_condition,
    _type_col_val,
    parse_param_to_filter_payload,
    val_to_primitive,
)


@pytest.mark.parametrize(
    "val, expected_val ",
    [
        pytest.param("foo", "foo", id="string_word"),
        pytest.param("one", "one", id="string_number_word"),
        pytest.param("1", 1, id="integer"),
        pytest.param("-5", -5, id="negative_integer"),
        pytest.param("0", 0, id="zero"),
        pytest.param("007", 7, id="string_leading_zeros"),
        pytest.param("+57", 57, id="string_leading_plus"),
        pytest.param("-57", -57, id="string_leading_minus"),
        pytest.param("l57", "l57", id="string_leading_letter"),
        pytest.param("1234567890", 1234567890, id="large_integer"),
        pytest.param("-1234567890", -1234567890, id="negative_large_integer"),
        pytest.param("123.45", 123.45, id="float"),
        pytest.param("-123.45", -123.45, id="negative_float"),
        pytest.param("true", True, id="boolean_true"),
        pytest.param("True", True, id="boolean_true_capitalized"),
        pytest.param("false", False, id="boolean_false"),
        pytest.param("False", False, id="boolean_false_capitalized"),
        pytest.param("null", None, id="null"),
        pytest.param("NULL", None, id="null_capitalized"),
        pytest.param("None", "None", id="none_string"),
    ],
)
def test_val_to_primitive_valid_val(val, expected_val):
    """
    Test val_to_primitive
    GIVEN a value
    WHEN calling val_to_primitive with a string representation of a primitive
    THEN return the primitive representation of the value
    """
    assert val_to_primitive(val) == expected_val


@pytest.mark.parametrize(
    "val, exception, exception_msg",
    [
        pytest.param(
            '["foo", "bar", "foobar"]',
            ValueError,
            "Arrays are not primitives",
            id="array_non_primitive",
        ),
        pytest.param(
            "[]",
            ValueError,
            "Arrays are not primitives",
            id="empty_array_non_primitive",
        ),
        pytest.param(
            '{"foo": "bar", "foobar": 2}',
            ValueError,
            "Dictionaries are not primitives",
            id="dict_non_primitive",
        ),
    ],
)
def test_val_to_primitive_invalid_val(val, exception, exception_msg):
    """
    Test val_to_primitive
    GIVEN a value
    WHEN calling val_to_primitive with a string representation of a non-primitive
    THEN return the error handling
    """
    with pytest.raises(exception) as excinfo:
        val_to_primitive(val)

    assert exception_msg in str(excinfo.value)


@pytest.mark.parametrize(
    "val, operator, expected_val",
    [
        pytest.param("foo", "eq", "foo", id="eq"),
        pytest.param("foo", "ne", "foo", id="ne"),
        pytest.param("foo", "lt", "foo", id="lt"),
        pytest.param("foo", "le", "foo", id="le"),
        pytest.param("foo", "gt", "foo", id="gt"),
        pytest.param("foo", "ge", "foo", id="ge"),
        pytest.param("foo", "like", "foo", id="like"),
        pytest.param("foo", "ilike", "foo", id="ilike"),
        pytest.param(
            '["foo", "bar", "foobar"]', "in", ["foo", "bar", "foobar"], id="in_array"
        ),
        pytest.param(
            '["foo", "bar", "foobar"]',
            "not_in",
            ["foo", "bar", "foobar"],
            id="not_in_array",
        ),
        pytest.param(
            '["foo", "bar", "foobar"]',
            "between",
            ["foo", "bar", "foobar"],
            id="between_array",
        ),
    ],
)
def test_type_col_val_valid_val(val, operator, expected_val):
    """
    Test type_col_val
    GIVEN a value and a column type
    WHEN calling type_col_val with the value and column type
    THEN return the value casted to the column type
    """
    assert _type_col_val(val, operator) == expected_val


@pytest.mark.parametrize(
    "val, operator, exception, exception_msg",
    [
        pytest.param(
            "foo",
            "in",
            ValueError,
            "Expected a list for operator 'between', 'in', or 'not_in'",
            id="in_array_non_primitive",
        ),
        pytest.param(
            "foo",
            "not_in",
            ValueError,
            "Expected a list for operator 'between', 'in', or 'not_in'",
            id="not_in_array_non_primitive",
        ),
        pytest.param(
            "foo",
            "between",
            ValueError,
            "Expected a list for operator 'between', 'in', or 'not_in'",
            id="between_array_non_primitive",
        ),
        pytest.param(
            '{"foo": "bar", "foobar": 2}',
            "between",
            ValueError,
            "Expected a list for operator 'between', 'in', or 'not_in'",
            id="between_dict_non_primitive",
        ),
        pytest.param(
            '("foo", "bar", "foobar")',
            "between",
            ValueError,
            "Expected a list for operator 'between', 'in', or 'not_in'",
            id="between_tuple_non_primitive",
        ),
    ],
)
def test_type_col_val_invalid_val(val, operator, exception, exception_msg):
    """
    Test type_col_val
    GIVEN a value and a column type
    WHEN calling type_col_val with the value and column type
    THEN raise an error indicating the value cannot be casted to the column type
    """
    with pytest.raises(exception) as excinfo:
        _type_col_val(val, operator)

    assert exception_msg in str(excinfo.value)


@pytest.mark.parametrize(
    "filter_str, expected_filter_condition",
    [
        pytest.param(
            "user_id~eq~5",
            FilterCondition(column="user_id", operator=ComparisonOperator.eq_, value=5),
            id="eq",
        ),
        pytest.param(
            "user_id~ne~5",
            FilterCondition(column="user_id", operator=ComparisonOperator.ne_, value=5),
            id="ne",
        ),
        pytest.param(
            "user_id~gt~45",
            FilterCondition(
                column="user_id", operator=ComparisonOperator.gt_, value=45
            ),
            id="gt",
        ),
        pytest.param(
            "user_id~in~[5,7,10,56]",
            FilterCondition(
                column="user_id",
                operator=ComparisonOperator.in_,
                value=[5, 7, 10, 56],
            ),
            id="in",
        ),
        pytest.param(
            "json_field->value~eq~true",
            FilterCondition(
                column="json_field->value",
                operator=ComparisonOperator.eq_,
                value=True,
            ),
            id="json_field_eq_true",
        ),
    ],
)
def test_parse_filter_str_to_filter_condition(filter_str, expected_filter_condition):
    """
    Test _parse_filter_str_to_filter_condition
    GIVEN a filter string
    WHEN calling parse_filter_str_to_filter_condition with the filter string
    THEN return the corresponding filter condition
    """

    result = _parse_filter_str_to_filter_condition(filter_str)
    assert result == expected_filter_condition


@pytest.mark.parametrize(
    "filter_str, expected_filter_condition",
    [
        pytest.param(
            'and(user_id~eq~"00000000-0000-0000-0000-000000000000";user_id~ne~"00000000-1111-0000-0000-000000000000")',
            FilterCompoundCondition(
                operator=CompoundOperator.and_,
                conditions=[
                    FilterCondition(
                        column="user_id",
                        operator=ComparisonOperator.eq_,
                        value="00000000-0000-0000-0000-000000000000",
                    ),
                    FilterCondition(
                        column="user_id",
                        operator=ComparisonOperator.ne_,
                        value="00000000-1111-0000-0000-000000000000",
                    ),
                ],
            ),
            id="and_simple",
        ),
        pytest.param(
            'and(user_id~eq~"00000000-0000-0000-0000-000000000000";username~eq~"foo")',
            FilterCompoundCondition(
                conditions=[
                    FilterCondition(
                        column="user_id",
                        operator=ComparisonOperator.eq_,
                        value="00000000-0000-0000-0000-000000000000",
                    ),
                    FilterCondition(
                        column="username",
                        operator=ComparisonOperator.eq_,
                        value="foo",
                    ),
                ],
                operator=CompoundOperator.and_,
            ),
            id="and_nested",
        ),
        pytest.param(
            'or(user_id~eq~"00000000-0000-0000-0000-000000000000";username~eq~"foo";username~ne~"foobar")',
            FilterCompoundCondition(
                conditions=[
                    FilterCondition(
                        column="user_id",
                        operator=ComparisonOperator.eq_,
                        value="00000000-0000-0000-0000-000000000000",
                    ),
                    FilterCondition(
                        column="username",
                        operator=ComparisonOperator.eq_,
                        value="foo",
                    ),
                    FilterCondition(
                        column="username",
                        operator=ComparisonOperator.ne_,
                        value="foobar",
                    ),
                ],
                operator=CompoundOperator.or_,
            ),
            id="or_simple",
        ),
        pytest.param(
            'or(and(hello~eq~5;username~eq~"foobar";json_field->arr~in~["foo", "bar", "fisbuzz"]);or(user_id~ne~null;name~eq~"bar"))',
            FilterCompoundCondition(
                conditions=[
                    FilterCompoundCondition(
                        conditions=[
                            FilterCondition(
                                column="hello",
                                operator=ComparisonOperator.eq_,
                                value=5,
                            ),
                            FilterCondition(
                                column="username",
                                operator=ComparisonOperator.eq_,
                                value="foobar",
                            ),
                            FilterCondition(
                                column="json_field->arr",
                                operator=ComparisonOperator.in_,
                                value=["foo", "bar", "fisbuzz"],
                            ),
                        ],
                        operator=CompoundOperator.and_,
                    ),
                    FilterCompoundCondition(
                        conditions=[
                            FilterCondition(
                                column="user_id",
                                operator=ComparisonOperator.ne_,
                                value=None,
                            ),
                            FilterCondition(
                                column="name",
                                operator=ComparisonOperator.eq_,
                                value="bar",
                            ),
                        ],
                        operator=CompoundOperator.or_,
                    ),
                ],
                operator=CompoundOperator.or_,
            ),
            id="or_nested",
        ),
    ],
)
def test_parse_filter_str_to_filter_compound_condition(
    filter_str, expected_filter_condition
):
    """
    Test parse_filter_str_to_filter_compound_condition
    GIVEN a filter string representing a compound condition
    WHEN calling parse_filter_str_to_filter_compound_condition with the filter string
    THEN return the corresponding compound filter condition
    """
    result = _parse_filter_str_to_filter_compound_condition(filter_str)
    assert result == expected_filter_condition


@pytest.mark.parametrize(
    "filter_str, expected_filter_payload",
    [
        (
            "user_id~eq~5",
            FilterPayload(
                where=FilterCondition(
                    column="user_id", operator=ComparisonOperator.eq_, value=5
                )
            ),
        ),
        (
            "json_field->value~eq~true",
            FilterPayload(
                where=FilterCondition(
                    column="json_field->value",
                    operator=ComparisonOperator.eq_,
                    value=True,
                )
            ),
        ),
        (
            'and(user_id~eq~5;username~eq~"foo")',
            FilterPayload(
                where=FilterCompoundCondition(
                    conditions=[
                        FilterCondition(
                            column="user_id",
                            operator=ComparisonOperator.eq_,
                            value=5,
                        ),
                        FilterCondition(
                            column="username",
                            operator=ComparisonOperator.eq_,
                            value="foo",
                        ),
                    ],
                    operator=CompoundOperator.and_,
                )
            ),
        ),
        (
            'and(created_at~eq~"foobar";or(and(hello~eq~5;username~eq~"foobar";json_field->arr~in~["foo", "bar", "fisbuzz"]);or(user_id~ne~null;name~eq~"bar")))',
            FilterPayload(
                where=FilterCompoundCondition(
                    conditions=[
                        FilterCondition(
                            column="created_at",
                            operator=ComparisonOperator.eq_,
                            value="foobar",
                        ),
                        FilterCompoundCondition(
                            conditions=[
                                FilterCompoundCondition(
                                    conditions=[
                                        FilterCondition(
                                            column="hello",
                                            operator=ComparisonOperator.eq_,
                                            value=5,
                                        ),
                                        FilterCondition(
                                            column="username",
                                            operator=ComparisonOperator.eq_,
                                            value="foobar",
                                        ),
                                        FilterCondition(
                                            column="json_field->arr",
                                            operator=ComparisonOperator.in_,
                                            value=["foo", "bar", "fisbuzz"],
                                        ),
                                    ],
                                    operator=CompoundOperator.and_,
                                ),
                                FilterCompoundCondition(
                                    conditions=[
                                        FilterCondition(
                                            column="user_id",
                                            operator=ComparisonOperator.ne_,
                                            value=None,
                                        ),
                                        FilterCondition(
                                            column="name",
                                            operator=ComparisonOperator.eq_,
                                            value="bar",
                                        ),
                                    ],
                                    operator=CompoundOperator.or_,
                                ),
                            ],
                            operator=CompoundOperator.or_,
                        ),
                    ],
                    operator=CompoundOperator.and_,
                )
            ),
        ),
        (
            "",
            None,
        ),
        (
            None,
            None,
        ),
    ],
)
def test_parse_param_to_filter_payload(filter_str, expected_filter_payload):
    """
    Test parse_param_to_filter_payload
    GIVEN a filter query param
    WHEN calling parse_param_to_filter_payload with the param
    THEN return the corresponding filter payload
    """
    result = parse_param_to_filter_payload(filter_str)
    assert result == expected_filter_payload


@pytest.mark.parametrize(
    "model, filter, expected_filter",
    [
        (
            User,
            FilterCondition(
                column="user_id",
                operator=ComparisonOperator.eq_,
                value="00000000-0000-0000-0000-000000000000",
            ),
            (User.user_id == "00000000-0000-0000-0000-000000000000"),
        ),
        (
            User,
            FilterCompoundCondition(
                conditions=[
                    FilterCondition(
                        column="user_id",
                        operator=ComparisonOperator.eq_,
                        value="00000000-0000-0000-0000-000000000000",
                    ),
                    FilterCondition(
                        column="username",
                        operator=ComparisonOperator.eq_,
                        value="foo",
                    ),
                ],
                operator=CompoundOperator.and_,
            ),
            and_(
                User.user_id == "00000000-0000-0000-0000-000000000000",
                User.username == "foo",
            ),
        ),
        (
            User,
            FilterCompoundCondition(
                conditions=[
                    FilterCondition(
                        column="created_at",
                        operator=ComparisonOperator.gt_,
                        value=datetime(day=1, month=1, year=2020).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    ),
                    FilterCompoundCondition(
                        conditions=[
                            FilterCompoundCondition(
                                conditions=[
                                    FilterCondition(
                                        column="email",
                                        operator=ComparisonOperator.eq_,
                                        value="some@email.com",
                                    ),
                                    FilterCondition(
                                        column="username",
                                        operator=ComparisonOperator.eq_,
                                        value="foobar",
                                    ),
                                ],
                                operator=CompoundOperator.and_,
                            ),
                            FilterCompoundCondition(
                                conditions=[
                                    FilterCondition(
                                        column="user_id",
                                        operator=ComparisonOperator.ne_,
                                        value=None,
                                    ),
                                    FilterCondition(
                                        column="given_name",
                                        operator=ComparisonOperator.ilike_,
                                        value="%bar%",
                                    ),
                                ],
                                operator=CompoundOperator.or_,
                            ),
                        ],
                        operator=CompoundOperator.or_,
                    ),
                ],
                operator=CompoundOperator.and_,
            ),
            and_(
                User.created_at
                > datetime(day=1, month=1, year=2020).strftime("%Y-%m-%d %H:%M:%S"),
                or_(
                    and_(User.email == "some@email.com", User.username == "foobar"),
                    or_(User.user_id.is_not(None), User.given_name.ilike("%bar%")),
                ),
            ),
        ),
    ],
)
def test_filter_generator_generate_filter(model, filter, expected_filter):
    """
    Test FilterGenerator.generate_filter
    GIVEN a filter payload
    WHEN calling FilterGenerator.generate_filter with the payload
    THEN return the corresponding filter condition
    """
    filter_generator = FilterGenerator(model)
    result = filter_generator.generate_filter(filter)
    assert expected_filter.compare(result)


@pytest.mark.parametrize(
    "model, filter_payload, expected_filter",
    [
        (
            User,
            FilterPayload(
                where=FilterCondition(
                    column="user_id",
                    operator=ComparisonOperator.eq_,
                    value="00000000-0000-0000-0000-000000000000",
                )
            ),
            (User.user_id == "00000000-0000-0000-0000-000000000000"),
        ),
        (
            User,
            FilterPayload(
                where=FilterCompoundCondition(
                    conditions=[
                        FilterCondition(
                            column="user_id",
                            operator=ComparisonOperator.eq_,
                            value="00000000-0000-0000-0000-000000000000",
                        ),
                        FilterCondition(
                            column="username",
                            operator=ComparisonOperator.eq_,
                            value="foo",
                        ),
                    ],
                    operator=CompoundOperator.and_,
                )
            ),
            and_(
                User.user_id == "00000000-0000-0000-0000-000000000000",
                User.username == "foo",
            ),
        ),
        (
            User,
            FilterPayload(
                where=FilterCompoundCondition(
                    conditions=[
                        FilterCondition(
                            column="created_at",
                            operator=ComparisonOperator.gt_,
                            value=datetime(day=1, month=1, year=2020).strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        ),
                        FilterCompoundCondition(
                            conditions=[
                                FilterCompoundCondition(
                                    conditions=[
                                        FilterCondition(
                                            column="email",
                                            operator=ComparisonOperator.eq_,
                                            value="some@email.com",
                                        ),
                                        FilterCondition(
                                            column="username",
                                            operator=ComparisonOperator.eq_,
                                            value="foobar",
                                        ),
                                    ],
                                    operator=CompoundOperator.and_,
                                ),
                                FilterCompoundCondition(
                                    conditions=[
                                        FilterCondition(
                                            column="user_id",
                                            operator=ComparisonOperator.ne_,
                                            value=None,
                                        ),
                                        FilterCondition(
                                            column="given_name",
                                            operator=ComparisonOperator.ilike_,
                                            value="%bar%",
                                        ),
                                    ],
                                    operator=CompoundOperator.or_,
                                ),
                            ],
                            operator=CompoundOperator.or_,
                        ),
                    ],
                    operator=CompoundOperator.and_,
                )
            ),
            and_(
                User.created_at
                > datetime(day=1, month=1, year=2020).strftime("%Y-%m-%d %H:%M:%S"),
                or_(
                    and_(User.email == "some@email.com", User.username == "foobar"),
                    or_(User.user_id.is_not(None), User.given_name.ilike("%bar%")),
                ),
            ),
        ),
    ],
)
def test_filter_generator_build_filter(model, filter_payload, expected_filter):
    """
    Test FilterGenerator.build_filter
    GIVEN a filter payload
    WHEN calling FilterGenerator.build_filter with the payload
    THEN return the corresponding filter condition
    """
    filter_generator = FilterGenerator(model)
    result = filter_generator.build_filter(filter_payload)
    assert expected_filter.compare(result)
