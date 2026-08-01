"""Pydantic schemas for user endpoints and taxonomy."""

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


class UserCreate(BaseModel):
    """Schema for creating a new user profile."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User full name (1 to 100 characters)",
    )
    interest_tags: List[str] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="List of 2 to 4 interest tags from taxonomy",
    )


class InterestsResponse(BaseModel):
    """Schema for returning domain interest taxonomy."""

    interests: List[str] = Field(..., description="Available taxonomy interest tags")
