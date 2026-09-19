from datetime import datetime
from typing import Optional
from sqlalchemy import Text, DateTime, ForeignKey, UniqueConstraint, text, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.db import Base
from app.models.enums import AuthorizationAction, authorization_action_type
from app.models.mixins import AuditMixin


# TODO: add relationships
class User(Base):
    """
    User database model
    """

    __tablename__ = "users"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        server_default=text("gen_random_uuid()"),
        primary_key=True,
        index=True,
    )
    username: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text)
    hashed_password: Mapped[str] = mapped_column(Text)
    salt: Mapped[str] = mapped_column(Text)
    given_name: Mapped[Optional[str]] = mapped_column(Text)
    family_name: Mapped[Optional[str]] = mapped_column(Text)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey(user_id))
    modified_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey(user_id))

    __table_args__ = (
        UniqueConstraint(email),
        UniqueConstraint(username),
    )

    # MARK: Relationships
    # user roles
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        foreign_keys="[UserRole.user_id]",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # roles
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="user_roles",
        primaryjoin="User.user_id == UserRole.user_id",
        secondaryjoin="UserRole.role_id == Role.role_id",
        viewonly=True,
    )

    # audit
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
        remote_side="[User.user_id]",
    )

    modified_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[modified_by],
        remote_side="[User.user_id]",
    )


class Permission(AuditMixin, Base):
    """
    Permission database model
    """

    __tablename__ = "permissions"
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        server_default=text("gen_random_uuid()"),
        primary_key=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text)
    action: Mapped[AuthorizationAction] = mapped_column(authorization_action_type)
    resource: Mapped[str] = mapped_column(Text)

    # MARK: Relationships
    role_permissions: Mapped[list["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan",
    )
    __table_args__ = (UniqueConstraint(action, resource),)


class Role(AuditMixin, Base):
    """
    Role database model
    """

    __tablename__ = "roles"
    role_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, index=True)
    description: Mapped[str] = mapped_column(Text)

    # MARK: Relationships
    role_permissions: Mapped[list["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
    )
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint(name),)


class RolePermission(AuditMixin, Base):
    """
    RolePermission database model
    """

    __tablename__ = "role_permissions"
    role_id: Mapped[str] = mapped_column(
        ForeignKey(Role.role_id, ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Permission.permission_id, ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    # MARK: Relationships
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="role_permissions",
        primaryjoin="RolePermission.role_id == Role.role_id",
    )

    permission: Mapped["Permission"] = relationship(
        "Permission",
        back_populates="role_permissions",
        primaryjoin="RolePermission.permission_id == Permission.permission_id",
    )


class UserRole(AuditMixin, Base):
    """
    UserRole database model
    """

    __tablename__ = "user_roles"
    user_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        server_default=text("gen_random_uuid()"),
        primary_key=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(User.user_id, ondelete="CASCADE"),
        index=True,
    )
    role_id: Mapped[str] = mapped_column(
        ForeignKey(Role.role_id, ondelete="CASCADE"),
        index=True,
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now() + text("interval '1 year'"),
    )

    # MARK: Relationships
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="user_roles",
        primaryjoin="UserRole.role_id == Role.role_id",
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys="[UserRole.user_id]",
        back_populates="user_roles",
        primaryjoin="UserRole.user_id == User.user_id",
    )
    __table_args__ = (UniqueConstraint(user_id, role_id),)
