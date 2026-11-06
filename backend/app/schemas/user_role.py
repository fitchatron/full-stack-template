import uuid
from datetime import datetime
from typing import Any, Self

from pydantic import (
    AwareDatetime,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.base import BaseSchemaModel
from app.schemas.pagination import OptionalPage


class UserRoleSchema(BaseSchemaModel):
    """
    Base user role schema
    """

    user_role_id: uuid.UUID = Field(description="ID of the user role")
    user_id: uuid.UUID = Field(description="ID of the user")
    role_id: str = Field(description="ID of the role")
    start_at: datetime = Field(description="Time the role becomes active for the user")
    end_at: datetime = Field(
        description="Time the role stops being active for the user"
    )
    created_at: datetime = Field(description="Time of user role creation")
    modified_at: datetime = Field(description="Time of user role modification")
    created_by: uuid.UUID | None = Field(
        description="User ID that created the user role"
    )
    modified_by: uuid.UUID | None = Field(
        description="User ID that modified the user role"
    )


class UserRoleSchemaPOSTRequest(BaseSchemaModel):
    """
    Request schema for creating a user role on a POST request
    """

    role_id: str = Field(description="ID of the role")
    start_at: AwareDatetime | None = Field(
        None,
        description="Time the role becomes active for the user. Defaults to now",
    )
    end_at: AwareDatetime | None = Field(
        None,
        description="Time the role stops being active for the user. Defaults to a year from now",
    )

    @field_validator("start_at", "end_at")
    @classmethod
    def reject_null(cls, value: Any) -> Any:
        # Fields may be omitted, but these columns are non-nullable so an explicit null is rejected
        if value is None:
            raise ValueError("field cannot be null")

        return value

    @model_validator(mode="after")
    def verify_end_after_start(self) -> Self:
        if self.start_at and self.end_at and self.start_at > self.end_at:
            raise ValueError("start_at cannot be later than end_at")

        return self


class UserRoleSchemaPATCHRequest(BaseSchemaModel):
    """
    Request schema for updating a user role on a PATCH request
    """

    # user_id and role_id can't change, so sending them is rejected rather than ignored
    model_config = ConfigDict(extra="forbid")

    start_at: AwareDatetime | None = Field(
        None,
        description="Time the role becomes active for the user. Only scheduled user roles can change this",
    )
    end_at: AwareDatetime | None = Field(
        None, description="Time the role stops being active for the user"
    )

    @field_validator("start_at", "end_at")
    @classmethod
    def reject_null(cls, value: Any) -> Any:
        # Fields may be omitted, but these columns are non-nullable so an explicit null is rejected
        if value is None:
            raise ValueError("field cannot be null")

        return value

    @model_validator(mode="after")
    def verify_end_after_start(self) -> Self:
        if self.start_at and self.end_at and self.start_at > self.end_at:
            raise ValueError("start_at cannot be later than end_at")

        return self


class UserRoleSchemaPaginated(OptionalPage[UserRoleSchema]):
    """
    Paginated user role schema. This is required for documentation purposes by FastAPI.
    Without this, the schema will be called "Page_<schema name>_" instead of "<schema name>Paginated"
    """

    pass
