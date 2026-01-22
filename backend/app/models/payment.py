"""
Payment Model - Payment records for bookings

Supports the unified payment lifecycle:
    created -> succeeded | failed | expired -> refunded

Provider field allows multiple payment integrations:
    - mock: Development/testing provider
    - prodamus: Prodamus Payform
    - telegram: Telegram Payments (Stars)
    - yookassa: YooKassa payment gateway
    - cloudpayments: CloudPayments gateway
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.extensions import db


class Payment(db.Model):
    """
    Payment records linked to bookings.
    
    Lifecycle:
        1. Payment created with status='created' when booking enters pending_payment
        2. Payment intent sent to provider (URL returned to client)
        3. Webhook received -> status='succeeded' or 'failed'
        4. On success: booking -> paid, slot -> booked
        5. On refund: status='refunded'
    
    Supports multiple providers (mock, prodamus, telegram, yookassa, cloudpayments).
    """

    __tablename__ = "payments"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    
    # Provider information
    provider = db.Column(
        db.String(50), nullable=False
    )  # mock/prodamus/telegram/yookassa/cloudpayments
    provider_payment_id = db.Column(db.Text, nullable=True)  # External payment ID
    
    # Payment details
    amount_rub = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="RUB")
    
    # Status tracking
    status = db.Column(
        db.String(20), nullable=False, default="created"
    )  # created/succeeded/failed/refunded/expired
    
    # Audit data
    raw_payload = db.Column(JSONB, nullable=True)  # Webhook payload for debugging
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Payment {self.id} ({self.provider}:{self.status})>"

    def to_dict(self):
        """Serialize payment to dictionary."""
        return {
            "id": str(self.id),
            "booking_id": str(self.booking_id),
            "provider": self.provider,
            "provider_payment_id": self.provider_payment_id,
            "amount_rub": self.amount_rub,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @property
    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == "succeeded"
    
    @property
    def is_pending(self) -> bool:
        """Check if payment is pending (created, not yet processed)."""
        return self.status == "created"

