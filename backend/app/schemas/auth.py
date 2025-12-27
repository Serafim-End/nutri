"""
Authentication Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional


class TelegramAuthRequest(BaseModel):
    """Request schema for Telegram authentication."""

    init_data: str = Field(..., description="Telegram Mini App initData string")


class AuthResponse(BaseModel):
    """Response schema for successful authentication."""

    access_token: str
    token_type: str = "bearer"
    profile: dict


class TelegramUser(BaseModel):
    """Telegram user data from initData."""

    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    language_code: Optional[str] = None


