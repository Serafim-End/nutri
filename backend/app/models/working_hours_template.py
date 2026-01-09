"""
Working Hours Template Model - Weekly schedule template
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.extensions import db


class WorkingHoursTemplate(db.Model):
    """
    Weekly working hours template for nutritionists.
    Defines available hours for each day of the week (Monday=0, Sunday=6).
    Each day can have multiple time ranges (e.g., 09:00-12:00, 14:00-18:00).
    """

    __tablename__ = "working_hours_templates"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nutritionist_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("nutritionist_profiles.nutritionist_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    # Store weekly schedule as JSONB: {0: [{"start": "09:00", "end": "12:00"}, ...], 1: [...], ...}
    # 0 = Monday, 6 = Sunday
    weekly_schedule = db.Column(JSONB, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    nutritionist = db.relationship("NutritionistProfile", backref="working_hours_template")

    def __repr__(self):
        return f"<WorkingHoursTemplate {self.nutritionist_id}>"

    def to_dict(self):
        """Serialize template to dictionary."""
        return {
            "id": str(self.id),
            "nutritionist_id": str(self.nutritionist_id),
            "weekly_schedule": self.weekly_schedule or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
