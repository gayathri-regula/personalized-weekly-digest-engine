"""FastAPI router for weekly digest generation and retrieval endpoints."""

from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import INTEREST_TAXONOMY
from app.db.session import get_db
from app.models.activity_item import ActivityItem
from app.models.digest import Digest
from app.models.digest_item import DigestItem
from app.models.feedback import ItemFeedback
from app.models.user import User
from app.schemas.digest import (
    AISuggestion,
    BoostRequest,
    BoostedDigestResponse,
    DigestItemResponse,
    DigestResponse,
)
from app.services.ai_suggestions import generate_ai_suggestions
from app.services.ranker import rank_items_for_user
from app.services.summarizer import generate_digest_summary
from app.utils import get_reference_now, get_week_identifier

router = APIRouter(prefix="/digest", tags=["digest"])


@router.post("/{user_id}/boost", response_model=BoostedDigestResponse)
async def boost_user_digest(
    user_id: str, boost_in: BoostRequest, db: AsyncSession = Depends(get_db)
) -> BoostedDigestResponse:
    """Generate a transient, read-only preview of user digest boosted by a specific taxonomy tag."""
    if boost_in.tag not in INTEREST_TAXONOMY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag '{boost_in.tag}' is not a valid taxonomy interest tag.",
        )

    # 1. Fetch user by user_id
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )

    # 2. Fetch all activity items
    items_result = await db.execute(
        select(ActivityItem).order_by(ActivityItem.created_at.desc())
    )
    items = items_result.scalars().all()
    items_by_id = {item.id: item for item in items}

    ref_now = get_reference_now()

    # 3. Score and rank items with boost_tag (read-only preview)
    ranked_items = rank_items_for_user(
        user=user, items=items, top_n=5, now=ref_now, boost_tag=boost_in.tag
    )

    # 4. Fetch existing feedback for user
    fb_result = await db.execute(
        select(ItemFeedback).where(ItemFeedback.user_id == user_id)
    )
    feedback_map = {
        fb.activity_item_id: fb.feedback_type for fb in fb_result.scalars().all()
    }

    response_items = []
    for r in ranked_items:
        act_item = items_by_id.get(r.activity_item_id)
        ditem_id = f"boost_{r.activity_item_id}"
        response_items.append(
            DigestItemResponse(
                id=ditem_id,
                activity_item_id=r.activity_item_id,
                title=act_item.title if act_item else "Untitled",
                content=act_item.content if act_item else "",
                category_tags=act_item.category_tags if act_item else [],
                relevance_score=r.relevance_score,
                explanation_text=r.explanation_text,
                rank_position=r.rank_position,
                feedback_type=feedback_map.get(r.activity_item_id),
            )
        )

    return BoostedDigestResponse(boost_tag=boost_in.tag, items=response_items)


