"""SQLAlchemy ORM model for Digest entity."""

from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.digest_item import DigestItem
    from app.models.user import User


class Digest(Base):
    """Digest entity representing a weekly generated summary for a user."""

    __tablename__ = "digests"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "week_identifier", name="uq_digest_user_week"
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False
    )
    week_identifier: Mapped[str] = mapped_column(String, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    summary_prose: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="digests")
    items: Mapped[List["DigestItem"]] = relationship(
        "DigestItem", back_populates="digest", cascade="all, delete-orphan"
    )
