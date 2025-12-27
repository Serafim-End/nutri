"""
Policy Acknowledgement Model - User consent tracking
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db


class PolicyAcknowledgement(db.Model):
    """
    Tracks user acknowledgements of policies and terms.
    Ensures compliance and consent tracking.
    """

    __tablename__ = "policies_acknowledgements"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    policy_code = db.Column(db.String(100), nullable=False)
    policy_version = db.Column(db.String(50), nullable=False)
    accepted_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Unique constraint: one acknowledgement per user per policy version
    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "policy_code", "policy_version", name="uq_user_policy_version"
        ),
    )

    def __repr__(self):
        return f"<PolicyAcknowledgement {self.policy_code} v{self.policy_version}>"

    def to_dict(self):
        """Serialize acknowledgement to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "policy_code": self.policy_code,
            "policy_version": self.policy_version,
            "accepted_at": self.accepted_at.isoformat(),
        }


