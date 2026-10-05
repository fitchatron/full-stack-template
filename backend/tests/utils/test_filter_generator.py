from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import Boolean, Float, Integer, Numeric, Text, and_, column, func, or_

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
    _val_to_primitive,
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
    Test _val_to_primitive
    GIVEN a value
    WHEN calling _val_to_primitive with a string representation of a primitive
    THEN return the primitive representation of the value
    """
    assert _val_to_primitive(val) == expected_val


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
    Test _val_to_primitive
    GIVEN a value
    WHEN calling _val_to_primitive with a string representation of a non-primitive
    THEN return the error handling
    """
    with pytest.raises(exception) as excinfo:
        _val_to_primitive(val)

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
    assert FilterGenerator(model=User)._type_col_val(val, operator) == expected_val


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
        FilterGenerator(model=User)._type_col_val(val, operator)

    assert exception_msg in str(excinfo.value)


@pytest.mark.parametrize(
    "model,filter_str, expected_filter_condition",
    [
        pytest.param(
            User,
            "user_id~eq~5",
            FilterCondition(
                column="user_id", operator=ComparisonOperator.eq_, value="5"
            ),
            id="eq",
        ),
        pytest.param(
            User,
            "user_id~ne~5",
            FilterCondition(
                column="user_id", operator=ComparisonOperator.ne_, value="5"
            ),
            id="ne",
        ),
        pytest.param(
            User,
            "user_id~gt~45",
            FilterCondition(
                column="user_id", operator=ComparisonOperator.gt_, value="45"
            ),
            id="gt",
        ),
        pytest.param(
            User,
            "user_id~in~[5,7,10,56]",
            FilterCondition(
                column="user_id",
                operator=ComparisonOperator.in_,
                value=["5", "7", "10", "56"],
            ),
            id="in",
        ),
        pytest.param(
            User,
            "json_field->value~eq~true",
            FilterCondition(
                column="json_field->value",
                operator=ComparisonOperator.eq_,
                value="true",
            ),
            id="json_field_eq_true",
        ),
    ],
)
def test_parse_filter_str_to_filter_condition(
    model, filter_str, expected_filter_condition
):
    """
    Test _parse_filter_str_to_filter_condition
    GIVEN a filter string
    WHEN calling parse_filter_str_to_filter_condition with the filter string
    THEN return the corresponding filter condition
    """

    result = FilterGenerator(model=model)._parse_filter_str_to_filter_condition(
        filter_str
    )
    assert result == expected_filter_condition


