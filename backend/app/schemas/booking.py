"""
Booking and Payment Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field


class BookingCreateRequest(BaseModel):
    """Request schema for creating a booking."""

    service_id: str = Field(..., description="UUID of the service to book")
    slot_id: str = Field(..., description="UUID of the availability slot")
    client_note: Optional[str] = Field(None, description="Optional note from client")


class PaymentCreateRequest(BaseModel):
    """Request schema for creating a payment intent."""

    booking_id: str = Field(..., description="UUID of the booking to pay for")


class PaymentWebhookRequest(BaseModel):
    """
    Request schema for legacy payment webhook.
    
    Note: The new webhook endpoint (/api/payments/webhook/{provider})
    doesn't require a specific schema as payload format varies by provider.
    """

    provider: str = Field(..., description="Payment provider: mock/telegram/yookassa/cloudpayments")
    payment_id: str = Field(..., description="Provider's payment ID")
    booking_id: str = Field(..., description="Our booking ID")
    amount_rub: int = Field(..., ge=0)
    status: str = Field(..., description="Payment status: succeeded/failed")
    signature: str = Field(..., description="Webhook signature for verification")


