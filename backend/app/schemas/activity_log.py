"""Pydantic schemas for Activity Log API endpoints."""

from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict


class ActivityLogResponse(BaseModel):
    """Payload representing a single user activity log entry."""

    id: str
    user_id: str
    event_type: str
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityLogListResponse(BaseModel):
    """Paginated response payload containing user activity log history."""

    items: List[ActivityLogResponse]
    total: int
