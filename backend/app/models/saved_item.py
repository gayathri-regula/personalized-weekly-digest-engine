"""SQLAlchemy ORM model for SavedItem entity."""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class SavedItem(Base):
    """SavedItem entity representing a user-bookmarked digest activity item."""

    __tablename__ = "saved_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False
    )
    activity_item_id: Mapped[str] = mapped_column(
        String, ForeignKey("activity_items.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "activity_item_id", name="uq_user_saved_item"
        ),
    )
