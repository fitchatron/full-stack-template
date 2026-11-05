from uuid import UUID

from sqlalchemy.orm import Session

from app.models.model import Permission, Role, RolePermission
from app.repositories.generic import CRUDRepository
from app.schemas.order_by_generator import OrderByCondition
from app.schemas.permission import PermissionSchemaPaginated
from app.schemas.role_permission import (
    RolePermissionSchema,
    RolePermissionSchemaPOSTRequest,
)
from app.schemas.user import (
    UserResponseSchema,
)
from app.utils.exception import ConflictError, NotFoundError


class RolePermissionService:
    def __init__(self, session: Session) -> None:
        """
        RolePermissionService constructor.
        """
        self.repository = CRUDRepository(session, RolePermission)
        self.role_repository = CRUDRepository(session, Role)
        self.permission_repository = CRUDRepository(session, Permission)

    def read_all(
        self, role_id: str, sort_by: list[OrderByCondition]
    ) -> PermissionSchemaPaginated:
        """
        Function to get all permissions of a role.
        """
        if self.role_repository.read_by_pk(role_id) is None:
            raise NotFoundError("Role not found")

        page = self.permission_repository.read_paginated_items(
            sort_by=sort_by,
            filters=(RolePermission.role_id == role_id),
            joins=[Permission.role_permissions],
        )
        return PermissionSchemaPaginated.model_validate(page, from_attributes=True)

    def create_role_permission(
        self,
        current_user: UserResponseSchema,
        role_id: str,
        request_body: RolePermissionSchemaPOSTRequest,
    ) -> RolePermissionSchema:
        """
        Create a new role permission object
        """
        if self.role_repository.read_by_pk(role_id) is None:
            raise NotFoundError("Role not found")

        permission_id = request_body.permission_id

        if self.permission_repository.read_by_pk(permission_id) is None:
            raise NotFoundError("Permission not found")

        existing_role_permission = self.repository.read_by_pk((role_id, permission_id))

        if existing_role_permission is not None:
            raise ConflictError("Permission already assigned to role")

        role_permission = self.repository.create_single_item(
            values=request_body.model_dump()
            | {
                "role_id": role_id,
                "created_by": current_user.user_id,
                "modified_by": current_user.user_id,
            },
        )
        return RolePermissionSchema.model_validate(role_permission)

    def delete_by_id(self, role_id: str, permission_id: UUID) -> None:
        """
        Function to delete a role permission by role ID and permission ID.
        """

        role_permission = self.repository.delete_single_item(
            filters=(
                (RolePermission.role_id == role_id)
                & (RolePermission.permission_id == permission_id)
            )
        )

        if not role_permission:
            raise NotFoundError("Role permission not found")
