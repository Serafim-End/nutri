"""
Support Ticket Model
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class SupportTicket(db.Model):
    """
    Support ticket submitted from bot or web app.
    """

    __tablename__ = "support_tickets"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    telegram_user_id = db.Column(db.BigInteger, nullable=True, index=True)
    author_name = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="client")
    text = db.Column(db.Text, nullable=False)
    booking_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = db.Column(db.String(20), nullable=False, default="open", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    profile = db.relationship("Profile", backref="support_tickets", lazy="joined")

    def __repr__(self):
        return f"<SupportTicket {self.id} ({self.status})>"

    def to_dict(self):
        """Serialize support ticket to dictionary."""
        author_id = (
            str(self.profile_id)
            if self.profile_id
            else (str(self.telegram_user_id) if self.telegram_user_id else "unknown")
        )
        author_name = self.author_name
        if not author_name and self.profile:
            author_name = self.profile.full_name
        telegram_user_id = self.telegram_user_id
        telegram_username = None
        if self.profile:
            telegram_user_id = self.profile.telegram_user_id
            telegram_username = self.profile.telegram_username
        elif self.telegram_user_id:
            telegram_user_id = self.telegram_user_id

        return {
            "id": str(self.id),
            "author_id": author_id,
            "author_name": author_name,
            "telegram_user_id": telegram_user_id,
            "telegram_username": telegram_username,
            "role": self.role,
            "text": self.text,
            "booking_id": str(self.booking_id) if self.booking_id else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
