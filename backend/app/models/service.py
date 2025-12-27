"""
Service Model - Nutritionist services/offerings
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class Service(db.Model):
    """
    Services offered by nutritionists.
    Each nutritionist can have multiple services with different prices and durations.
    """

    __tablename__ = "services"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nutritionist_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("nutritionist_profiles.nutritionist_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    price_rub = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    bookings = db.relationship("Booking", backref="service", lazy="dynamic")

    def __repr__(self):
        return f"<Service {self.title} ({self.price_rub} RUB)>"

    def to_dict(self):
        """Serialize service to dictionary."""
        return {
            "id": str(self.id),
            "nutritionist_id": str(self.nutritionist_id),
            "title": self.title,
            "description": self.description,
            "duration_minutes": self.duration_minutes,
            "price_rub": self.price_rub,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


