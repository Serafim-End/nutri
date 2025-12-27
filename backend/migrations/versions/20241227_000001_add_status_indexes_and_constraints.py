"""Add status indexes and CHECK constraints

Revision ID: 20241227_000001
Revises: 20241225_000001
Create Date: 2024-12-27 00:00:01

This migration adds:
- Indexes on status columns for faster filtering
- Indexes on created_at columns for time-based queries
- CHECK constraints for enum-like status fields
- Composite indexes for common query patterns
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20241227_000001"
down_revision: Union[str, None] = "20241225_000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========================================
    # INDEXES ON STATUS COLUMNS
    # ========================================
    
    # profiles.role index
    op.create_index(
        "ix_profiles_role",
        "profiles",
        ["role"],
    )
    
    # nutritionist_profiles.verification_status index
    op.create_index(
        "ix_nutritionist_profiles_verification_status",
        "nutritionist_profiles",
        ["verification_status"],
    )
    
    # nutritionist_profiles.is_active index
    op.create_index(
        "ix_nutritionist_profiles_is_active",
        "nutritionist_profiles",
        ["is_active"],
    )
    
    # Composite index for approved & active nutritionists (common query)
    op.create_index(
        "ix_nutritionist_profiles_approved_active",
        "nutritionist_profiles",
        ["verification_status", "is_active"],
    )
    
    # availability_slots.status index
    op.create_index(
        "ix_availability_slots_status",
        "availability_slots",
        ["status"],
    )
    
    # Composite index for available slots query (nutritionist + status + time)
    op.create_index(
        "ix_availability_slots_nutritionist_status_time",
        "availability_slots",
        ["nutritionist_id", "status", "start_at"],
    )
    
    # bookings.status index
    op.create_index(
        "ix_bookings_status",
        "bookings",
        ["status"],
    )
    
    # Composite index for client bookings by status
    op.create_index(
        "ix_bookings_client_status",
        "bookings",
        ["client_id", "status"],
    )
    
    # payments.status index
    op.create_index(
        "ix_payments_status",
        "payments",
        ["status"],
    )
    
    # nutritionist_documents.status index
    op.create_index(
        "ix_nutritionist_documents_status",
        "nutritionist_documents",
        ["status"],
    )
    
    # ========================================
    # INDEXES ON TIMESTAMP COLUMNS
    # ========================================
    
    # profiles.created_at for sorting/filtering
    op.create_index(
        "ix_profiles_created_at",
        "profiles",
        ["created_at"],
    )
    
    # bookings.created_at for time-based queries
    op.create_index(
        "ix_bookings_created_at",
        "bookings",
        ["created_at"],
    )
    
    # payments.created_at for reporting
    op.create_index(
        "ix_payments_created_at",
        "payments",
        ["created_at"],
    )
    
    # intakes.created_at for sorting
    op.create_index(
        "ix_intakes_created_at",
        "intakes",
        ["created_at"],
    )
    
    # ========================================
    # CHECK CONSTRAINTS FOR ENUM-LIKE FIELDS
    # ========================================
    
    # profiles.role CHECK constraint
    op.create_check_constraint(
        "ck_profiles_role",
        "profiles",
        "role IN ('client', 'nutritionist', 'admin')",
    )
    
    # nutritionist_profiles.verification_status CHECK constraint
    op.create_check_constraint(
        "ck_nutritionist_profiles_verification_status",
        "nutritionist_profiles",
        "verification_status IN ('draft', 'pending', 'approved', 'rejected', 'needs_update')",
    )
    
    # availability_slots.status CHECK constraint
    op.create_check_constraint(
        "ck_availability_slots_status",
        "availability_slots",
        "status IN ('free', 'held', 'booked', 'cancelled')",
    )
    
    # bookings.status CHECK constraint
    op.create_check_constraint(
        "ck_bookings_status",
        "bookings",
        "status IN ('pending_payment', 'paid', 'cancelled', 'completed', 'no_show', 'refunded')",
    )
    
    # bookings.currency CHECK constraint
    op.create_check_constraint(
        "ck_bookings_currency",
        "bookings",
        "currency IN ('RUB', 'USD', 'EUR')",
    )
    
    # payments.status CHECK constraint
    op.create_check_constraint(
        "ck_payments_status",
        "payments",
        "status IN ('created', 'succeeded', 'failed', 'refunded')",
    )
    
    # payments.provider CHECK constraint
    op.create_check_constraint(
        "ck_payments_provider",
        "payments",
        "provider IN ('telegram', 'yookassa', 'cloudpayments', 'manual')",
    )
    
    # nutritionist_documents.type CHECK constraint
    op.create_check_constraint(
        "ck_nutritionist_documents_type",
        "nutritionist_documents",
        "type IN ('diploma', 'certificate', 'license', 'other')",
    )
    
    # nutritionist_documents.status CHECK constraint
    op.create_check_constraint(
        "ck_nutritionist_documents_status",
        "nutritionist_documents",
        "status IN ('uploaded', 'accepted', 'rejected')",
    )


def downgrade() -> None:
    # Drop CHECK constraints
    op.drop_constraint("ck_nutritionist_documents_status", "nutritionist_documents")
    op.drop_constraint("ck_nutritionist_documents_type", "nutritionist_documents")
    op.drop_constraint("ck_payments_provider", "payments")
    op.drop_constraint("ck_payments_status", "payments")
    op.drop_constraint("ck_bookings_currency", "bookings")
    op.drop_constraint("ck_bookings_status", "bookings")
    op.drop_constraint("ck_availability_slots_status", "availability_slots")
    op.drop_constraint("ck_nutritionist_profiles_verification_status", "nutritionist_profiles")
    op.drop_constraint("ck_profiles_role", "profiles")
    
    # Drop timestamp indexes
    op.drop_index("ix_intakes_created_at", "intakes")
    op.drop_index("ix_payments_created_at", "payments")
    op.drop_index("ix_bookings_created_at", "bookings")
    op.drop_index("ix_profiles_created_at", "profiles")
    
    # Drop status indexes
    op.drop_index("ix_nutritionist_documents_status", "nutritionist_documents")
    op.drop_index("ix_payments_status", "payments")
    op.drop_index("ix_bookings_client_status", "bookings")
    op.drop_index("ix_bookings_status", "bookings")
    op.drop_index("ix_availability_slots_nutritionist_status_time", "availability_slots")
    op.drop_index("ix_availability_slots_status", "availability_slots")
    op.drop_index("ix_nutritionist_profiles_approved_active", "nutritionist_profiles")
    op.drop_index("ix_nutritionist_profiles_is_active", "nutritionist_profiles")
    op.drop_index("ix_nutritionist_profiles_verification_status", "nutritionist_profiles")
    op.drop_index("ix_profiles_role", "profiles")

