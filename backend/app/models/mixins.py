import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from app.models.model import User


class AuditMixin:
    """
    Audit mixin for created/modified timestamp and user columns.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @declared_attr
    def created_by(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"))

    @declared_attr
    def modified_by(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"))

    @declared_attr
    @classmethod
    def created_by_user(cls) -> Mapped[User | None]:
        return relationship("User", foreign_keys=[cls.created_by])

    @declared_attr
    @classmethod
    def modified_by_user(cls) -> Mapped[User | None]:
        return relationship("User", foreign_keys=[cls.modified_by])
