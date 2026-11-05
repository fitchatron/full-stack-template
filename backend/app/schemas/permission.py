import uuid
from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.models.enums import AuthorizationAction
from app.schemas.base import BaseSchemaModel
from app.schemas.pagination import OptionalPage


class PermissionSchema(BaseSchemaModel):
    """
    Base permissions schema
    """

    permission_id: uuid.UUID = Field(description="ID of the permission")
    description: str = Field(description="Description of the permission")
    action: AuthorizationAction = Field(description="Action of the permission")
    resource: str = Field(description="Resource of the permission")
    created_at: datetime = Field(description="Time of permission details creation")
    modified_at: datetime = Field(description="Time of permission details modification")
    created_by: uuid.UUID | None = Field(
        description="User ID that creates the permission details"
    )
    modified_by: uuid.UUID | None = Field(
        description="User ID that modified the permission details"
    )


class PermissionSchemaPOSTRequest(BaseSchemaModel):
    """
    Request schema for creating a permission on a POST request
    """

    action: AuthorizationAction = Field(description="Action of the permission")
    resource: str = Field(description="Resource of the permission")
    description: str = Field(description="Description of the permission")


class PermissionSchemaPUTRequest(BaseSchemaModel):
    """
    Request schema for updating a permission on a PUT request
    """

    action: AuthorizationAction = Field(description="Action of the permission")
    resource: str = Field(description="Resource of the permission")
    description: str = Field(description="Description of the permission")


class PermissionSchemaPATCHRequest(BaseSchemaModel):
    """
    Request schema for updating a permission on a PATCH request
    """

    action: AuthorizationAction | None = Field(
        None, description="Action of the permission"
    )
    resource: str | None = Field(None, description="Resource of the permission")
    description: str | None = Field(None, description="Description of the permission")

    @field_validator("action", "resource", "description")
    @classmethod
    def reject_null(cls, value: Any) -> Any:
        # Fields may be omitted, but these columns are non-nullable so an explicit null is rejected
        if value is None:
            raise ValueError("field cannot be null")

        return value


class PermissionSchemaPaginated(OptionalPage[PermissionSchema]):
    """
    Paginated permission schema. This is required for documentation purposes by FastAPI.
    Without this, the schema will be called "Page_<schema name>_" instead of "<schema name>Paginated"
    """

    pass
