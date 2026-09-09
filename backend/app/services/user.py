from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import TypeAdapter

from app.schemas.user import (
    UserSchema,
)
from app.repositories.user import UserRepository
from app.repositories.generic import CRUDRepository


class UserService:
    def __init__(self, session: Session) -> None:
        """
        UserService constructor.
        """

        self.repository = UserRepository(session, User)
        self.user_role_repository = CRUDRepository(session, UserRole)

    def read_active_permissions_for_user_id(
        self, user_id: int
    ) -> list[PermissionSchema]:
        """
        Function to get user permissions at app level.
        """
        try:
            # check user first
            permissions = self.repository.read_all_permissions(user_id)
            return TypeAdapter(list[PermissionSchema]).validate_python(permissions)

        except Exception as exception:
            LOG.exception("Exception")
            raise HTTPException(status_code=500, detail=str(exception))
