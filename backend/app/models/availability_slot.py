"""
Availability Slot Model - Time slots for bookings
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from app.utils.timezone import normalize_to_utc


class AvailabilitySlot(db.Model):
    """
    Time slots when nutritionists are available for consultations.
    Slots can be free, held (temporarily reserved), booked, or cancelled.
    
    source indicates how the slot was created:
    - manual: Created by nutritionist via bot (PRIMARY)
    - calendar: Imported from Google Calendar (OPTIONAL)
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
    source = db.Column(
        db.String(20), nullable=False, default="manual"
    )  # manual/calendar
    hold_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    booking = db.relationship("Booking", backref="slot", uselist=False)

    def __repr__(self):
        return f"<AvailabilitySlot {self.start_at} ({self.status})>"

    def to_dict(self):
        """Serialize slot to dictionary."""
        def isoformat_utc(value: Optional[datetime]) -> Optional[str]:
            if value is None:
                return None
            value = normalize_to_utc(value)
            return value.isoformat()

        return {
            "id": str(self.id),
            "nutritionist_id": str(self.nutritionist_id),
            "start_at": isoformat_utc(self.start_at),
            "end_at": isoformat_utc(self.end_at),
            "status": self.status,
            "source": self.source,
            "hold_expires_at": isoformat_utc(self.hold_expires_at),
            "created_at": isoformat_utc(self.created_at),
            "updated_at": isoformat_utc(self.updated_at),
        }
