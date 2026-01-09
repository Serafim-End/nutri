"""
Google Calendar Model - Stores OAuth tokens and selected calendar for nutritionists
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.extensions import db


class GoogleCalendar(db.Model):
    """
    Stores Google Calendar OAuth credentials and selected calendar for nutritionists.
    One record per nutritionist.
    """

    __tablename__ = "google_calendars"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nutritionist_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("nutritionist_profiles.nutritionist_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    # OAuth token data (encrypted in production)
    access_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    # Selected calendar ID
    selected_calendar_id = db.Column(db.String(255), nullable=True)
    selected_calendar_summary = db.Column(db.String(255), nullable=True)
    # Connection status
    is_connected = db.Column(db.Boolean, default=False, nullable=False)
    connected_at = db.Column(db.DateTime(timezone=True), nullable=True)
    disconnected_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship
    nutritionist = db.relationship(
        "NutritionistProfile",
        backref="google_calendar",
        uselist=False,
    )

    def __repr__(self):
        return f"<GoogleCalendar {self.nutritionist_id} (connected={self.is_connected})>"

    def to_dict(self):
        """Serialize Google Calendar connection to dictionary."""
        return {
            "id": str(self.id),
            "nutritionist_id": str(self.nutritionist_id),
            "is_connected": self.is_connected,
            "selected_calendar_id": self.selected_calendar_id,
            "selected_calendar_summary": self.selected_calendar_summary,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "disconnected_at": self.disconnected_at.isoformat() if self.disconnected_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
