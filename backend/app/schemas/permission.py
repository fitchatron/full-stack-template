from pydantic import Field, EmailStr
from typing import Optional
import uuid
from datetime import datetime
from app.schemas.base import BaseSchemaModel
from app.models.enums import AuthorizationAction


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
    created_by: Optional[int] = Field(
        description="User ID that creates the permission details"
    )
    modified_by: Optional[int] = Field(
        description="User ID that modified the permission details"
    )
