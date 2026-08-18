"""FastAPI router for public shared digest retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.activity_item import ActivityItem
from app.models.digest import Digest
from app.models.digest_item import DigestItem
from app.models.user import User
from app.schemas.digest import (
    AISuggestion,
    SharedDigestItemResponse,
    SharedDigestResponse,
)

router = APIRouter(prefix="/share", tags=["share"])


@router.get("/{token}", response_model=SharedDigestResponse)
async def get_shared_digest(
    token: str, db: AsyncSession = Depends(get_db)
) -> SharedDigestResponse:
    """Public read-only endpoint to retrieve a user's latest digest by share token.

    Does not require user login or session. Leaks only public read-only content.
    """
    # 1. Lookup user by share_token
    user_stmt = select(User).where(User.share_token == token)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared digest link is invalid or expired.",
        )

    # 2. Lookup user's latest digest
    digest_stmt = (
        select(Digest)
        .where(Digest.user_id == user.id)
        .order_by(Digest.generated_at.desc())
    )
    digest_result = await db.execute(digest_stmt)
    digest_obj = digest_result.scalars().first()

    if digest_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No digest available for this shared link.",
        )

    # 3. Retrieve digest items
    items_stmt = (
        select(DigestItem)
        .where(DigestItem.digest_id == digest_obj.id)
        .order_by(DigestItem.rank_position.asc())
    )
    ditems_result = await db.execute(items_stmt)
    ditems = ditems_result.scalars().all()

    # 4. Fetch activity item details
    act_ids = [di.activity_item_id for di in ditems]
    if act_ids:
        act_result = await db.execute(
            select(ActivityItem).where(ActivityItem.id.in_(act_ids))
        )
        act_items = act_result.scalars().all()
        act_map = {ai.id: ai for ai in act_items}
    else:
        act_map = {}

    response_items = []
    for di in ditems:
        act = act_map.get(di.activity_item_id)
        response_items.append(
            SharedDigestItemResponse(
                id=di.id,
                activity_item_id=di.activity_item_id,
                title=act.title if act else "Untitled",
                content=act.content if act else "",
                category_tags=act.category_tags if act else [],
                section_title=act.section_title if act else None,
                relevance_score=di.relevance_score,
                explanation_text=di.explanation_text,
                rank_position=di.rank_position,
                created_at=act.created_at if act else None,
            )
        )

    return SharedDigestResponse(
        user_name=user.name,
        week_identifier=digest_obj.week_identifier,
        generated_at=digest_obj.generated_at,
        summary_prose=digest_obj.summary_prose,
        items=response_items,
        ai_suggestions=[AISuggestion(**s) for s in (digest_obj.ai_suggestions or [])],
    )
