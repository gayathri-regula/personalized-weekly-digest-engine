"""SQLAlchemy ORM model for User entity."""

from typing import TYPE_CHECKING, List
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.digest import Digest


class User(Base):
    """User entity representing platform users and their interest topics."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # Using SQLAlchemy JSON column type to store interest_tags as a list of strings,
    # providing cross-database compatibility while leveraging native JSON support in PostgreSQL.
    interest_tags: Mapped[List[str]] = mapped_column(JSON, nullable=False)

    digests: Mapped[List["Digest"]] = relationship(
        "Digest", back_populates="user", cascade="all, delete-orphan"
    )
