"""Update payments provider constraint

Revision ID: 20250122_000001
Revises: 20250111_000001
Create Date: 2025-01-22 00:00:01

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20250122_000001'
down_revision = '20250111_000001'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_payments_provider", "payments")
    op.create_check_constraint(
        "ck_payments_provider",
        "payments",
        "provider IN ('mock', 'prodamus', 'telegram', 'yookassa', 'cloudpayments', 'manual')",
    )


def downgrade():
    op.drop_constraint("ck_payments_provider", "payments")
    op.create_check_constraint(
        "ck_payments_provider",
        "payments",
        "provider IN ('telegram', 'yookassa', 'cloudpayments', 'manual')",
    )
