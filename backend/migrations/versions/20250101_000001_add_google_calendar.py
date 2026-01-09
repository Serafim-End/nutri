"""Add Google Calendar integration

Revision ID: 20250101_000001
Revises: 20241230_000001
Create Date: 2025-01-01 00:00:01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250101_000001'
down_revision = '20241230_000001'
branch_labels = None
depends_on = None


def upgrade():
    # Create google_calendars table
    op.create_table(
        'google_calendars',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'nutritionist_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('nutritionist_profiles.nutritionist_id', ondelete='CASCADE'),
            nullable=False,
            unique=True,
        ),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('selected_calendar_id', sa.String(255), nullable=True),
        sa.Column('selected_calendar_summary', sa.String(255), nullable=True),
        sa.Column('is_connected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('connected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disconnected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_google_calendars_nutritionist_id', 'google_calendars', ['nutritionist_id'])


def downgrade():
    op.drop_table('google_calendars')
