"""Add google_calendar_event_id to bookings

Revision ID: 20250102_000001
Revises: 20250101_000001
Create Date: 2025-01-02 00:00:01

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250102_000001'
down_revision = '20250101_000001'
branch_labels = None
depends_on = None


def upgrade():
    # Add google_calendar_event_id column to bookings table
    op.add_column(
        'bookings',
        sa.Column('google_calendar_event_id', sa.String(255), nullable=True)
    )
    op.create_index(
        'ix_bookings_google_calendar_event_id',
        'bookings',
        ['google_calendar_event_id']
    )


def downgrade():
    op.drop_index('ix_bookings_google_calendar_event_id', table_name='bookings')
    op.drop_column('bookings', 'google_calendar_event_id')
