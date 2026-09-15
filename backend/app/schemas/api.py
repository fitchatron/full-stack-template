from pydantic import BaseModel, Field


class HTTPExceptionSchema(BaseModel):
    """
    Base HTTP exception schema
    """

    detail: str = Field(description="HTTP exception detail message")
