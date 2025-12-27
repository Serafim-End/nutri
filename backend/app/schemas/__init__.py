"""
Pydantic Schemas for Request/Response Validation
"""

from app.schemas.auth import TelegramAuthRequest, AuthResponse
from app.schemas.nutritionist import (
    NutritionistUpsertRequest,
    DocumentUploadRequest,
    ServiceCreateRequest,
    SlotCreateRequest,
)
from app.schemas.client import IntakeCreateRequest, MatchQuery
from app.schemas.booking import BookingCreateRequest

__all__ = [
    "TelegramAuthRequest",
    "AuthResponse",
    "NutritionistUpsertRequest",
    "DocumentUploadRequest",
    "ServiceCreateRequest",
    "SlotCreateRequest",
    "IntakeCreateRequest",
    "MatchQuery",
    "BookingCreateRequest",
]


