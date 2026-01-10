"""Add is_problematic to reviews

Revision ID: 20250110_000002
Revises: 20250110_000001
Create Date: 2025-01-10 00:00:02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250110_000002'
down_revision = '20250110_000001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'reviews',
        sa.Column('is_problematic', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.create_index('ix_reviews_is_problematic', 'reviews', ['is_problematic'])


def downgrade():
    op.drop_index('ix_reviews_is_problematic', table_name='reviews')
    op.drop_column('reviews', 'is_problematic')
