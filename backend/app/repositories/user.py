from sqlalchemy import select
from sqlalchemy.orm import Session, lazyload
from typing import Type
from app.repositories.generic import CRUDRepository
from app.models.model import (
    User,
    Role,
    Permission,
)
from app.schemas.user import UserSchema


class UserRepository(CRUDRepository[User, UserSchema]):
    """
    User repository
    """

    def __init__(self, session: Session, model: Type[User]) -> None:
        """
        UserRepository constructor
        """
        super().__init__(session, model)

    def read_all_permissions(self, user_id: int):
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
