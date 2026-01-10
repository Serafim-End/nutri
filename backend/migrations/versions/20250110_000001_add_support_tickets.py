"""Add support tickets table

Revision ID: 20250110_000001
Revises: 20250109_000001
Create Date: 2025-01-10 00:00:01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20250110_000001'
down_revision = '20250109_000001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'support_tickets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'profile_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('profiles.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=True),
        sa.Column('author_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='client'),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column(
            'booking_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('bookings.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index('ix_support_tickets_profile_id', 'support_tickets', ['profile_id'])
    op.create_index('ix_support_tickets_telegram_user_id', 'support_tickets', ['telegram_user_id'])
    op.create_index('ix_support_tickets_booking_id', 'support_tickets', ['booking_id'])
    op.create_index('ix_support_tickets_status', 'support_tickets', ['status'])
    op.create_index('ix_support_tickets_created_at', 'support_tickets', ['created_at'])


def downgrade():
    op.drop_index('ix_support_tickets_created_at', table_name='support_tickets')
    op.drop_index('ix_support_tickets_status', table_name='support_tickets')
    op.drop_index('ix_support_tickets_booking_id', table_name='support_tickets')
    op.drop_index('ix_support_tickets_telegram_user_id', table_name='support_tickets')
    op.drop_index('ix_support_tickets_profile_id', table_name='support_tickets')
    op.drop_table('support_tickets')
