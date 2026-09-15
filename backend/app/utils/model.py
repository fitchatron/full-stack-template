from typing import Any, Type, TypeVar
from sqlalchemy import Function, func
from sqlalchemy.orm.attributes import InstrumentedAttribute

ModelType = TypeVar("ModelType")


class ModelAttributeUtils:

    FILTER_SYNTAX = {
        "join_delimiter": ".",  # denotes how joined tables are defined and split from column names e.g. roles.name
        "json_delimiter": "->",  # denotes how a column splits to a JSON key e.g. user.email == user["email"]
    }

    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

    def resolve_attr_path(self, column: str) -> InstrumentedAttribute:
        obj = self.model

        path = column.split(self.FILTER_SYNTAX["join_delimiter"])
        # prediction.prediction_value name
        for part in path[:-1]:  # loop through path minus last value
            attr: InstrumentedAttribute = getattr(obj, part)
            obj = attr.property.mapper.class_

        return getattr(obj, path[-1])

    def parse_column_to_attribute(
        self, column: str
    ) -> Function[Any] | InstrumentedAttribute:
        # should be a JSON column
        if self.FILTER_SYNTAX["json_delimiter"] in column:
            parts = column.split(self.FILTER_SYNTAX["json_delimiter"])

            # should be a join column
            attr: InstrumentedAttribute = (
                self.resolve_attr_path(column)
                if self.FILTER_SYNTAX["join_delimiter"] in parts[0]
                else getattr(self.model, parts[0])
            )
            return func.JSON_VALUE(attr, f"$.{parts[1]}")

        # referencing a mapped relationship
        if self.FILTER_SYNTAX["join_delimiter"] in column:
            return self.resolve_attr_path(column)

        # should be a standard column
        attr: InstrumentedAttribute = getattr(self.model, column)
        return attr
