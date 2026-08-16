"""FastAPI router for user endpoints."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import INTEREST_TAXONOMY
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdateInterest, UsersListResponse
from app.services.activity_logger import log_user_activity

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


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate, db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Create a new platform user with validated interest tags."""
    cleaned_name = user_in.name.strip()
    if not cleaned_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="User name cannot be empty or whitespace only.",
        )

    # Validate duplicate tags
    if len(user_in.interest_tags) != len(set(user_in.interest_tags)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate interest tags are not allowed.",
        )

    # Validate all tags against INTEREST_TAXONOMY
    for tag in user_in.interest_tags:
        if tag not in INTEREST_TAXONOMY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interest tag '{tag}'. Tag must be one of the supported taxonomy interests.",
            )

    # Generate unique ID: "user_" + first 8 characters of UUID4 hex
    user_id = f"user_{uuid.uuid4().hex[:8]}"

    # Verify ID collision (just in case)
    existing = await db.execute(select(User).where(User.id == user_id))
    while existing.scalar_one_or_none() is not None:
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        existing = await db.execute(select(User).where(User.id == user_id))

    new_user = User(
        id=user_id,
        name=cleaned_name,
        interest_tags=user_in.interest_tags,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        name=new_user.name,
        interest_tags=new_user.interest_tags,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_interests(
    user_id: str,
    update_in: UserUpdateInterest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update an existing user's interest tags."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found.",
        )

    # Validate duplicate tags
    if len(update_in.interest_tags) != len(set(update_in.interest_tags)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate interest tags are not allowed.",
        )

    # Validate all tags against INTEREST_TAXONOMY
    for tag in update_in.interest_tags:
        if tag not in INTEREST_TAXONOMY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interest tag '{tag}'. Tag must be one of the supported taxonomy interests.",
            )

    # Update ONLY interest_tags column
    user.interest_tags = update_in.interest_tags

    tags_str = ", ".join(update_in.interest_tags) if update_in.interest_tags else "None"
    await log_user_activity(
        db,
        user_id=user_id,
        event_type="interests_updated",
        description=f"Updated focus topics to: {tags_str}",
    )

    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        name=user.name,
        interest_tags=user.interest_tags,
    )
