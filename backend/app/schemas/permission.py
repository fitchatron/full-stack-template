import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import AuthorizationAction
from app.schemas.base import BaseSchemaModel


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
    created_by: int | None = Field(
        description="User ID that creates the permission details"
    )
    modified_by: int | None = Field(
        description="User ID that modified the permission details"
    )
