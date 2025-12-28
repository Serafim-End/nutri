"""
ClientFilterState Model - Persists client's current search filters
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.extensions import db


class ClientFilterState(db.Model):
    """
    Stores the current filter state for a client.
    Used to persist filters between sessions and allow editing.
    """

    __tablename__ = "client_filter_states"

    client_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    intake_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("intakes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filters = db.Column(JSONB, nullable=False, default=dict)
    # Expected structure:
    # {
    #   "goals": ["weight_loss", "muscle_gain"],
    #   "topics": ["nutrition_basics", "meal_planning"],
    #   "budget_max_rub": 5000,
    #   "dietary": ["vegetarian", "gluten_free"],
    #   "help_mode": "one_time" | "plan" | "long_term" | null,
    #   "specializations": [],
    #   "tags": []
    # }
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    intake = db.relationship("Intake", backref="filter_state", uselist=False)

    def __repr__(self):
        return f"<ClientFilterState {self.client_id}>"

    def to_dict(self):
        """Serialize filter state to dictionary."""
        return {
            "client_id": str(self.client_id),
            "intake_id": str(self.intake_id) if self.intake_id else None,
            "filters": self.filters,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

