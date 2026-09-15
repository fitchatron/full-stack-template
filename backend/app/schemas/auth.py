from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    """
    JWT token payload schema
    """

    sub: str | None = Field(default=None, description="Subject of the JWT token")


# JSON payload containing access token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
