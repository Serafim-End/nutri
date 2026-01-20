"""Add user_sessions table

Revision ID: 20250111_000001
Revises: 20250110_000002
Create Date: 2025-01-11 00:00:01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20250111_000001'
down_revision = '20250110_000002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source', sa.String(length=32), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('booking_made', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('payment_made', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_user_sessions_profile_id', 'user_sessions', ['profile_id'])
    op.create_index('ix_user_sessions_started_at', 'user_sessions', ['started_at'])


def downgrade():
    op.drop_index('ix_user_sessions_started_at', table_name='user_sessions')
    op.drop_index('ix_user_sessions_profile_id', table_name='user_sessions')
    op.drop_table('user_sessions')
