from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.core.app_permissions import AppPermissions
from app.models.model import Permission, User, UserRole
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


class UserService:
    def __init__(self, session: Session) -> None:
        """
        UserService constructor.
        """
        self.repository = UserRepository(session, User)
        self.user_role_repository = CRUDRepository(session, UserRole)
        self.permission_repository = PermissionRepository(session, Permission)

    def _update_by_id(self, user_id: UUID, current_user_user_id: UUID, values: dict):
        """
        Internal method to update a user by ID with the given values.
        """
        if user_id == current_user_user_id:
            raise ForbiddenError("Users cannot update their own account")

        user = self.repository.update_single_item(
            filters=(User.user_id == user_id), values=values
        )

        if not user:
            raise NotFoundError("User not found")
        return UserResponseSchema.model_validate(user)

    def read_all(self, sort_by: list[OrderByCondition]) -> UserResponseSchemaPaginated:
        """
        Function to get all users.
        """
        page = self.repository.read_paginated_items(sort_by=sort_by)
        return UserResponseSchemaPaginated.model_validate(page, from_attributes=True)

    def read_by_id(self, user_id: UUID) -> UserResponseSchema:
        """
        Function to get user by ID.
        """
        user = self.repository.read_by_pk(user_id)

        if not user:
            raise NotFoundError("User not found")

        return UserResponseSchema.model_validate(user)

    def update_by_id(
        self,
        current_user: UserResponseSchema,
        user_id: UUID,
        request_body: UserSchemaPUTRequest,
    ) -> UserResponseSchema:
        """
        Update an entire existing user object by ID
        """
        return self._update_by_id(
            user_id=user_id,
            current_user_user_id=current_user.user_id,
            values=request_body.model_dump() | {"modified_by": current_user.user_id},
        )

    def patch_by_id(
        self,
        current_user: UserResponseSchema,
        user_id: UUID,
        request_body: UserSchemaPATCHRequest,
    ) -> UserResponseSchema:
        """
        Update part of an existing user object by ID
        """
        return self._update_by_id(
            user_id=user_id,
            current_user_user_id=current_user.user_id,
            values=request_body.model_dump(exclude_unset=True)
            | {"modified_by": current_user.user_id},
        )

    def delete_by_id(self, current_user: UserResponseSchema, user_id: UUID) -> None:
        """
        Function to delete a user by ID.
        """
        if current_user.user_id == user_id:
            raise ForbiddenError("Users cannot delete their own account")

        user = self.repository.delete_single_item(filters=(User.user_id == user_id))

        if not user:
            raise NotFoundError("User not found")

    def read_active_for_user(self, user_id: UUID) -> list[PermissionSchema]:
        """
        Function to get user permissions at app level.
        """
        permissions = self.permission_repository.read_active_for_user(user_id)
        return TypeAdapter(list[PermissionSchema]).validate_python(permissions)

    def has_all_permissions(
        self, user_id: UUID, required_permissions: list[AppPermissions]
    ):
        """
        Function to check if the user has all specified permissions at app level.
        """
        if not required_permissions:
            return True

        permissions = (
            self.permission_repository.read_active_for_user_and_required_permissions(
                user_id=user_id, required_permissions=required_permissions
            )
        )
        return all(
            any(required.is_granted_by(p.action, p.resource) for p in permissions)
            for required in required_permissions
        )
