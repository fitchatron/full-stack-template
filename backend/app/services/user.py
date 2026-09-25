from uuid import UUID

from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import TypeAdapter
from app.models.model import User, Role, Permission, UserRole
from app.schemas.permission import (
    PermissionSchema,
)
from app.repositories.user import UserRepository
from app.repositories.generic import CRUDRepository
from app.repositories.permission import PermissionRepository
from app.core.app_permissions import AppPermissions


class UserService:
    def __init__(self, session: Session) -> None:
        """
        UserService constructor.
        """

        self.repository = UserRepository(session, User)
        self.user_role_repository = CRUDRepository(session, UserRole)
        self.permission_repository = PermissionRepository(session, Permission)

    def read_by_id(self, user_id: UUID) -> User | None:
        """
        Function to get user by ID.
        """
        try:
            return self.repository.read_user_by_id(user_id)

        except Exception as exception:
            # LOG.exception("Exception")
            raise HTTPException(status_code=500, detail=str(exception))

    def read_active_permissions_for_user_id(
        self, user_id: UUID
    ) -> list[PermissionSchema]:
        """
        Function to get user permissions at app level.
        """
        try:
            permissions = (
                self.permission_repository.read_active_permissions_for_user_id(user_id)
            )
            return TypeAdapter(list[PermissionSchema]).validate_python(permissions)

        except Exception as exception:
            # LOG.exception("Exception")
            raise HTTPException(status_code=500, detail=str(exception))

    def has_all_permissions(
        self, user_id: UUID, required_permissions: list[AppPermissions]
    ):
        """
        Function to check if the user has all specified permissions at app level.
        """
        if not required_permissions:
            return True

        try:
            permissions = self.permission_repository.read_active_permissions_for_user_id_and_required_permissions(
                user_id=user_id, required_permissions=required_permissions
            )
            return all(
                any(required.is_granted_by(p.action, p.resource) for p in permissions)
                for required in required_permissions
            )

        except Exception as exception:
            # LOG.exception("Exception")
            raise HTTPException(status_code=500, detail=str(exception))
