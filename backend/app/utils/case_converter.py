import re

# Splits at a lower/digit -> upper boundary ("helloWorld"), or on any run of
# non-alphanumeric characters.
_WORD_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|[^A-Za-z0-9]+")


def _split_words(value: str) -> list[str]:
    return [word.lower() for word in _WORD_BOUNDARY.split(value) if word]


def to_snake_case(value: str) -> str:
    """Converts a string to snake_case"""
    return "_".join(_split_words(value))


def to_pascal_case(value: str) -> str:
    """Converts a string to PascalCase"""
    return "".join(word.capitalize() for word in _split_words(value))


def to_camel_case(value: str) -> str:
    """Converts a string to camelCase"""
    pascal = to_pascal_case(value)
    return pascal[:1].lower() + pascal[1:]
