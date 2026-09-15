from pydantic import Field, EmailStr, SecretStr, field_validator, model_validator
from typing import Optional, Self
from datetime import datetime
from app.schemas.base import BaseSchemaModel


class UserSchema(BaseSchemaModel):
    """
    Base users schema
    """

    user_id: int = Field(description="ID of the user")
    username: str = Field(description="Username of the user")
    email: EmailStr = Field(description="Email of the user")
    hashed_password: str = Field(description="Hashed password of the user")
    salt: str = Field(description="Salt used for hashing the password")
    given_name: Optional[str] = Field(description="Given name of the user")
    family_name: Optional[str] = Field(description="Family name of the user")
    email_verified: bool = Field(description="Email verification status of the user")
    is_active: bool = Field(description="Active status of the user")
    created_at: datetime = Field(description="Time of user details creation")
    modified_at: datetime = Field(description="Time of user details modification")
    created_by: Optional[int] = Field(
        description="User ID that creates the user details"
    )
    modified_by: Optional[int] = Field(
        description="User ID that modified the user details"
    )


class RegisterUserPOSTRequest(BaseSchemaModel):
    email: EmailStr = Field(description="Email of the user")
    username: str = Field(description="Username of the user")
    given_name: Optional[str] = Field(description="Given name of the user")
    family_name: Optional[str] = Field(description="Family name of the user")
    password: SecretStr = Field(description="Password of the user", min_length=8)
    password_confirm: SecretStr = Field(description="Confirm password of the user")

    @model_validator(mode="after")
    def verify_password_match(self) -> Self:
        # Extract the raw string values to compare them
        pw = self.password.get_secret_value()
        pw_confirm = self.password_confirm.get_secret_value()

        if pw != pw_confirm:
            raise ValueError("passwords do not match")

        return self


class RegisterUserSchema(BaseSchemaModel):
    email: EmailStr = Field(description="Email of the user")
    username: str = Field(description="Username of the user")
    given_name: Optional[str] = Field(description="Given name of the user")
    family_name: Optional[str] = Field(description="Family name of the user")
    hashed_password: SecretStr = Field(..., description="Hashed password of the user")
    salt: str = Field(description="Salt used for hashing the password")
