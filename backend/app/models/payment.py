"""
Payment Model - Payment records for bookings
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.extensions import db


class Payment(db.Model):
    """
    Payment records linked to bookings.
    Supports multiple providers (Telegram, YooKassa, CloudPayments, manual).
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
    provider = db.Column(
        db.String(50), nullable=False
    )  # telegram/yookassa/cloudpayments/manual
    provider_payment_id = db.Column(db.Text, nullable=True)
    amount_rub = db.Column(db.Integer, nullable=False)
    status = db.Column(
        db.String(20), nullable=False, default="created"
    )  # created/succeeded/failed/refunded
    raw_payload = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Payment {self.id} ({self.status})>"

    def to_dict(self):
        """Serialize payment to dictionary."""
        return {
            "id": str(self.id),
            "booking_id": str(self.booking_id),
            "provider": self.provider,
            "provider_payment_id": self.provider_payment_id,
            "amount_rub": self.amount_rub,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


