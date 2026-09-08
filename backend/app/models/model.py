from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.db import Base
from app.models.enums import AuthorizationAction, authorization_action_type
from app.models.mixins import AuditMixin


class User(Base):
    """
    User database model
    """

    __tablename__ = "users"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    email: Mapped[str] = mapped_column(Text)
    username: Mapped[str] = mapped_column(Text)
    given_name: Mapped[Optional[str]] = mapped_column(Text)
    family_name: Mapped[Optional[str]] = mapped_column(Text)
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

    # audit
    created_by_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
        remote_side="[User.user_id]",
    )

    modified_by_user: Mapped["User"] = relationship(
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
        default=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text)
    action: Mapped[AuthorizationAction] = mapped_column(authorization_action_type)
    resource: Mapped[str] = mapped_column(Text)

    __table_args__ = (UniqueConstraint(action, resource),)


class Role(AuditMixin, Base):
    """
    Role database model
    """

    __tablename__ = "roles"
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(Text, index=True)
    description: Mapped[str] = mapped_column(Text)

    __table_args__ = (UniqueConstraint(name),)


class RolePermission(AuditMixin, Base):
    """
    RolePermission database model
    """

    __tablename__ = "role_permissions"
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Role.role_id, ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(Permission.permission_id, ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )


class UserRole(AuditMixin, Base):
    """
    UserRole database model
    """

    __tablename__ = "user_roles"
    user_role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(User.user_id, ondelete="CASCADE"),
        index=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
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

    __table_args__ = (UniqueConstraint(user_id, role_id),)
