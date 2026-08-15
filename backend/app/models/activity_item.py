"""SQLAlchemy ORM model for ActivityItem entity."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import JSON, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.digest_item import DigestItem


class ActivityItem(Base):
    """ActivityItem entity representing weekly community content items."""

    __tablename__ = "activity_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Using SQLAlchemy JSON column type to store category_tags as a list of strings.
    category_tags: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    section_title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    engagement_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False
    )
    is_ai_generated: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    digest_items: Mapped[List["DigestItem"]] = relationship(
        "DigestItem", back_populates="activity_item"
    )