@router.post("/{user_id}", response_model=DigestResponse)
async def generate_user_digest(
    user_id: str, db: AsyncSession = Depends(get_db)
) -> DigestResponse:
    """Generate or update (upsert) the weekly personalized digest for a user."""
    # 1. Fetch user by user_id
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )

    # 2. Fetch all activity items and calculate reference time & week identifier
    items_result = await db.execute(
        select(ActivityItem).order_by(ActivityItem.created_at.desc())
    )
    items = items_result.scalars().all()
    items_by_id = {item.id: item for item in items}

    ref_now = get_reference_now()
    week_id = get_week_identifier(ref_now)
    actual_generation_time = datetime.now(timezone.utc)

    # 3. Score and rank items using dataset reference time (ref_now)
    ranked_items = rank_items_for_user(
        user=user, items=items, top_n=5, now=ref_now
    )

    # 4. Join ranked items with full ActivityItem data for summarizer
    joined_details = []
    for r in ranked_items:
        act_item = items_by_id.get(r.activity_item_id)
        joined_details.append(
            {
                "activity_item_id": r.activity_item_id,
                "relevance_score": r.relevance_score,
                "explanation_text": r.explanation_text,
                "rank_position": r.rank_position,
                "title": act_item.title if act_item else "Untitled",
                "content": act_item.content if act_item else "",
                "category_tags": act_item.category_tags if act_item else [],
            }
        )

    # 5. Generate summary prose
    summary_prose = generate_digest_summary(
        user_name=user.name,
        ranked_items_with_details=joined_details,
        use_llm=True,
    )

    # 6. Generate AI suggestions (exploratory, separate from ranked items)
    ai_suggestions = generate_ai_suggestions(
        user_name=user.name,
        interest_tags=user.interest_tags or [],
        use_llm=True,
    )

    # 6. Upsert Digest record per (user_id, week_identifier) with real generation time
    digest_stmt = select(Digest).where(
        Digest.user_id == user_id, Digest.week_identifier == week_id
    )
    digest_result = await db.execute(digest_stmt)
    existing_digest = digest_result.scalar_one_or_none()

    if existing_digest is not None:
        digest_obj = existing_digest
        digest_obj.generated_at = actual_generation_time
        digest_obj.summary_prose = summary_prose
        digest_obj.ai_suggestions = ai_suggestions
        # Delete existing DigestItem rows for upsert replacement
        await db.execute(
            delete(DigestItem).where(DigestItem.digest_id == digest_obj.id)
        )
    else:
        digest_id = f"digest_{user_id}_{week_id}"
        digest_obj = Digest(
            id=digest_id,
            user_id=user_id,
            week_identifier=week_id,
            generated_at=actual_generation_time,
            summary_prose=summary_prose,
            ai_suggestions=ai_suggestions,
        )
        db.add(digest_obj)

    # Fetch existing feedback for user
    fb_result = await db.execute(
        select(ItemFeedback).where(ItemFeedback.user_id == user_id)
    )
    feedback_map = {
        fb.activity_item_id: fb.feedback_type for fb in fb_result.scalars().all()
    }

    # 7. Insert new DigestItem rows
    response_items = []
    for idx, (r, detail) in enumerate(zip(ranked_items, joined_details), start=1):
        ditem_id = f"ditem_{digest_obj.id}_{r.activity_item_id}"
        ditem = DigestItem(
            id=ditem_id,
            digest_id=digest_obj.id,
            activity_item_id=r.activity_item_id,
            relevance_score=r.relevance_score,
            explanation_text=r.explanation_text,
            rank_position=r.rank_position,
        )
        db.add(ditem)

        response_items.append(
            DigestItemResponse(
                id=ditem_id,
                activity_item_id=r.activity_item_id,
                title=detail["title"],
                content=detail["content"],
                category_tags=detail["category_tags"],
                relevance_score=r.relevance_score,
                explanation_text=r.explanation_text,
                rank_position=r.rank_position,
                feedback_type=feedback_map.get(r.activity_item_id),
            )
        )

    await db.commit()

    return DigestResponse(
        id=digest_obj.id,
        user_id=user_id,
        week_identifier=week_id,
        generated_at=digest_obj.generated_at,
        summary_prose=summary_prose,
        items=response_items,
        ai_suggestions=[AISuggestion(**s) for s in (digest_obj.ai_suggestions or [])],
    )


@router.get("/{user_id}", response_model=DigestResponse)
async def get_latest_user_digest(
    user_id: str, db: AsyncSession = Depends(get_db)
) -> DigestResponse:
    """Retrieve the most recently generated digest for a user from the database."""
    # 1. Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )

    # 2. Fetch most recent digest
    digest_stmt = (
        select(Digest)
        .where(Digest.user_id == user_id)
        .order_by(Digest.generated_at.desc())
    )
    digest_result = await db.execute(digest_stmt)
    digest_obj = digest_result.scalars().first()

    if digest_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No digest found for user '{user_id}'",
        )

    # 3. Fetch digest items ordered by rank_position
    items_stmt = (
        select(DigestItem)
        .where(DigestItem.digest_id == digest_obj.id)
        .order_by(DigestItem.rank_position.asc())
    )
    ditems_result = await db.execute(items_stmt)
    ditems = ditems_result.scalars().all()

    # 4. Fetch activity item details for response payload
    act_ids = [di.activity_item_id for di in ditems]
    if act_ids:
        act_result = await db.execute(
            select(ActivityItem).where(ActivityItem.id.in_(act_ids))
        )
        act_items = act_result.scalars().all()
        act_map = {ai.id: ai for ai in act_items}
    else:
        act_map = {}

    # Fetch existing feedback for user
    fb_result = await db.execute(
        select(ItemFeedback).where(ItemFeedback.user_id == user_id)
    )
    feedback_map = {
        fb.activity_item_id: fb.feedback_type for fb in fb_result.scalars().all()
    }

    response_items = []
    for di in ditems:
        act = act_map.get(di.activity_item_id)
        response_items.append(
            DigestItemResponse(
                id=di.id,
                activity_item_id=di.activity_item_id,
                title=act.title if act else "Untitled",
                content=act.content if act else "",
                category_tags=act.category_tags if act else [],
                relevance_score=di.relevance_score,
                explanation_text=di.explanation_text,
                rank_position=di.rank_position,
                feedback_type=feedback_map.get(di.activity_item_id),
            )
        )

    return DigestResponse(
        id=digest_obj.id,
        user_id=user_id,
        week_identifier=digest_obj.week_identifier,
        generated_at=digest_obj.generated_at,
        summary_prose=digest_obj.summary_prose,
        items=response_items,
        ai_suggestions=[AISuggestion(**s) for s in (digest_obj.ai_suggestions or [])],
    )
