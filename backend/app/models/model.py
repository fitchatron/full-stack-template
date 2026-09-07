from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


class User(Base):
    """
    User database model
    """

    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True
    )
    email: Mapped[str] = mapped_column(Text)
    username: Mapped[str] = mapped_column(Text, index=True)
    given_name: Mapped[Optional[str]] = mapped_column(Text)
    family_name: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey(user_id))
    modified_by: Mapped[Optional[int]] = mapped_column(ForeignKey(user_id))

    # Unique constraint
    __table_args__ = (
        UniqueConstraint(email),
        UniqueConstraint(username),
    )

    # audit
    created_by_user: Mapped["User"] = relationship(
        "User",
        primaryjoin="User.user_id == User.created_by",
        foreign_keys=[created_by],
        remote_side="[User.user_id]",
    )

    modified_by_user: Mapped["User"] = relationship(
        "User",
        primaryjoin="User.user_id == User.modified_by",
        foreign_keys=[modified_by],
        remote_side="[User.user_id]",
    )
