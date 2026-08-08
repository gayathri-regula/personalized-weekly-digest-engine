"""Pydantic request and response schemas for feedback endpoints."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_FEEDBACK_TYPES = {"useful", "not_useful", "not_interested"}


class FeedbackRequest(BaseModel):
    """Schema for submitting item feedback."""

    feedback_type: str = Field(
        ...,
        description="Feedback type. Allowed values: useful, not_useful, not_interested",
    )

    @field_validator("feedback_type")
    @classmethod
    def validate_feedback_type(cls, value: str) -> str:
        if value not in ALLOWED_FEEDBACK_TYPES:
            raise ValueError(
                f"Invalid feedback_type '{value}'. Must be one of: {', '.join(sorted(ALLOWED_FEEDBACK_TYPES))}"
            )
        return value


class FeedbackResponse(BaseModel):
    """Schema representing stored feedback item response."""

    id: str = Field(..., description="Feedback record ID")
    user_id: str = Field(..., description="User ID who provided feedback")
    activity_item_id: str = Field(..., description="Activity item ID rated")
    feedback_type: str = Field(..., description="Feedback rating type")
    created_at: datetime = Field(..., description="Timestamp when feedback was submitted")

    model_config = ConfigDict(from_attributes=True)
