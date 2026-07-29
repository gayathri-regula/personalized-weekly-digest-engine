"""Pydantic response schemas for user endpoints."""

from typing import List
from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    """Schema representing a platform user."""

    id: str = Field(..., description="User ID")
    name: str = Field(..., description="User full name")
    interest_tags: List[str] = Field(
        default_factory=list, description="User interest tags"
    )

    model_config = ConfigDict(from_attributes=True)


class UsersListResponse(BaseModel):
    """Schema representing list of platform users."""

    users: List[UserResponse] = Field(
        default_factory=list, description="List of all users"
    )
