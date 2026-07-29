"""FastAPI router for user endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UsersListResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UsersListResponse)
async def list_users(db: AsyncSession = Depends(get_db)) -> UsersListResponse:
    """Retrieve list of all platform users with their interest tags."""
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()

    user_responses = [
        UserResponse(
            id=u.id,
            name=u.name,
            interest_tags=u.interest_tags or [],
        )
        for u in users
    ]

    return UsersListResponse(users=user_responses)
