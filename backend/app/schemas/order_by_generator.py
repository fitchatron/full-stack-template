from enum import Enum
from typing import Annotated
from pydantic import Field
from app.schemas.base import BaseSchemaModel


class OrderOperator(str, Enum):
    """
    Represents an operator that can be applied to the orientation clause e.g. asc, desc
    """

    asc_ = "asc"
    desc_ = "desc"


class OrderByCondition(BaseSchemaModel):
    """
    Represents a sort by condition
    """

    column: Annotated[
        str,
        Field(
            description="The column to be sorted in the query",
            examples=[
                "prediction_id",
                "user_id",
                "status",
            ],
        ),
    ]

    orientation: Annotated[
        OrderOperator,
        Field(
            description="orientation clause to sort by",
            examples=[
                "asc",
                "desc",
            ],
        ),
    ]
