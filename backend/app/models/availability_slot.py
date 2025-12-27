"""
Availability Slot Model - Time slots for bookings
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class AvailabilitySlot(db.Model):
    """
    Time slots when nutritionists are available for consultations.
    Slots can be free, held (temporarily reserved), booked, or cancelled.
    """

    __tablename__ = "availability_slots"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nutritionist_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("nutritionist_profiles.nutritionist_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    end_at = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(
        db.String(20), nullable=False, default="free"
    )  # free/held/booked/cancelled
    hold_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    booking = db.relationship("Booking", backref="slot", uselist=False)

    def __repr__(self):
        return f"<AvailabilitySlot {self.start_at} ({self.status})>"

    def to_dict(self):
        """Serialize slot to dictionary."""
        return {
            "id": str(self.id),
            "nutritionist_id": str(self.nutritionist_id),
            "start_at": self.start_at.isoformat(),
            "end_at": self.end_at.isoformat(),
            "status": self.status,
            "hold_expires_at": (
                self.hold_expires_at.isoformat() if self.hold_expires_at else None
            ),
            "created_at": self.created_at.isoformat(),
        }


