"""
Nutritionist Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


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
    """Request schema for creating availability slots."""

    start_at: datetime
    end_at: datetime


class BulkSlotCreateRequest(BaseModel):
    """Request schema for bulk slot creation."""

    slots: List[SlotCreateRequest] = Field(..., min_length=1)


