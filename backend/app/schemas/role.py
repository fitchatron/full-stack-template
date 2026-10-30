import uuid
from datetime import datetime
from typing import Any, Self

from pydantic import EmailStr, Field, SecretStr, field_validator, model_validator

from app.schemas.base import BaseSchemaModel
from app.schemas.pagination import OptionalPage


class RoleSchema(BaseSchemaModel):
    """
    Base role schema
    """

    role_id: str = Field(description="ID of the role")
    name: str = Field(description="Client friendly name of the role")
    description: str = Field(description="Role description")
    created_at: datetime = Field(description="Time of user details creation")
    modified_at: datetime = Field(description="Time of user details modification")
    created_by: uuid.UUID | None = Field(
        description="User ID that creates the user details"
    )
    modified_by: uuid.UUID | None = Field(
        description="User ID that modified the user details"
    )

class RoleSchemaPOSTRequest(BaseSchemaModel):
    """
    Request schema for creating a role on a POST request
    """

    role_id: str = Field(description="ID of the role")
    name: str = Field(description="Client friendly name of the role")
    description: str = Field(description="Role description")


class RoleSchemaPUTRequest(BaseSchemaModel):
    """
    Request schema for updating a role on a PUT request
    """

    name: str = Field(description="Client friendly name of the role")
    description: str = Field(description="Role description")


class RoleSchemaPATCHRequest(BaseSchemaModel):
    """
    Request schema for updating a role on a PATCH request
    """

    name: str | None = Field(None, description="Client friendly name of the role")
    description: str | None = Field(None, description="Role description")

class RoleSchemaPaginated(OptionalPage[RoleSchema]):
    """
    Paginated role schema. This is required for documentation purposes by FastAPI.
    Without this, the schema will be called "Page_<schema name>_" instead of "<schema name>Paginated"
    """
    pass