"""
Review Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field, validator


class ReviewCreateRequest(BaseModel):
    """Request schema for creating a review."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(None, max_length=2000, description="Optional review comment (max 2000 chars)")

    @validator("comment")
    def validate_comment(cls, v):
        """Ensure comment is not empty if provided."""
        if v is not None and len(v.strip()) == 0:
            return None
        return v


class ReviewResponse(BaseModel):
    """Response schema for a review."""

    id: str
    booking_id: str
    client_id: Optional[str]
    nutritionist_id: str
    rating: int
    comment: Optional[str]
    is_hidden: bool
    created_at: str
    updated_at: str
    client: Optional[dict] = None
    booking: Optional[dict] = None
