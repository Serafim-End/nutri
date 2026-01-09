"""
Date Exception Model - Exceptions to working hours template
"""

import uuid
from datetime import datetime, date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.extensions import db


class DateException(db.Model):
    """
    Date exceptions for nutritionist working hours.
    Overrides the weekly template for specific dates.
    
    Types:
    - "off": Day is completely off (no hours)
    - "custom": Custom hours for this date (stored in custom_hours)
    """

    __tablename__ = "date_exceptions"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nutritionist_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("nutritionist_profiles.nutritionist_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exception_date = db.Column(db.Date, nullable=False, index=True)
    exception_type = db.Column(
        db.String(20), nullable=False
    )  # "off" or "custom"
    # For "custom" type: [{"start": "09:00", "end": "12:00"}, ...]
    # For "off" type: null or []
    custom_hours = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    nutritionist = db.relationship("NutritionistProfile", backref="date_exceptions")

    __table_args__ = (
        db.UniqueConstraint("nutritionist_id", "exception_date", name="uq_nutritionist_date"),
    )

    def __repr__(self):
        return f"<DateException {self.nutritionist_id} {self.exception_date} ({self.exception_type})>"

    def to_dict(self):
        """Serialize exception to dictionary."""
        return {
            "id": str(self.id),
            "nutritionist_id": str(self.nutritionist_id),
            "exception_date": self.exception_date.isoformat(),
            "exception_type": self.exception_type,
            "custom_hours": self.custom_hours or [],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
