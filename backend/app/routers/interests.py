"""FastAPI router for interest taxonomy endpoints."""

from fastapi import APIRouter
from app.constants import INTEREST_TAXONOMY
from app.schemas.user import InterestsResponse

router = APIRouter(prefix="/interests", tags=["interests"])


@router.get("", response_model=InterestsResponse)
async def get_interests() -> InterestsResponse:
    """Retrieve the full interest taxonomy list."""
    return InterestsResponse(interests=INTEREST_TAXONOMY)
