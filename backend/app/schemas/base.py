from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseSchemaModel(BaseModel):
    """
    Base pydantic schema to setup schema config
    """

    model_config: ConfigDict = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )


def reject_null(value: Any) -> Any:
    # Fields may be omitted, but these columns are non-nullable so an explicit null is rejected
    if value is None:
        raise ValueError("field cannot be null")

    return value
