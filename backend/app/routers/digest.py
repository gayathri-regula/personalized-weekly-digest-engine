"""FastAPI router for weekly digest generation and retrieval endpoints."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from app.services.ai_digest_generator import generate_ai_digest_items
from app.services.ai_suggestions import generate_ai_suggestions
from app.services.summarizer import generate_digest_summary
from app.utils import get_reference_now, get_week_identifier

router = APIRouter(prefix="/digest", tags=["digest"])


@router.post("/{user_id}/boost", response_model=BoostedDigestResponse)
async def boost_user_digest(
    user_id: str, boost_in: BoostRequest, db: AsyncSession = Depends(get_db)
) -> BoostedDigestResponse:
    """Generate a transient, read-only preview of user digest boosted by a specific tag/topic.

    Generates 5 fresh AI items emphasizing the boost tag (open-ended), persists the ActivityItem
    rows with 'boost_act_' IDs for foreign key reference, and returns a BoostedDigestResponse payload.
    """
    # 1. Fetch user by user_id
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )

    boost_tag = boost_in.tag.strip() if boost_in.tag else "Technology"

    # 2. Generate 5 fresh AI items focused on boost_tag
    raw_ai_items = generate_ai_digest_items(
        user_name=user.name,
        interest_tags=[boost_tag] + (user.interest_tags or []),
        use_llm=True,
    )

    # 3. Create and persist ActivityItem objects with prefix "boost_act_"
    response_items = []
    for raw in raw_ai_items:
        boost_act_id = f"boost_act_{uuid4().hex[:12]}"
        act_obj = ActivityItem(
            id=boost_act_id,
            title=raw["title"],
            content=raw["content"],
            category_tags=raw["category_tags"],
            section_title=raw.get("section_title"),
            created_at=raw["created_at"],
            engagement_metadata=raw["engagement_metadata"],
            is_ai_generated=True,
        )
        db.add(act_obj)

        response_items.append(
            DigestItemResponse(
                id=f"boost_item_{boost_act_id}",
                activity_item_id=boost_act_id,
                title=raw["title"],
                content=raw["content"],
                category_tags=raw["category_tags"],
                section_title=raw.get("section_title"),
                relevance_score=raw["relevance_score"],
                explanation_text=raw.get(
                    "explanation_text", f"Boosted highlight focused on {boost_tag}"
                ),
                rank_position=raw["rank_position"],
                feedback_type=None,
                created_at=raw["created_at"],
            )
        )

    await db.commit()

    return BoostedDigestResponse(boost_tag=boost_tag, items=response_items)


@router.post("/{user_id}", response_model=DigestResponse)
async def generate_user_digest(
    user_id: str,
    diversity: Optional[bool] = Query(False),
    mode: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> DigestResponse:
    """Generate or update (upsert) the weekly personalized digest for a user.

    Uses AI generation as the single unified path for all users and modes.
    """
    # 1. Fetch user by user_id
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )

    ref_now = get_reference_now()
    week_id = get_week_identifier(ref_now)
    actual_generation_time = datetime.now(timezone.utc)

    # 2. Generate 5 AI activity items for this user (60/40 interest/explore ratio)
    raw_ai_items = generate_ai_digest_items(
        user_name=user.name,
        interest_tags=user.interest_tags or [],
        use_llm=True,
    )

    # 3. Create ActivityItem ORM objects with is_ai_generated=True and persist them
    joined_details = []
    for raw in raw_ai_items:
        ai_act_id = f"ai_act_{uuid4().hex[:12]}"
        act_obj = ActivityItem(
            id=ai_act_id,
            title=raw["title"],
            content=raw["content"],
            category_tags=raw["category_tags"],
            section_title=raw.get("section_title"),
            created_at=raw["created_at"],
            engagement_metadata=raw["engagement_metadata"],
            is_ai_generated=True,
        )
        db.add(act_obj)

        joined_details.append(
            {
                "activity_item_id": ai_act_id,
                "relevance_score": raw["relevance_score"],
                "explanation_text": raw["explanation_text"],
                "rank_position": raw["rank_position"],
                "title": raw["title"],
                "content": raw["content"],
                "category_tags": raw["category_tags"],
                "section_title": raw.get("section_title"),
                "created_at": raw["created_at"],
            }
        )

    # 4. Generate summary prose and AI exploratory suggestions
    summary_prose = generate_digest_summary(
        user_name=user.name,
        ranked_items_with_details=joined_details,
        use_llm=True,
    )

    ai_suggestions = generate_ai_suggestions(
        user_name=user.name,
        interest_tags=user.interest_tags or [],
        use_llm=True,
    )

    # 5. Upsert Digest record per (user_id, week_identifier) with per-user scoped cleanup
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

        # Collect old DigestItem rows and exact ActivityItem IDs belonging STRICTLY to THIS user's previous digest
        old_ditems_res = await db.execute(
            select(DigestItem).where(DigestItem.digest_id == digest_obj.id)
        )
        old_ditems = old_ditems_res.scalars().all()
        old_user_act_ids = [
            di.activity_item_id
            for di in old_ditems
            if di.activity_item_id.startswith("ai_act_")
            or di.activity_item_id.startswith("boost_act_")
        ]

        # Delete old DigestItem records for THIS digest
        await db.execute(
            delete(DigestItem).where(DigestItem.digest_id == digest_obj.id)
        )

        # Delete ONLY the specific ActivityItem IDs belonging to THIS user's previous digest
        if old_user_act_ids:
            await db.execute(
                delete(ActivityItem).where(ActivityItem.id.in_(old_user_act_ids))
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

    # 6. Fetch existing feedback for user
    fb_result = await db.execute(
        select(ItemFeedback).where(ItemFeedback.user_id == user_id)
    )
    feedback_map = {
        fb.activity_item_id: fb.feedback_type for fb in fb_result.scalars().all()
    }

    # 7. Insert new DigestItem rows
    response_items = []
    for detail in joined_details:
        ditem_id = f"ditem_{digest_obj.id}_{detail['activity_item_id']}"
        ditem = DigestItem(
            id=ditem_id,
            digest_id=digest_obj.id,
            activity_item_id=detail["activity_item_id"],
            relevance_score=detail["relevance_score"],
            explanation_text=detail["explanation_text"],
            rank_position=detail["rank_position"],
        )
        db.add(ditem)

        response_items.append(
            DigestItemResponse(
                id=ditem_id,
                activity_item_id=detail["activity_item_id"],
                title=detail["title"],
                content=detail["content"],
                category_tags=detail["category_tags"],
                section_title=detail.get("section_title"),
                relevance_score=detail["relevance_score"],
                explanation_text=detail["explanation_text"],
                rank_position=detail["rank_position"],
                feedback_type=feedback_map.get(detail["activity_item_id"]),
                created_at=detail["created_at"],
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
        section_title = act.section_title if act else None
        response_items.append(
            DigestItemResponse(
                id=di.id,
                activity_item_id=di.activity_item_id,
                title=act.title if act else "Untitled",
                content=act.content if act else "",
                category_tags=act.category_tags if act else [],
                section_title=section_title,
                relevance_score=di.relevance_score,
                explanation_text=di.explanation_text,
                rank_position=di.rank_position,
                feedback_type=feedback_map.get(di.activity_item_id),
                created_at=act.created_at if act else None,
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


