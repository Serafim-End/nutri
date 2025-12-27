"""
Nutritionist Document Model - Document metadata for verification
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class NutritionistDocument(db.Model):
    """
    Metadata for documents uploaded by nutritionists for verification.
    Actual files are stored externally; this tracks file paths and review status.
    """

    __tablename__ = "nutritionist_documents"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nutritionist_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("nutritionist_profiles.nutritionist_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = db.Column(
        db.String(50), nullable=False
    )  # diploma/certificate/other
    file_path = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.String(20), nullable=False, default="uploaded"
    )  # uploaded/accepted/rejected
    review_note = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<NutritionistDocument {self.type} ({self.status})>"

    def to_dict(self):
        """Serialize document to dictionary."""
        return {
            "id": str(self.id),
            "nutritionist_id": str(self.nutritionist_id),
            "type": self.type,
            "file_path": self.file_path,
            "status": self.status,
            "review_note": self.review_note,
            "uploaded_at": self.uploaded_at.isoformat(),
        }


