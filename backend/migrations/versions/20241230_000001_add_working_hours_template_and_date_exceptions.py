"""Add working hours template and date exceptions

Revision ID: 20241230_000001
Revises: 20241229_000001_add_slot_source_and_updated_at
Create Date: 2024-12-30 00:00:01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241230_000001'
down_revision = '20241229_000001_add_slot_source_and_updated_at'
branch_labels = None
depends_on = None


def upgrade():
    # Create working_hours_templates table
    op.create_table(
        'working_hours_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'nutritionist_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('nutritionist_profiles.nutritionist_id', ondelete='CASCADE'),
            nullable=False,
            unique=True,
        ),
        sa.Column('weekly_schedule', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_working_hours_templates_nutritionist_id', 'working_hours_templates', ['nutritionist_id'])

    # Create date_exceptions table
    op.create_table(
        'date_exceptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'nutritionist_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('nutritionist_profiles.nutritionist_id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('exception_date', sa.Date(), nullable=False),
        sa.Column('exception_type', sa.String(20), nullable=False),
        sa.Column('custom_hours', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_date_exceptions_nutritionist_id', 'date_exceptions', ['nutritionist_id'])
    op.create_index('ix_date_exceptions_exception_date', 'date_exceptions', ['exception_date'])
    op.create_unique_constraint(
        'uq_nutritionist_date',
        'date_exceptions',
        ['nutritionist_id', 'exception_date']
    )


def downgrade():
    op.drop_table('date_exceptions')
    op.drop_table('working_hours_templates')
