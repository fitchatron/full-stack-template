import uuid

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session
from typing import Type
from app.repositories.generic import CRUDRepository
from app.models.model import Role, Permission, UserRole
from app.schemas.permission import PermissionSchema
from app.core.app_permissions import AppPermissions


class PermissionRepository(CRUDRepository[Permission, PermissionSchema]):
    """
    Permission repository
    """

    def __init__(self, session: Session, model: Type[Permission]) -> None:
        """
        Permission Repository constructor
        """
        super().__init__(session, model)

    def _active_for_user_query(self, user_id: uuid.UUID) -> Select[tuple[Permission]]:
        """
        Build a query for the permissions granted by the user's currently active roles
        """

        return (
            select(Permission)
            .select_from(Role)
            .join(Role.role_permissions)
            .join(Role.user_roles)
            .join(Permission)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.start_at <= func.now(),
                    UserRole.end_at >= func.now(),
                )
            )
            .distinct()
        )

    def read_active_for_user(self, user_id: uuid.UUID):
        """
        Read user permissions at app level
        """

        sql = self._active_for_user_query(user_id)

        # execute sql
        result = self.session.scalars(sql).all()
        return result

    def read_active_for_user_and_required_permissions(
        self, user_id: uuid.UUID, required_permissions: list[AppPermissions]
    ):
        """
        Read the user's active permissions that grant at least one of the required permissions
        """

        sql = self._active_for_user_query(user_id).where(
            or_(*(perm.to_granted_by_clause() for perm in required_permissions))
        )

        # execute sql
        result = self.session.scalars(sql).all()
        return result
