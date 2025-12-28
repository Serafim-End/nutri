"""Add client_filter_state table for persisting client search filters

Revision ID: 20241227_000002
Revises: 20241227_000001
Create Date: 2024-12-27 00:00:02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20241227_000002"
down_revision: Union[str, None] = "20241227_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create client_filter_state table
    op.create_table(
        "client_filter_states",
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "intake_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("intakes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("filters", postgresql.JSONB, nullable=False, default={}),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_client_filter_states_intake_id", "client_filter_states", ["intake_id"])


def downgrade() -> None:
    op.drop_table("client_filter_states")

