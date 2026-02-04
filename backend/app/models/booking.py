"""
Booking Model - Consultation bookings
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class Booking(db.Model):
    """
    Booking records for client-nutritionist consultations.
    Tracks the full lifecycle from creation through payment and completion.
    """

    __tablename__ = "bookings"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    nutritionist_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("nutritionist_profiles.nutritionist_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    service_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("services.id", ondelete="SET NULL"),
        nullable=True,
    )
    slot_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("availability_slots.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    status = db.Column(
        db.String(20), nullable=False, default="pending_payment"
    )  # pending_payment/paid/cancelled/completed/no_show/refunded
    price_rub = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="RUB")
    meeting_link = db.Column(db.Text, nullable=True)
    google_calendar_event_id = db.Column(db.String(255), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    paid_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    payment = db.relationship(
        "Payment", backref="booking", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Booking {self.id} ({self.status})>"

    def to_dict(self, include_relations=False):
        """Serialize booking to dictionary."""
        data = {
            "id": str(self.id),
            "client_id": str(self.client_id) if self.client_id else None,
            "nutritionist_id": str(self.nutritionist_id) if self.nutritionist_id else None,
            "service_id": str(self.service_id) if self.service_id else None,
            "slot_id": str(self.slot_id) if self.slot_id else None,
            "status": self.status,
            "price_rub": self.price_rub,
            "currency": self.currency,
            "meeting_link": self.meeting_link,
            "created_at": self.created_at.isoformat(),
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "has_review": self.review is not None,
        }
        if include_relations:
            if self.service:
                data["service"] = self.service.to_dict()
            if self.slot:
                data["slot"] = self.slot.to_dict()
            # Include nutritionist profile info
            if self.nutritionist_profile:
                data["nutritionist"] = self.nutritionist_profile.to_dict(include_profile=True)
        return data

