import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchemaModel


class RolePermissionSchema(BaseSchemaModel):
    """
    Base role permission schema
    """

    role_id: str = Field(description="ID of the role")
    permission_id: uuid.UUID = Field(description="ID of the permission")
    created_at: datetime = Field(description="Time of role permission creation")
    modified_at: datetime = Field(description="Time of role permission modification")
    created_by: uuid.UUID | None = Field(
        description="User ID that created the role permission"
    )
    modified_by: uuid.UUID | None = Field(
        description="User ID that modified the role permission"
    )


class RolePermissionSchemaPOSTRequest(BaseSchemaModel):
    """
    Request schema for creating a role permission on a POST request
    """

    permission_id: uuid.UUID = Field(description="ID of the permission")
