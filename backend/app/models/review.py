"""
Review Model - Client reviews for completed bookings
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class Review(db.Model):
    """
    Reviews left by clients for completed bookings.
    Reviews can be hidden by admins but not deleted (soft delete via is_hidden flag).
    """

    __tablename__ = "reviews"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    client_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    nutritionist_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("nutritionist_profiles.nutritionist_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    is_hidden = db.Column(db.Boolean, nullable=False, default=False, index=True)
    is_problematic = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    booking = db.relationship("Booking", backref="review", uselist=False)
    client = db.relationship("Profile", foreign_keys=[client_id], backref="reviews")
    nutritionist_profile = db.relationship(
        "NutritionistProfile",
        foreign_keys=[nutritionist_id],
        backref="reviews",
    )

    def __repr__(self):
        return f"<Review {self.id} ({self.rating}★) - {self.booking_id}>"

    def to_dict(self, include_relations=False):
        """Serialize review to dictionary."""
        data = {
            "id": str(self.id),
            "booking_id": str(self.booking_id),
            "client_id": str(self.client_id) if self.client_id else None,
            "nutritionist_id": str(self.nutritionist_id),
            "rating": self.rating,
            "comment": self.comment,
            "text": self.comment,
            "is_hidden": self.is_hidden,
            "is_problematic": self.is_problematic,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_relations:
            if self.client:
                data["client"] = {
                    "id": str(self.client.id),
                    "full_name": self.client.full_name,
                    "photo_url": self.client.photo_url,
                }
                data["client_name"] = self.client.full_name
            else:
                data["client_name"] = None
            if self.booking:
                data["booking"] = {
                    "id": str(self.booking.id),
                    "status": self.booking.status,
                    "created_at": self.booking.created_at.isoformat(),
                }
            if self.nutritionist_profile and self.nutritionist_profile.profile:
                data["nutritionist_name"] = self.nutritionist_profile.profile.full_name
            else:
                data["nutritionist_name"] = None
        return data
