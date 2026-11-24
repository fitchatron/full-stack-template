import pytest

from app.utils.case_converter import (
    _split_words,
    to_camel_case,
    to_pascal_case,
    to_snake_case,
)


@pytest.mark.parametrize(
    "value, expected_list",
    [
        pytest.param(
            "foo",
            ["foo"],
            id="single-word",
        ),
        pytest.param(
            "foo-bar",
            ["foo", "bar"],
            id="multi-word-dashed",
        ),
        pytest.param(
            "fooBar",
            ["foo", "bar"],
            id="multi-word-capitalized",
        ),
        pytest.param(
            "foo bar time",
            ["foo", "bar", "time"],
            id="multi-word-space",
        ),
        pytest.param(
            "fooBar-hello",
            ["foo", "bar", "hello"],
            id="multi-word-combo",
        ),
        pytest.param(
            "",
            [],
            id="empty-string",
        ),
    ],
)
def test_split_words(value: str, expected_list: list[str]):
    """
    Test _split_words

    GIVEN a a string of word(s)
    WHEN calling _split_words
    THEN return a list of words trimmed
    """
    assert _split_words(value) == expected_list


@pytest.mark.parametrize(
    "value, expected_output",
    [
        pytest.param(
            "foo",
            "foo",
            id="single-word",
        ),
        pytest.param(
            "foo-bar",
            "foo_bar",
            id="multi-word-dashed",
        ),
        pytest.param(
            "FooBar",
            "foo_bar",
            id="multi-word-pascal",
        ),
        pytest.param(
            "fooBar",
            "foo_bar",
            id="multi-word-camel",
        ),
        pytest.param(
            "fooBar-hello",
            "foo_bar_hello",
            id="multi-word-combo",
        ),
        pytest.param(
            "",
            "",
            id="empty-string",
        ),
    ],
)
def test_to_snake_case(value: str, expected_output: str):
    """
    Test to_snake_case

    GIVEN a string of word(s)
    WHEN calling to_snake_case
    THEN return the word(s) in camel_case
    """
    assert to_snake_case(value) == expected_output


@pytest.mark.parametrize(
    "value, expected_output",
    [
        pytest.param(
            "reset",
            "Reset",
            id="single-word",
        ),
        pytest.param(
            "Reset Password",
            "ResetPassword",
            id="multi-word-spaced",
        ),
        pytest.param(
            "ResetPassword",
            "ResetPassword",
            id="multi-word-pascal",
        ),
        pytest.param(
            "resetPassword",
            "ResetPassword",
            id="multi-word-camel",
        ),
        pytest.param(
            "reset_password",
            "ResetPassword",
            id="multi-word-snaked",
        ),
        pytest.param(
            "reset-password",
            "ResetPassword",
            id="multi-word-kebabed",
        ),
        pytest.param(
            "",
            "",
            id="empty-string",
        ),
    ],
)
def test_to_pascal_case(value: str, expected_output: str):
    """
    Test to_pascal_case

    GIVEN a a string of word(s)
    WHEN calling to_pascal_case
    THEN return the word(s) in PascalCase
    """
    assert to_pascal_case(value) == expected_output


@pytest.mark.parametrize(
    "value, expected_output",
    [
        pytest.param(
            "reset",
            "reset",
            id="single-word",
        ),
        pytest.param(
            "Reset Password",
            "resetPassword",
            id="multi-word-spaced",
        ),
        pytest.param(
            "ResetPassword",
            "resetPassword",
            id="multi-word-pascal",
        ),
        pytest.param(
            "resetPassword",
            "resetPassword",
            id="multi-word-camel",
        ),
        pytest.param(
            "reset_password",
            "resetPassword",
            id="multi-word-snaked",
        ),
        pytest.param(
            "reset-password",
            "resetPassword",
            id="multi-word-kebabed",
        ),
        pytest.param(
            "",
            "",
            id="empty-string",
        ),
    ],
)
def test_to_camel_case(value: str, expected_output: str):
    """
    Test to_camel_case

    GIVEN a a string of word(s)
    WHEN calling to_camel_case
    THEN return the word(s) in camelCase
    """
    assert to_camel_case(value) == expected_output
