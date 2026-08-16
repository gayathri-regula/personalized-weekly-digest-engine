"""FastAPI router for user activity history log endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.schemas.activity_log import ActivityLogListResponse, ActivityLogResponse

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get(
    "/{user_id}",
    response_model=ActivityLogListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_activity_log(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ActivityLogListResponse:
    """Retrieve chronologically ordered activity log history for a specific user."""
    # 1. Validate user existence
    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found.",
        )

    # 2. Query total count
    count_stmt = (
        select(func.count())
        .select_from(ActivityLog)
        .where(ActivityLog.user_id == user_id)
    )
    total_res = await db.execute(count_stmt)
    total_count = total_res.scalar() or 0

    # 3. Query paginated activity log entries ordered by created_at DESC
    stmt = (
        select(ActivityLog)
        .where(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(stmt)
    log_rows = res.scalars().all()

    items = [ActivityLogResponse.model_validate(row) for row in log_rows]

    return ActivityLogListResponse(items=items, total=total_count)
