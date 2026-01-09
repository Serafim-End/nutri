"""
Nutritionist Schemas
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, date


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


class TimeRange(BaseModel):
    """Time range schema (e.g., {"start": "09:00", "end": "12:00"})."""

    start: str = Field(..., pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="Start time in HH:MM format")
    end: str = Field(..., pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", description="End time in HH:MM format")

    @field_validator('end')
    @classmethod
    def end_after_start(cls, v, info):
        """Ensure end time is after start time."""
        if 'start' in info.data:
            start_parts = info.data['start'].split(':')
            end_parts = v.split(':')
            start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
            end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
            if end_minutes <= start_minutes:
                raise ValueError('end time must be after start time')
        return v


class WorkingHoursTemplateUpdateRequest(BaseModel):
    """Request schema for creating/updating working hours template."""

    weekly_schedule: Dict[int, List[TimeRange]] = Field(
        ...,
        description="Weekly schedule: {0: [TimeRange, ...], 1: [...], ...} where 0=Monday, 6=Sunday"
    )

    @field_validator('weekly_schedule')
    @classmethod
    def validate_day_numbers(cls, v):
        """Ensure day numbers are 0-6 (Monday-Sunday)."""
        for day in v.keys():
            if day < 0 or day > 6:
                raise ValueError('Day numbers must be 0-6 (Monday=0, Sunday=6)')
        return v


class DateExceptionCreateRequest(BaseModel):
    """Request schema for creating a date exception."""

    exception_date: date = Field(..., description="Date for the exception")
    exception_type: str = Field(..., pattern="^(off|custom)$", description="Type: 'off' or 'custom'")
    custom_hours: Optional[List[TimeRange]] = Field(
        None,
        description="Custom hours for 'custom' type. Required if exception_type='custom', ignored if 'off'"
    )

    @field_validator('custom_hours')
    @classmethod
    def validate_custom_hours(cls, v, info):
        """Ensure custom_hours is provided for 'custom' type."""
        if 'exception_type' in info.data:
            if info.data['exception_type'] == 'custom' and (not v or len(v) == 0):
                raise ValueError('custom_hours is required when exception_type is "custom"')
        return v


class DateExceptionUpdateRequest(BaseModel):
    """Request schema for updating a date exception."""

    exception_type: str = Field(..., pattern="^(off|custom)$", description="Type: 'off' or 'custom'")
    custom_hours: Optional[List[TimeRange]] = Field(
        None,
        description="Custom hours for 'custom' type. Required if exception_type='custom', ignored if 'off'"
    )

    @field_validator('custom_hours')
    @classmethod
    def validate_custom_hours(cls, v, info):
        """Ensure custom_hours is provided for 'custom' type."""
        if 'exception_type' in info.data:
            if info.data['exception_type'] == 'custom' and (not v or len(v) == 0):
                raise ValueError('custom_hours is required when exception_type is "custom"')
        return v

