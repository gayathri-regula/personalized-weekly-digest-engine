"""Pydantic schemas for Saved Item API endpoints."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SavedItemResponse(BaseModel):
    """Payload returned when an item is saved."""

    id: str
    user_id: str
    activity_item_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavedItemDetailResponse(BaseModel):
    """Payload returned when listing saved items for a user, joined with ActivityItem details."""

    id: str
    user_id: str
    activity_item_id: str
    title: str
    content: str
    category_tags: List[str]
    section_title: Optional[str] = None
    explanation_text: Optional[str] = None
    created_at: Optional[datetime] = None
    saved_at: datetime

    model_config = ConfigDict(from_attributes=True)
