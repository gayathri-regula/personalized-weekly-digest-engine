"""FastAPI router for user item feedback endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.activity_item import ActivityItem
from app.models.feedback import ItemFeedback
from app.models.user import User
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.activity_logger import log_user_activity

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post(
    "/{user_id}/{activity_item_id}",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_item_feedback(
    user_id: str,
    activity_item_id: str,
    feedback_in: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    """Upsert feedback (insert or update) for a specific user and activity item."""
    # 1. Validate user existence (404 if not found)
    user_stmt = select(User).where(User.id == user_id)
    user_res = await db.execute(user_stmt)
    user = user_res.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )

    # 2. Validate activity item existence (404 if not found)
    item_stmt = select(ActivityItem).where(ActivityItem.id == activity_item_id)
    item_res = await db.execute(item_stmt)
    item = item_res.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity item '{activity_item_id}' not found",
        )

    # 3. Check for existing feedback row (upsert logic)
    fb_stmt = select(ItemFeedback).where(
        ItemFeedback.user_id == user_id,
        ItemFeedback.activity_item_id == activity_item_id,
    )
    fb_res = await db.execute(fb_stmt)
    existing_fb = fb_res.scalar_one_or_none()

    now_utc = datetime.now(timezone.utc)

    if existing_fb is not None:
        existing_fb.feedback_type = feedback_in.feedback_type
        existing_fb.created_at = now_utc
        fb_obj = existing_fb
    else:
        fb_id = f"fb_{user_id}_{activity_item_id}"
        fb_obj = ItemFeedback(
            id=fb_id,
            user_id=user_id,
            activity_item_id=activity_item_id,
            feedback_type=feedback_in.feedback_type,
            created_at=now_utc,
        )
        db.add(fb_obj)

    readable_type = feedback_in.feedback_type.replace("_", " ").title()
    await log_user_activity(
        db,
        user_id=user_id,
        event_type="feedback_submitted",
        description=f"Marked story as '{readable_type}'",
    )

    await db.commit()
    await db.refresh(fb_obj)

    return FeedbackResponse.model_validate(fb_obj)
