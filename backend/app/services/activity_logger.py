"""Activity logging service for inserting user action records."""

from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity_log import ActivityLog


async def log_user_activity(
    db: AsyncSession,
    user_id: str,
    event_type: str,
    description: str,
) -> ActivityLog:
    """Insert a lightweight user activity log entry into the active database session."""
    log_id = f"log_{uuid4().hex[:12]}"
    log_entry = ActivityLog(
        id=log_id,
        user_id=user_id,
        event_type=event_type,
        description=description,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log_entry)
    return log_entry
