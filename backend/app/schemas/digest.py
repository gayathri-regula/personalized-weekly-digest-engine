"""Pydantic response schemas for digest endpoints."""

from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict, Field


class DigestItemResponse(BaseModel):
    """Schema representing an individual ranked activity item within a digest response."""

    id: str = Field(..., description="DigestItem row ID")
    activity_item_id: str = Field(..., description="Activity item ID")
    title: str = Field(..., description="Activity item title")
    content: str = Field(..., description="Activity item content")
    category_tags: List[str] = Field(
        default_factory=list, description="Category tags for the activity item"
    )
    relevance_score: float = Field(
        ..., description="Computed relevance score (0.0 to 1.0)"
    )
    explanation_text: str = Field(
        ..., description="Truthful explanation text for why item was selected"
    )
    rank_position: int = Field(
        ..., description="1-indexed rank position in the digest"
    )

    model_config = ConfigDict(from_attributes=True)


class DigestResponse(BaseModel):
    """Schema representing the full digest payload returned by API endpoints."""

    id: str = Field(..., description="Digest ID")
    user_id: str = Field(..., description="User ID receiving the digest")
    week_identifier: str = Field(
        ..., description="ISO week identifier (e.g. 2026-W30)"
    )
    generated_at: datetime = Field(
        ..., description="Timestamp when digest was generated"
    )
    summary_prose: str = Field(
        ..., description="Executive summary prose text"
    )
    items: List[DigestItemResponse] = Field(
        default_factory=list, description="Top-ranked items for this digest"
    )

    model_config = ConfigDict(from_attributes=True)
