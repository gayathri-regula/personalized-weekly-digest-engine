"""FastAPI router for user endpoints."""

import secrets
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import INTEREST_TAXONOMY
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    ShareLinkResponse,
    UserCreate,
    UserResponse,
    UserUpdateInterest,
    UserUpdatePreferences,
    UsersListResponse,
)
from app.services.activity_logger import log_user_activity

router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_FREQUENCIES = {"daily", "weekly", "monthly"}
ALLOWED_CONTENT_LENGTHS = {"brief", "detailed"}
ALLOWED_LANGUAGES = {"en"}


def _build_user_response(user: User) -> UserResponse:
    """Helper to convert User ORM model to UserResponse schema with safe defaults."""
    return UserResponse(
        id=user.id,
        name=user.name,
        interest_tags=user.interest_tags or [],
        digest_frequency=user.digest_frequency or "weekly",
        content_length=user.content_length or "detailed",
        digest_language=user.digest_language or "en",
    )


@router.get("", response_model=UsersListResponse)
async def list_users(db: AsyncSession = Depends(get_db)) -> UsersListResponse:
    """Retrieve list of all platform users with their interest tags."""
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()

    user_responses = [_build_user_response(u) for u in users]

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
        digest_frequency="weekly",
        content_length="detailed",
        digest_language="en",
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return _build_user_response(new_user)


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

    return _build_user_response(user)


@router.patch("/{user_id}/preferences", response_model=UserResponse)
async def update_user_preferences(
    user_id: str,
    update_in: UserUpdatePreferences,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update an existing user's digest preferences (frequency, content length, language)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found.",
        )

    changes = []

    if update_in.digest_frequency is not None:
        freq = update_in.digest_frequency.strip().lower()
        if freq not in ALLOWED_FREQUENCIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid digest frequency '{update_in.digest_frequency}'. Must be one of: {sorted(ALLOWED_FREQUENCIES)}.",
            )
        user.digest_frequency = freq
        changes.append(f"frequency={freq}")

    if update_in.content_length is not None:
        length = update_in.content_length.strip().lower()
        if length not in ALLOWED_CONTENT_LENGTHS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid content length '{update_in.content_length}'. Must be one of: {sorted(ALLOWED_CONTENT_LENGTHS)}.",
            )
        user.content_length = length
        changes.append(f"content_length={length}")

    if update_in.digest_language is not None:
        lang = update_in.digest_language.strip().lower()
        if lang not in ALLOWED_LANGUAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid digest language '{update_in.digest_language}'. Must be one of: {sorted(ALLOWED_LANGUAGES)}.",
            )
        user.digest_language = lang
        changes.append(f"language={lang}")

    desc = f"Updated preferences: {', '.join(changes)}" if changes else "Updated digest preferences"

    await log_user_activity(
        db,
        user_id=user_id,
        event_type="preferences_updated",
        description=desc,
    )

    await db.commit()
    await db.refresh(user)

    return _build_user_response(user)


@router.post("/{user_id}/share", response_model=ShareLinkResponse)
async def generate_user_share_link(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ShareLinkResponse:
    """Generate (or retrieve existing) unique share token and public URL for a user's digest."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found.",
        )

    if not user.share_token:
        token = secrets.token_urlsafe(16)
        existing = await db.execute(select(User).where(User.share_token == token))
        while existing.scalar_one_or_none() is not None:
            token = secrets.token_urlsafe(16)
            existing = await db.execute(select(User).where(User.share_token == token))

        user.share_token = token
        await db.commit()
        await db.refresh(user)

    origin = request.headers.get("origin") or request.headers.get("referer")
    if origin:
        origin_clean = origin.rstrip("/")
        if "://" in origin_clean:
            parts = origin_clean.split("/")
            base = f"{parts[0]}//{parts[2]}"
        else:
            base = origin_clean
        share_url = f"{base}/share/{user.share_token}"
    else:
        share_url = f"http://localhost:5173/share/{user.share_token}"

    return ShareLinkResponse(
        share_token=user.share_token,
        share_url=share_url,
    )

