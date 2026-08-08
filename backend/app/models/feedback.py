"""SQLAlchemy ORM model for ItemFeedback entity."""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ItemFeedback(Base):
    """ItemFeedback entity representing explicit user ratings on digest items."""

    __tablename__ = "item_feedback"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False
    )
    activity_item_id: Mapped[str] = mapped_column(
        String, ForeignKey("activity_items.id"), nullable=False
    )
    feedback_type: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "activity_item_id", name="uq_user_activity_feedback"
        ),
    )
