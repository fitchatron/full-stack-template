from uuid import UUID

from sqlalchemy.orm import Session

from app.models.model import Permission
from app.repositories.generic import CRUDRepository
from app.schemas.order_by_generator import OrderByCondition
from app.schemas.permission import (
    PermissionSchema,
    PermissionSchemaPaginated,
    PermissionSchemaPATCHRequest,
    PermissionSchemaPOSTRequest,
    PermissionSchemaPUTRequest,
)
from app.schemas.user import (
    UserResponseSchema,
)
from app.utils.exception import NotFoundError


class PermissionService:
    def __init__(self, session: Session) -> None:
        """
        PermissionService constructor.
        """
        self.repository = CRUDRepository(session, Permission)

    def _update_by_id(self, permission_id: UUID, values: dict) -> PermissionSchema:
        """
        Internal method to update a permission by ID with the given values.
        """
        permission = self.repository.update_single_item(
            filters=(Permission.permission_id == permission_id), values=values
        )

        if not permission:
            raise NotFoundError("Permission not found")
        return PermissionSchema.model_validate(permission)

    def read_all(self, sort_by: list[OrderByCondition]) -> PermissionSchemaPaginated:
        """
        Function to get all permissions.
        """
        page = self.repository.read_paginated_items(sort_by=sort_by)
        return PermissionSchemaPaginated.model_validate(page, from_attributes=True)

    def read_by_id(self, permission_id: UUID) -> PermissionSchema:
        """
        Function to get permission by ID.
        """
        permission = self.repository.read_by_pk(permission_id)

        if not permission:
            raise NotFoundError("Permission not found")

        return PermissionSchema.model_validate(permission)

    def create_permission(
        self,
        current_user: UserResponseSchema,
        request_body: PermissionSchemaPOSTRequest,
    ) -> PermissionSchema:
        """
        Create a new permission object
        """

        permission = self.repository.create_single_item(
            values=request_body.model_dump()
            | {"created_by": current_user.user_id, "modified_by": current_user.user_id},
        )
        return PermissionSchema.model_validate(permission)

    def update_by_id(
        self,
        current_user: UserResponseSchema,
        permission_id: UUID,
        request_body: PermissionSchemaPUTRequest,
    ) -> PermissionSchema:
        """
        Update an entire existing permission object by ID
        """
        return self._update_by_id(
            permission_id=permission_id,
            values=request_body.model_dump() | {"modified_by": current_user.user_id},
        )

    def patch_by_id(
        self,
        current_user: UserResponseSchema,
        permission_id: UUID,
        request_body: PermissionSchemaPATCHRequest,
    ) -> PermissionSchema:
        """
        Update part of an existing permission object by ID
        """
        return self._update_by_id(
            permission_id=permission_id,
            values=request_body.model_dump(exclude_unset=True)
            | {"modified_by": current_user.user_id},
        )

    def delete_by_id(self, permission_id: UUID) -> None:
        """
        Function to delete a permission by ID.
        """

        permission = self.repository.delete_single_item(
            filters=(Permission.permission_id == permission_id)
        )

        if not permission:
            raise NotFoundError("Permission not found")
