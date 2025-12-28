"""Add currency field to payments table

Revision ID: 20241228_000001
Revises: 20241227_000002_add_client_filter_state
Create Date: 2024-12-28 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20241228_000001'
down_revision = '20241227_000002_add_client_filter_state'
branch_labels = None
depends_on = None


def upgrade():
    """Add currency column to payments table."""
    # Add currency column with default value
    op.add_column(
        'payments',
        sa.Column('currency', sa.String(3), nullable=False, server_default='RUB')
    )
    
    # Remove server default after column is populated
    op.alter_column(
        'payments',
        'currency',
        server_default=None
    )


def downgrade():
    """Remove currency column from payments table."""
    op.drop_column('payments', 'currency')

