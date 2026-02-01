"""
Nutritionist Profile Model - Extended profile for nutritionists
"""

from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.extensions import db


class NutritionistProfile(db.Model):
    """
    Extended profile information for nutritionists.
    Contains verification status, specializations, and ratings.
    """

    __tablename__ = "nutritionist_profiles"

    nutritionist_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    bio = db.Column(db.Text, nullable=True)
    tags = db.Column(ARRAY(db.Text), default=list)
    specializations = db.Column(ARRAY(db.Text), default=list)
    verification_status = db.Column(
        db.String(20), nullable=False, default="draft"
    )  # draft/pending/approved/rejected/needs_update
    rating = db.Column(db.Numeric(3, 2), default=0.00)
    reviews_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    services = db.relationship(
        "Service", backref="nutritionist", lazy="dynamic", cascade="all, delete-orphan"
    )
    availability_slots = db.relationship(
        "AvailabilitySlot",
        backref="nutritionist",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    documents = db.relationship(
        "NutritionistDocument",
        backref="nutritionist",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    bookings = db.relationship(
        "Booking",
        foreign_keys="Booking.nutritionist_id",
        backref="nutritionist_profile",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<NutritionistProfile {self.nutritionist_id} ({self.verification_status})>"

    def to_dict(self, include_profile=True):
        """Serialize nutritionist profile to dictionary."""
        data = {
            "id": str(self.nutritionist_id),  # Add id alias for frontend compatibility
            "nutritionist_id": str(self.nutritionist_id),
            "bio": self.bio,
            "tags": self.tags or [],
            "specializations": self.specializations or [],
            "verification_status": self.verification_status,
            "rating": float(self.rating) if self.rating else 0.0,
            "reviews_count": self.reviews_count,
            "is_active": self.is_active,
            "is_blocked": self.is_blocked,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
        }
        if include_profile and self.profile:
            # Promote commonly used fields to root level for frontend convenience
            data["full_name"] = self.profile.full_name
            data["created_at"] = self.profile.created_at.isoformat()
            data["profile"] = self.profile.to_dict()
        return data

