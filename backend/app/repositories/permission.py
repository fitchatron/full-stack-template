from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Type
from app.repositories.generic import CRUDRepository
from app.models.model import Role, Permission
from app.schemas.permission import PermissionSchema


class PermissionRepository(CRUDRepository[Permission, PermissionSchema]):
    """
    Permission repository
    """

    def __init__(self, session: Session, model: Type[Permission]) -> None:
        """
        Permission Repository constructor
        """
        super().__init__(session, model)

    def read_all_permissions_for_user_id(self, user_id: int):
        """
        Read user permissions at app level
        """

        sql = (
            select(Permission)
            .select_from(self.model)
            .join(self.model.user_roles)
            .join(Role)
            .join(Role.role_permissions)
            .join(Permission)
            .where(self.model.user_id == user_id)
            .distinct()
        )

        # execute sql
        result = self.session.scalars(sql).all()
        return result
