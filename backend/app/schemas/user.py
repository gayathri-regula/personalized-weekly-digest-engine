"""Pydantic schemas for user endpoints and taxonomy."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    """Schema representing a platform user."""

    id: str = Field(..., description="User ID")
    name: str = Field(..., description="User full name")
    interest_tags: List[str] = Field(
        default_factory=list, description="User interest tags"
    )
    digest_frequency: str = Field(
        default="weekly", description="Digest frequency: 'daily', 'weekly', 'monthly'"
    )
    content_length: str = Field(
        default="detailed", description="Digest content length: 'brief', 'detailed'"
    )
    digest_language: str = Field(
        default="en", description="Digest language code: 'en'"
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
        description="List of 2 or more interest tags from taxonomy",
    )


class UserUpdateInterest(BaseModel):
    """Schema for updating a user's interest tags."""

    interest_tags: List[str] = Field(
        ...,
        min_length=2,
        description="Updated list of 2 or more interest tags from taxonomy",
    )


class UserUpdatePreferences(BaseModel):
    """Schema for updating a user's digest preferences."""

    digest_frequency: Optional[str] = Field(
        None, description="Digest frequency: 'daily', 'weekly', 'monthly'"
    )
    content_length: Optional[str] = Field(
        None, description="Digest content length: 'brief', 'detailed'"
    )
    digest_language: Optional[str] = Field(
        None, description="Digest language code: 'en'"
    )


class InterestsResponse(BaseModel):
    """Schema for returning domain interest taxonomy."""

    interests: List[str] = Field(..., description="Available taxonomy interest tags")
