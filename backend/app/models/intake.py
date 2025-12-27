"""
Intake Model - Client intake questionnaire responses
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.extensions import db


class Intake(db.Model):
    """
    Client intake form submissions.
    Stores questionnaire answers used for matching with nutritionists.
    """

    __tablename__ = "intakes"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answers = db.Column(JSONB, nullable=False, default=dict)
    # Expected structure:
    # {
    #   "goals": ["weight_loss", "muscle_gain"],
    #   "dietary_restrictions": ["vegetarian", "gluten_free"],
    #   "budget_min": 1000,
    #   "budget_max": 5000,
    #   "preferred_schedule": "weekends",
    #   "health_conditions": ["diabetes"],
    #   "additional_notes": "..."
    # }
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Intake {self.id}>"

    def to_dict(self):
        """Serialize intake to dictionary."""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "answers": self.answers,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


