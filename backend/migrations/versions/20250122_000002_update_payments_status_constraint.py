"""Update payments status constraint

Revision ID: 20250122_000002
Revises: 20250122_000001
Create Date: 2025-01-22 00:00:02

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20250122_000002'
down_revision = '20250122_000001'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_payments_status", "payments")
    op.create_check_constraint(
        "ck_payments_status",
        "payments",
        "status IN ('created', 'succeeded', 'failed', 'refunded', 'expired')",
    )


def downgrade():
    op.drop_constraint("ck_payments_status", "payments")
    op.create_check_constraint(
        "ck_payments_status",
        "payments",
        "status IN ('created', 'succeeded', 'failed', 'refunded')",
    )
