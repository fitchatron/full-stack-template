import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import AuthorizationAction
from app.schemas.base import BaseSchemaModel


class PermissionSchema(BaseSchemaModel):
    """
    Base permissions schema
    """

    permission_id: int = Field(description="Private ID of the permission")
    public_id: uuid.UUID = Field(description="Public ID of the user")
    action: AuthorizationAction = Field(description="Action of the permission")
    resource: str = Field(description="Resource of the permission")
    description: str = Field(description="Description of the permission")
    created_at: datetime = Field(description="Time of permission details creation")
    modified_at: datetime = Field(description="Time of permission details modification")
    created_by: uuid.UUID | None = Field(
        description="User ID that creates the permission details"
    )
    modified_by: uuid.UUID | None = Field(
        description="User ID that modified the permission details"
    )
