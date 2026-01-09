"""Add profile activity fields

Revision ID: 20250109_000001
Revises: 20250103_000001
Create Date: 2025-01-09 00:00:01

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250109_000001'
down_revision = '20250103_000001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('profiles', sa.Column('telegram_username', sa.String(length=255), nullable=True))
    op.add_column('profiles', sa.Column('first_mini_app_at', sa.DateTime(), nullable=True))
    op.add_column('profiles', sa.Column('last_mini_app_at', sa.DateTime(), nullable=True))
    op.add_column('profiles', sa.Column('first_bot_start_at', sa.DateTime(), nullable=True))
    op.add_column('profiles', sa.Column('last_bot_start_at', sa.DateTime(), nullable=True))
    op.add_column('profiles', sa.Column('first_nutritionist_intent_at', sa.DateTime(), nullable=True))
    op.add_column('profiles', sa.Column('last_nutritionist_intent_at', sa.DateTime(), nullable=True))
    op.create_index('ix_profiles_telegram_username', 'profiles', ['telegram_username'])


def downgrade():
    op.drop_index('ix_profiles_telegram_username', table_name='profiles')
    op.drop_column('profiles', 'last_nutritionist_intent_at')
    op.drop_column('profiles', 'first_nutritionist_intent_at')
    op.drop_column('profiles', 'last_bot_start_at')
    op.drop_column('profiles', 'first_bot_start_at')
    op.drop_column('profiles', 'last_mini_app_at')
    op.drop_column('profiles', 'first_mini_app_at')
    op.drop_column('profiles', 'telegram_username')
