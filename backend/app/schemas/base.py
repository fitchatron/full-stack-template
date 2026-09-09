from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel


class BaseSchemaModel(BaseModel):
    """
    Base pydantic schema to setup schema config
    """

    model_config: ConfigDict = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True
    )
