from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core.app_permissions import AppPermissions
from app.models.model import Permission, User, UserRole, Role
from app.repositories.generic import CRUDRepository
from app.repositories.permission import PermissionRepository
from app.repositories.user import UserRepository
from app.schemas.order_by_generator import OrderByCondition
from app.schemas.permission import (
    PermissionSchema,
)
from app.schemas.user import (
    UserResponseSchema,
    UserResponseSchemaPaginated,
    UserSchemaPATCHRequest,
    UserSchemaPUTRequest,
)
from app.utils.exception import ForbiddenError, NotFoundError


class RoleService:
    def __init__(self, session: Session) -> None:
        """
        RoleService constructor.
        """
        self.repository = CRUDRepository(session, Role)

    def _update_by_id(self, role_id: str, current_user_user_id: UUID, values: dict) -> RoleSchema:
        """
        Internal method to update a role by ID with the given values.
        """
        role = self.repository.update_single_item(
            filters=(Role.role_id == role_id), values=values
        )

        if not role:
            raise NotFoundError("Role not found")
        return RoleSchema.model_validate(user)

    def read_all(self, sort_by: list[OrderByCondition]) -> RoleSchemaPaginated:
        """
        Function to get all roles.
        """
        page = self.repository.read_paginated_items(sort_by=sort_by)
        return RoleSchemaPaginated.model_validate(page, from_attributes=True)

    def read_by_id(self, role_id: str) -> RoleSchema:
        """
        Function to get role by ID.
        """
        role = self.repository.read_by_pk(role_id)

        if not role:
            raise NotFoundError("Role not found")

        return RoleSchema.model_validate(role)

    def create_role(
        self,
        current_user: UserResponseSchema,
        request_body: RoleSchemaPOSTRequest,
    ) -> RoleSchema:
        """
        Create a new role object
        """
        return self.repository.create_single_item(
            values=request_body.model_dump() | {"created_by": current_user.user_id, "modified_by": current_user.user_id},
            
        )

    def update_by_id(
        self,
        current_user: UserResponseSchema,
        role_id: str,
        request_body: RoleSchemaPUTRequest,
    ) -> RoleSchema:
        """
        Update an entire existing role object by ID
        """
        return self._update_by_id(
            role_id=role_id,
            current_user_user_id=current_user.user_id,
            values=request_body.model_dump() | {"modified_by": current_user.user_id},
        )

    def update_by_id(
        self,
        current_user: UserResponseSchema,
        role_id: str,
        request_body: RoleSchemaPUTRequest,
    ) -> RoleSchema:
        """
        Update an entire existing role object by ID
        """
        return self._update_by_id(
            role_id=role_id,
            current_user_user_id=current_user.user_id,
            values=request_body.model_dump() | {"modified_by": current_user.user_id},
        )

    def patch_by_id(
        self,
        current_user: UserResponseSchema,
        role_id: str,
        request_body: RoleSchemaPATCHRequest,
    ) -> RoleSchema:
        """
        Update part of an existing role object by ID
        """
        return self._update_by_id(
            role_id=role_id,
            current_user_user_id=current_user.user_id,
            values=request_body.model_dump(exclude_unset=True)
            | {"modified_by": current_user.user_id},
        )

    def delete_by_id(self, role_id: str) -> None:
        """
        Function to delete a role by ID.
        """

        role = self.repository.delete_single_item(filters=(Role.role_id == role_id))

        if not role:
            raise NotFoundError("Role not found")
