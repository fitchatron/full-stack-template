from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    """
    JWT token payload schema
    """

    sub: str | None = Field(default=None, description="Subject of the JWT token")
