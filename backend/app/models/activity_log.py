"""SQLAlchemy ORM model for ActivityLog entity."""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ActivityLog(Base):
    """ActivityLog entity representing user action event history."""

    __tablename__ = "activity_log"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        Index("idx_activity_log_user_created", "user_id", "created_at"),
    )
