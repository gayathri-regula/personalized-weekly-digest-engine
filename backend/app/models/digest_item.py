"""SQLAlchemy ORM model for DigestItem entity."""

from typing import TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.activity_item import ActivityItem
    from app.models.digest import Digest


class DigestItem(Base):
    """DigestItem entity representing ranked activity line items within a digest."""

    __tablename__ = "digest_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    digest_id: Mapped[str] = mapped_column(
        String, ForeignKey("digests.id"), nullable=False
    )
    activity_item_id: Mapped[str] = mapped_column(
        String, ForeignKey("activity_items.id"), nullable=False
    )
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation_text: Mapped[str] = mapped_column(Text, nullable=False)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)

    digest: Mapped["Digest"] = relationship("Digest", back_populates="items")
    activity_item: Mapped["ActivityItem"] = relationship(
        "ActivityItem", back_populates="digest_items"
    )
