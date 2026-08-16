"""FastAPI router for saved items endpoints."""

from datetime import datetime, timezone
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.activity_item import ActivityItem
from app.models.digest import Digest
from app.models.digest_item import DigestItem
from app.models.saved_item import SavedItem
from app.models.user import User
from app.schemas.saved_item import SavedItemDetailResponse, SavedItemResponse
from app.services.activity_logger import log_user_activity

router = APIRouter(prefix="/saved", tags=["saved"])


@router.post(
    "/{user_id}/{activity_item_id}",
    response_model=SavedItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_item(
    user_id: str,
    activity_item_id: str,
    db: AsyncSession = Depends(get_db),
) -> SavedItemResponse:
    """Save an activity item for a specific user profile."""
    # 1. Validate user existence
    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found.",
        )

    # 2. Validate activity item existence
    item_res = await db.execute(
        select(ActivityItem).where(ActivityItem.id == activity_item_id)
    )
    item = item_res.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity item '{activity_item_id}' not found.",
        )

    # 3. Check for existing saved record (idempotent)
    saved_res = await db.execute(
        select(SavedItem).where(
            SavedItem.user_id == user_id,
            SavedItem.activity_item_id == activity_item_id,
        )
    )
    existing_saved = saved_res.scalar_one_or_none()
    if existing_saved is not None:
        return SavedItemResponse.model_validate(existing_saved)

    # 4. Insert new SavedItem record
    now_utc = datetime.now(timezone.utc)
    save_id = f"save_{user_id}_{activity_item_id}"
    saved_obj = SavedItem(
        id=save_id,
        user_id=user_id,
        activity_item_id=activity_item_id,
        created_at=now_utc,
    )
    db.add(saved_obj)

    # 5. Log activity event
    short_title = item.title[:40] + "..." if len(item.title) > 40 else item.title
    await log_user_activity(
        db,
        user_id=user_id,
        event_type="item_saved",
        description=f"Saved story '{short_title}' to reading list",
    )

    await db.commit()
    await db.refresh(saved_obj)

    return SavedItemResponse.model_validate(saved_obj)


@router.delete(
    "/{user_id}/{activity_item_id}",
    status_code=status.HTTP_200_OK,
)
async def unsave_item(
    user_id: str,
    activity_item_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Unsave (remove) an activity item from a user's saved reading list."""
    saved_res = await db.execute(
        select(SavedItem).where(
            SavedItem.user_id == user_id,
            SavedItem.activity_item_id == activity_item_id,
        )
    )
    saved_obj = saved_res.scalar_one_or_none()

    if saved_obj is not None:
        # Fetch item for title in log description
        item_res = await db.execute(
            select(ActivityItem).where(ActivityItem.id == activity_item_id)
        )
        item = item_res.scalar_one_or_none()
        title_str = item.title if item else activity_item_id
        short_title = title_str[:40] + "..." if len(title_str) > 40 else title_str

        await db.delete(saved_obj)
        await log_user_activity(
            db,
            user_id=user_id,
            event_type="item_unsaved",
            description=f"Removed story '{short_title}' from saved reading list",
        )
        await db.commit()

    return {"status": "success", "message": "Item unsaved successfully."}


@router.get(
    "/{user_id}",
    response_model=List[SavedItemDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def get_user_saved_items(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[SavedItemDetailResponse]:
    """Retrieve all saved items for a specific user with joined ActivityItem details."""
    # Validate user existence
    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found.",
        )

    # Correlated subquery to fetch explanation_text from the user's most recent DigestItem
    explanation_subq = (
        select(DigestItem.explanation_text)
        .join(Digest, DigestItem.digest_id == Digest.id)
        .where(
            Digest.user_id == user_id,
            DigestItem.activity_item_id == SavedItem.activity_item_id,
        )
        .order_by(Digest.generated_at.desc())
        .limit(1)
        .scalar_subquery()
    )

    stmt = (
        select(SavedItem, ActivityItem, explanation_subq.label("explanation_text"))
        .join(ActivityItem, SavedItem.activity_item_id == ActivityItem.id)
        .where(SavedItem.user_id == user_id)
        .order_by(SavedItem.created_at.desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for saved, act, exp_text in rows:
        items.append(
            SavedItemDetailResponse(
                id=saved.id,
                user_id=saved.user_id,
                activity_item_id=saved.activity_item_id,
                title=act.title,
                content=act.content,
                category_tags=act.category_tags or [],
                section_title=act.section_title,
                explanation_text=exp_text,
                created_at=act.created_at,
                saved_at=saved.created_at,
            )
        )

    return items
