"""
Profile Model - Core user entity
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class Profile(db.Model):
    """
    Base profile for all users (clients, nutritionists, admins).
    Role determines access level and available features.
    """

    __tablename__ = "profiles"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = db.Column(
        db.String(20), nullable=False, default="client"
    )  # client/nutritionist/admin
    telegram_user_id = db.Column(db.BigInteger, unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    photo_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    nutritionist_profile = db.relationship(
        "NutritionistProfile",
        backref="profile",
        uselist=False,
        cascade="all, delete-orphan",
    )
    bookings_as_client = db.relationship(
        "Booking",
        foreign_keys="Booking.client_id",
        backref="client",
        lazy="dynamic",
    )
    intakes = db.relationship("Intake", backref="client", lazy="dynamic")
    policy_acknowledgements = db.relationship(
        "PolicyAcknowledgement", backref="user", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Profile {self.full_name} ({self.role})>"

    def to_dict(self):
        """Serialize profile to dictionary."""
        return {
            "id": str(self.id),
            "role": self.role,
            "telegram_user_id": self.telegram_user_id,
            "full_name": self.full_name,
            "photo_url": self.photo_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


