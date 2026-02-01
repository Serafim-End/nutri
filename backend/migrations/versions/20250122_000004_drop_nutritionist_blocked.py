"""Drop is_blocked from nutritionist profiles

Revision ID: 20250122_000004
Revises: 20250122_000003
Create Date: 2025-01-22 00:00:04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250122_000004'
down_revision = '20250122_000003'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE nutritionist_profiles DROP COLUMN IF EXISTS is_blocked")


def downgrade():
    op.add_column(
        'nutritionist_profiles',
        sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )
