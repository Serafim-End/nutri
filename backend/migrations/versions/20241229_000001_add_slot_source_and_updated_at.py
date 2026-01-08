"""Add source and updated_at to availability_slots

Revision ID: 20241229_000001
Revises: 20241228_000001_add_currency_to_payments
Create Date: 2024-12-29 00:00:01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20241229_000001'
down_revision = '20241228_000001_add_currency_to_payments'
branch_labels = None
depends_on = None


def upgrade():
    # Add source column with default 'manual'
    op.add_column(
        'availability_slots',
        sa.Column('source', sa.String(20), nullable=False, server_default='manual')
    )
    
    # Add updated_at column
    op.add_column(
        'availability_slots',
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )
    
    # Set updated_at to created_at for existing rows
    op.execute("UPDATE availability_slots SET updated_at = created_at WHERE updated_at IS NULL")
    
    # Make updated_at not nullable after populating
    op.alter_column('availability_slots', 'updated_at', nullable=False)


def downgrade():
    op.drop_column('availability_slots', 'updated_at')
    op.drop_column('availability_slots', 'source')
