import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from sqlalchemy.sql import func


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
    def created_by(cls) -> Mapped[Optional[uuid.UUID]]:
        return mapped_column(ForeignKey("users.user_id"))

    @declared_attr
    def modified_by(cls) -> Mapped[Optional[uuid.UUID]]:
        return mapped_column(ForeignKey("users.user_id"))

    @declared_attr
    def created_by_user(cls) -> Mapped[Optional["User"]]:  # noqa: F821
        return relationship("User", foreign_keys=[cls.created_by])

    @declared_attr
    def modified_by_user(cls) -> Mapped[Optional["User"]]:  # noqa: F821
        return relationship("User", foreign_keys=[cls.modified_by])