@pytest.mark.parametrize(
    "model, filter_str, expected_filter_condition",
    [
        pytest.param(
            User,
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
            User,
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
            User,
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
            User,
            'or(and(hello~eq~5;username~eq~"foobar";json_field->arr~in~["foo", "bar", "fisbuzz"]);or(user_id~ne~null;name~eq~"bar"))',
            FilterCompoundCondition(
                conditions=[
                    FilterCompoundCondition(
                        conditions=[
                            FilterCondition(
                                column="hello",
                                operator=ComparisonOperator.eq_,
                                value="5",
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
    model, filter_str, expected_filter_condition
):
    """
    Test parse_filter_str_to_filter_compound_condition
    GIVEN a filter string representing a compound condition
    WHEN calling parse_filter_str_to_filter_compound_condition with the filter string
    THEN return the corresponding compound filter condition
    """
    result = FilterGenerator(
        model=model
    )._parse_filter_str_to_filter_compound_condition(filter_str)
    assert result == expected_filter_condition


@pytest.mark.parametrize(
    "model, filter_str, expected_filter_payload",
    [
        pytest.param(
            User,
            "user_id~eq~5",
            FilterPayload(
                where=FilterCondition(
                    column="user_id", operator=ComparisonOperator.eq_, value="5"
                )
            ),
            id="simple_filter",
        ),
        pytest.param(
            User,
            "json_field->value~eq~true",
            FilterPayload(
                where=FilterCondition(
                    column="json_field->value",
                    operator=ComparisonOperator.eq_,
                    value="true",
                )
            ),
            id="json_field_filter",
        ),
        pytest.param(
            User,
            'and(user_id~eq~5;username~eq~"foo")',
            FilterPayload(
                where=FilterCompoundCondition(
                    conditions=[
                        FilterCondition(
                            column="user_id",
                            operator=ComparisonOperator.eq_,
                            value="5",
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
            id="simple_and_filter",
        ),
        pytest.param(
            User,
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
                                            value="5",
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
            id="complex_filter",
        ),
        pytest.param(
            User,
            "",
            None,
            id="empty_filter",
        ),
        pytest.param(
            User,
            None,
            None,
            id="none_filter",
        ),
    ],
)
def test_parse_param_to_filter_payload(model, filter_str, expected_filter_payload):
    """
    Test parse_param_to_filter_payload
    GIVEN a filter query param
    WHEN calling parse_param_to_filter_payload with the param
    THEN return the corresponding filter payload
    """
    result = FilterGenerator(model=model).parse_param_to_filter_payload(filter_str)
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


@pytest.mark.parametrize(
    "val, operator, expected_val",
    [
        pytest.param("00501", "eq", "00501", id="leading_zeros_kept"),
        pytest.param("1e3", "eq", "1e3", id="exponent_kept"),
        pytest.param("+5", "eq", "+5", id="leading_plus_kept"),
        pytest.param("true", "eq", "true", id="boolean_text_kept"),
        pytest.param('"foo"', "eq", "foo", id="surrounding_quotes_stripped"),
        pytest.param("null", "eq", None, id="null"),
        pytest.param("", "eq", None, id="empty"),
        pytest.param("[0.1, 1]", "in", ["0.1", "1"], id="list_numbers_kept_as_text"),
    ],
)
def test_type_col_val_keeps_raw_text(val, operator, expected_val):
    """
    Test type_col_val
    GIVEN a query-string value
    WHEN calling type_col_val before the column type is known
    THEN keep the value's original text so the column type can decide how to convert it
    """
    assert FilterGenerator(model=User)._type_col_val(val, operator) == expected_val


# Columns of each type, so tests can filter numeric columns that User doesn't have
TYPED_COLUMNS = {
    "code": column("code", Text),
    "flag": column("flag", Boolean),
    "qty": column("qty", Integer),
    "amount": column("amount", Float),
    "price": column("price", Numeric),
    "score": func.JSON_VALUE(column("payload", Text), "$.score"),
}


def _bound_values(filter_str: str) -> list:
    """Parse a query-string filter and return the values bound into the SQL."""
    generator = FilterGenerator(model=User, column_mapping=TYPED_COLUMNS)
    payload = generator.parse_param_to_filter_payload(filter_str)
    assert payload is not None
    params = generator.build_filter(payload).compile().params
    # `in` binds one list parameter, so flatten it
    values = []
    for v in params.values():
        values.extend(v if isinstance(v, list) else [v])
    # JSON_VALUE's path argument is bound too, so leave it out
    return [v for v in values if v != "$.score"]


@pytest.mark.parametrize(
    "filter_str, expected_values",
    [
        pytest.param("code~eq~00501", ["00501"], id="str_leading_zeros"),
        pytest.param("code~eq~1e3", ["1e3"], id="str_exponent"),
        pytest.param("code~eq~true", ["true"], id="str_boolean_text"),
        pytest.param("code~eq~+5", ["+5"], id="str_leading_plus"),
        pytest.param('code~in~["00501", 7]', ["00501", "7"], id="str_in"),
        pytest.param("qty~eq~5", [5], id="int"),
        pytest.param("qty~eq~1.0", [1], id="int_whole_float"),
        pytest.param("qty~lt~1e3", [1000], id="int_exponent"),
        pytest.param("amount~eq~2.5", [2.5], id="float"),
        pytest.param("price~eq~0.1", [Decimal("0.1")], id="decimal_exact"),
        pytest.param(
            "price~in~[0.1, 2]", [Decimal("0.1"), Decimal("2")], id="decimal_in"
        ),
        pytest.param("score~eq~2.5", [2.5], id="json_guesses_type"),
        pytest.param("score~between~[1,10]", [1.0, 10.0], id="json_between_float"),
        pytest.param("qty~between~[1,10]", [1.0, 10.0], id="int_between_float"),
        pytest.param(
            "price~between~[0.1,0.2]",
            [Decimal("0.1"), Decimal("0.2")],
            id="decimal_between_stays_decimal",
        ),
        pytest.param("qty~like~12%", ["12%"], id="like_skips_coercion"),
        pytest.param("price~ilike~%0.1%", ["%0.1%"], id="ilike_skips_coercion"),
    ],
)
def test_build_filter_coerces_to_column_type(filter_str, expected_values):
    """
    Test FilterGenerator.build_filter
    GIVEN a query-string filter on a typed column
    WHEN building the filter
    THEN bind the value converted exactly to the column's type
    """
    values = _bound_values(filter_str)
    assert values == expected_values
    assert [type(v) for v in values] == [type(v) for v in expected_values]


@pytest.mark.parametrize(
    "val, expected_val",
    [
        pytest.param("false", False, id="text_false"),
        pytest.param("True", True, id="text_true_capitalized"),
        pytest.param(False, False, id="bool"),
    ],
)
def test_coerce_to_column_type_bool(val, expected_val):
    """
    Test _coerce_to_column_type
    GIVEN a boolean value as text or a bool
    WHEN coercing it for a Boolean column
    THEN return the matching bool
    """
    generator = FilterGenerator(model=User)
    assert generator._coerce_to_column_type(TYPED_COLUMNS["flag"], val) is expected_val


@pytest.mark.parametrize(
    "filter_str, exception_msg",
    [
        pytest.param("qty~eq~1.5", "'1.5' is not a valid int", id="int_fraction"),
        pytest.param("qty~lt~1.5", "'1.5' is not a valid int", id="int_fraction_lt"),
        pytest.param("qty~eq~true", "'true' is not a valid int", id="int_boolean"),
        pytest.param("qty~eq~abc", "'abc' is not a valid int", id="int_text"),
        pytest.param("amount~eq~abc", "'abc' is not a valid float", id="float_text"),
        pytest.param("price~eq~abc", "'abc' is not a valid Decimal", id="decimal_text"),
        pytest.param("price~eq~NaN", "'NaN' is not a valid Decimal", id="decimal_nan"),
        pytest.param("flag~eq~5", "'5' is not a valid boolean", id="bool_number"),
    ],
)
def test_build_filter_rejects_values_that_dont_fit_column(filter_str, exception_msg):
    """
    Test FilterGenerator.build_filter
    GIVEN a query-string filter whose value can't be converted exactly to the column's type
    WHEN building the filter
    THEN raise a ValueError instead of truncating or guessing
    """
    with pytest.raises(ValueError) as excinfo:
        _bound_values(filter_str)

    assert exception_msg in str(excinfo.value)
