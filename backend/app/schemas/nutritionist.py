"""
Nutritionist Schemas
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, timezone


class NutritionistUpsertRequest(BaseModel):
    """Request schema for creating/updating nutritionist profile."""

    telegram_user_id: int = Field(..., description="Telegram user ID")
    full_name: str = Field(..., min_length=1, max_length=255)
    photo_url: Optional[str] = None
    bio: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    specializations: List[str] = Field(default_factory=list)
    submit_for_verification: bool = Field(
        default=False, description="Set to true to submit for verification"
    )


class DocumentUploadRequest(BaseModel):
    """Request schema for document metadata upload."""

    type: str = Field(..., description="Document type: diploma/certificate/other")
    file_path: str = Field(..., description="URL or path to the uploaded file")


class ServiceCreateRequest(BaseModel):
    """Request schema for creating a service."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    duration_minutes: int = Field(..., ge=15, le=480)
    price_rub: int = Field(..., ge=0)
    is_active: bool = True


class SlotCreateRequest(BaseModel):
    """Request schema for creating a single availability slot."""

    start_at: datetime
    end_at: datetime

    @field_validator('start_at', 'end_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime string if needed."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v

    @field_validator('end_at')
    @classmethod
    def end_after_start(cls, v, info):
        """Ensure end_at is after start_at."""
        if 'start_at' in info.data and v <= info.data['start_at']:
            raise ValueError('end_at must be after start_at')
        return v

    @field_validator('start_at')
    @classmethod
    def start_in_future(cls, v):
        """Ensure slot starts in the future."""
        now = datetime.now(timezone.utc)
        # Make v timezone-aware if it isn't
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v <= now:
            raise ValueError('Слот должен быть в будущем')
        return v


class BulkSlotCreateRequest(BaseModel):
    """Request schema for bulk slot creation."""

    slots: List[SlotCreateRequest] = Field(..., min_length=1)


