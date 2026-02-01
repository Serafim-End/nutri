"""Add is_blocked to nutritionist profiles

Revision ID: 20250122_000003
Revises: 20250122_000002
Create Date: 2025-01-22 00:00:03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250122_000003'
down_revision = '20250122_000002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'nutritionist_profiles',
        sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )


def downgrade():
    op.drop_column('nutritionist_profiles', 'is_blocked')
