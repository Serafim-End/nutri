"""
Booking Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field


class BookingCreateRequest(BaseModel):
    """Request schema for creating a booking."""

    service_id: str = Field(..., description="UUID of the service to book")
    slot_id: str = Field(..., description="UUID of the availability slot")
    client_note: Optional[str] = Field(None, description="Optional note from client")


class PaymentWebhookRequest(BaseModel):
    """Request schema for payment webhook."""

    provider: str = Field(..., description="Payment provider: telegram/yookassa/cloudpayments")
    payment_id: str = Field(..., description="Provider's payment ID")
    booking_id: str = Field(..., description="Our booking ID")
    amount_rub: int = Field(..., ge=0)
    status: str = Field(..., description="Payment status: succeeded/failed")
    signature: str = Field(..., description="Webhook signature for verification")


