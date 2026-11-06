from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.model import Role, User, UserRole
from app.repositories.generic import CRUDRepository
from app.repositories.user import UserRepository
from app.schemas.order_by_generator import OrderByCondition
from app.schemas.user import (
    UserResponseSchema,
)
from app.schemas.user_role import (
    UserRoleSchema,
    UserRoleSchemaPaginated,
    UserRoleSchemaPATCHRequest,
    UserRoleSchemaPOSTRequest,
)
from app.utils.exception import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)

DEFAULT_USER_ROLE_DURATION = timedelta(days=365)


class UserRoleService:
    def __init__(self, session: Session) -> None:
        """
        UserRoleService constructor.
        """
        self.repository = CRUDRepository(session, UserRole)
        self.user_repository = UserRepository(session, User)
        self.role_repository = CRUDRepository(session, Role)

    def _read_by_id(self, user_id: UUID, user_role_id: UUID) -> UserRole:
        """
        Internal method to read a user role that belongs to the given user.
        """
        user_role = self.repository.read_single_item(
            filters=(
                and_(UserRole.user_role_id == user_role_id, UserRole.user_id == user_id)
            )
        )

        if not user_role:
            raise NotFoundError("User role not found")
        return user_role

    def _verify_no_overlap(
        self,
        user_id: UUID,
        role_id: str,
        start_at: datetime,
        end_at: datetime,
        ignored_user_role_id: UUID | None = None,
    ) -> None:
        """
        Internal method to verify the user doesn't hold the role at any point in the period.
        Both ends are inclusive, matching how active user roles are read.
        """
        conditions = [
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.start_at <= end_at,
            UserRole.end_at >= start_at,
        ]

        if ignored_user_role_id is not None:
            conditions.append(UserRole.user_role_id != ignored_user_role_id)

        if self.repository.read_single_item(filters=and_(*conditions)) is not None:
            raise ConflictError("User already holds this role during this period")

    def read_all(
        self, user_id: UUID, sort_by: list[OrderByCondition]
    ) -> UserRoleSchemaPaginated:
        """
        Function to get all user roles of a user, including inactive ones.
        """
        if self.user_repository.read_by_pk(user_id) is None:
            raise NotFoundError("User not found")

        page = self.repository.read_paginated_items(
            sort_by=sort_by, filters=(UserRole.user_id == user_id)
        )
        return UserRoleSchemaPaginated.model_validate(page, from_attributes=True)

    def create_user_role(
        self,
        current_user: UserResponseSchema,
        user_id: UUID,
        request_body: UserRoleSchemaPOSTRequest,
    ) -> UserRoleSchema:
        """
        Create a new user role object
        """
        start_at = request_body.start_at or datetime.now(UTC)
        try:
            end_at = request_body.end_at or start_at + DEFAULT_USER_ROLE_DURATION
        except OverflowError:
            raise BadRequestError("start_at is too far in the future") from None

        if current_user.user_id == user_id:
            raise ForbiddenError("Users cannot change their own roles")

        if self.user_repository.read_by_pk(user_id) is None:
            raise NotFoundError("User not found")

        role_id = request_body.role_id

        if self.role_repository.read_by_pk(role_id) is None:
            raise NotFoundError("Role not found")

        start_at = request_body.start_at or datetime.now(UTC)
        end_at = request_body.end_at or start_at + DEFAULT_USER_ROLE_DURATION

        if start_at > end_at:
            raise BadRequestError("start_at cannot be later than end_at")

        self._verify_no_overlap(
            user_id=user_id, role_id=role_id, start_at=start_at, end_at=end_at
        )

        user_role = self.repository.create_single_item(
            values={
                "user_id": user_id,
                "role_id": role_id,
                "start_at": start_at,
                "end_at": end_at,
                "created_by": current_user.user_id,
                "modified_by": current_user.user_id,
            },
        )
        return UserRoleSchema.model_validate(user_role)

    def patch_by_id(
        self,
        current_user: UserResponseSchema,
        user_id: UUID,
        user_role_id: UUID,
        request_body: UserRoleSchemaPATCHRequest,
    ) -> UserRoleSchema:
        """
        Update the dates of an existing user role by ID.
        Scheduled user roles can change both dates, active user roles only their
        end date and expired user roles neither. Neither date can move into the past.
        """
        if current_user.user_id == user_id:
            raise ForbiddenError("Users cannot change their own roles")

        user_role = self._read_by_id(user_id=user_id, user_role_id=user_role_id)
        now = datetime.now(UTC)

        if user_role.end_at < now:
            raise ConflictError("Expired user roles cannot be changed")

        values = request_body.model_dump(exclude_unset=True)

        if "start_at" in values:
            if user_role.start_at <= now:
                raise ConflictError("Active user roles cannot change their start date")

            if values["start_at"] < now:
                raise BadRequestError("start_at cannot be in the past")

        start_at = values.get("start_at", user_role.start_at)
        end_at = values.get("end_at", user_role.end_at)

        if end_at < now:
            raise BadRequestError("end_at cannot be in the past")

        if start_at > end_at:
            raise BadRequestError("start_at cannot be later than end_at")

        self._verify_no_overlap(
            user_id=user_id,
            role_id=user_role.role_id,
            start_at=start_at,
            end_at=end_at,
            ignored_user_role_id=user_role_id,
        )

        updated_user_role = self.repository.update_single_item(
            filters=(UserRole.user_role_id == user_role_id),
            values=values | {"modified_by": current_user.user_id},
        )
        return UserRoleSchema.model_validate(updated_user_role)

    def delete_by_id(
        self, current_user: UserResponseSchema, user_id: UUID, user_role_id: UUID
    ) -> None:
        """
        Function to revoke a user role by ID. Active user roles end now and are kept
        for audit, scheduled user roles never granted access so they're deleted.
        """
        if current_user.user_id == user_id:
            raise ForbiddenError("Users cannot change their own roles")

        user_role = self._read_by_id(user_id=user_id, user_role_id=user_role_id)
        now = datetime.now(UTC)

        if user_role.end_at < now:
            raise ConflictError("Expired user roles cannot be changed")

        if user_role.start_at > now:
            self.repository.delete_single_item(
                filters=(UserRole.user_role_id == user_role_id)
            )
            return

        self.repository.update_single_item(
            filters=(UserRole.user_role_id == user_role_id),
            values={"end_at": now, "modified_by": current_user.user_id},
        )
