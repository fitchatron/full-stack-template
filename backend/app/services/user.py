from sqlalchemy.orm import Session
from fastapi import HTTPException
from pydantic import TypeAdapter
from app.models.model import User, Role, Permission, UserRole
from app.schemas.user import (
    UserSchema,
)
from app.schemas.permission import (
    PermissionSchema,
)
from app.repositories.user import UserRepository
from app.repositories.generic import CRUDRepository
from app.repositories.permission import PermissionRepository
from backend.app.schemas.filter_generator import (
    ComparisonOperator,
    FilterCondition,
    FilterPayload,
)


class UserService:
    def __init__(self, session: Session) -> None:
        """
        UserService constructor.
        """

        self.repository = UserRepository(session, User)
        self.user_role_repository = CRUDRepository(session, UserRole)
        self.permission_repository = PermissionRepository(session, Permission)

    def read_by_id(self, user_id: int) -> User | None:
        """
        Function to get user by ID.
        """
        try:
            user = self.repository.read_single_item(
                filters=FilterPayload(
                    where=(
                        FilterCondition(
                            column="user_id",
                            operator=ComparisonOperator.eq_,
                            value=user_id,
                        )
                    )
                )
            )
            return user

        except Exception as exception:
            # LOG.exception("Exception")
            raise HTTPException(status_code=500, detail=str(exception))

    def read_active_permissions_for_user_id(
        self, user_id: int
    ) -> list[PermissionSchema]:
        """
        Function to get user permissions at app level.
        """
        try:
            permissions = self.permission_repository.read_all_permissions_for_user_id(
                user_id
            )
            return TypeAdapter(list[PermissionSchema]).validate_python(permissions)

        except Exception as exception:
            # LOG.exception("Exception")
            raise HTTPException(status_code=500, detail=str(exception))
