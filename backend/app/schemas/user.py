from pydantic import Field, EmailStr
from typing import Optional
from datetime import datetime
from app.schemas.base import BaseSchemaModel


class UserSchema(BaseSchemaModel):
    """
    Base users schema
    """

    user_id: int = Field(description="ID of the user")
    email: EmailStr = Field(description="Email of the user")
    username: str = Field(description="Username of the user")
    given_name: Optional[str] = Field(description="Given name of the user")
    family_name: Optional[str] = Field(description="Family name of the user")
    created_at: datetime = Field(description="Time of user details creation")
    modified_at: datetime = Field(description="Time of user details modification")
    created_by: Optional[int] = Field(
        description="User ID that creates the user details"
    )
    modified_by: Optional[int] = Field(
        description="User ID that modified the user details"
    )
