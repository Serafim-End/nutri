"""Add reviews table

Revision ID: 20250103_000001
Revises: 20250102_000001
Create Date: 2025-01-03 00:00:01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250103_000001'
down_revision = '20250102_000001'
branch_labels = None
depends_on = None


def upgrade():
    # Create reviews table
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'booking_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('bookings.id', ondelete='CASCADE'),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            'client_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('profiles.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column(
            'nutritionist_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('nutritionist_profiles.nutritionist_id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('is_hidden', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('ix_reviews_booking_id', 'reviews', ['booking_id'])
    op.create_index('ix_reviews_client_id', 'reviews', ['client_id'])
    op.create_index('ix_reviews_nutritionist_id', 'reviews', ['nutritionist_id'])
    op.create_index('ix_reviews_is_hidden', 'reviews', ['is_hidden'])


def downgrade():
    op.drop_index('ix_reviews_is_hidden', table_name='reviews')
    op.drop_index('ix_reviews_nutritionist_id', table_name='reviews')
    op.drop_index('ix_reviews_client_id', table_name='reviews')
    op.drop_index('ix_reviews_booking_id', table_name='reviews')
    op.drop_table('reviews')
