"""
User Session Model - Tracks individual login sessions and in-session actions.
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class UserSession(db.Model):
    """
    Represents a single login session for a profile.
    """

    __tablename__ = "user_sessions"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source = db.Column(db.String(32), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    booking_made = db.Column(db.Boolean, default=False, nullable=False)
    payment_made = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "profile_id": str(self.profile_id),
            "source": self.source,
            "started_at": self.started_at.isoformat(),
            "booking_made": self.booking_made,
            "payment_made": self.payment_made,
        }
