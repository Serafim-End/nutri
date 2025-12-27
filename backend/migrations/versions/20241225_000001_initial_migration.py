"""Initial migration - Create all tables

Revision ID: 20241225_000001
Revises: 
Create Date: 2024-12-25 00:00:01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20241225_000001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create profiles table
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role", sa.String(20), nullable=False, default="client"),
        sa.Column("telegram_user_id", sa.BigInteger, unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("photo_url", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_profiles_telegram_user_id", "profiles", ["telegram_user_id"])

    # Create nutritionist_profiles table
    op.create_table(
        "nutritionist_profiles",
        sa.Column(
            "nutritionist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text), default=[]),
        sa.Column("specializations", postgresql.ARRAY(sa.Text), default=[]),
        sa.Column("verification_status", sa.String(20), nullable=False, default="draft"),
        sa.Column("rating", sa.Numeric(3, 2), default=0.00),
        sa.Column("reviews_count", sa.Integer, default=0),
        sa.Column("is_active", sa.Boolean, default=False),
        sa.Column("submitted_at", sa.DateTime, nullable=True),
        sa.Column("verified_at", sa.DateTime, nullable=True),
    )

    # Create services table
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "nutritionist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("nutritionist_profiles.nutritionist_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("duration_minutes", sa.Integer, nullable=False, default=60),
        sa.Column("price_rub", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_services_nutritionist_id", "services", ["nutritionist_id"])

    # Create availability_slots table
    op.create_table(
        "availability_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "nutritionist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("nutritionist_profiles.nutritionist_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="free"),
        sa.Column("hold_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_availability_slots_nutritionist_id", "availability_slots", ["nutritionist_id"])
    op.create_index("ix_availability_slots_start_at", "availability_slots", ["start_at"])

    # Create bookings table
    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "nutritionist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("nutritionist_profiles.nutritionist_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "service_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("services.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "slot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("availability_slots.id", ondelete="SET NULL"),
            nullable=True,
            unique=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, default="pending_payment"),
        sa.Column("price_rub", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, default="RUB"),
        sa.Column("meeting_link", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("paid_at", sa.DateTime, nullable=True),
        sa.Column("cancelled_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_bookings_client_id", "bookings", ["client_id"])
    op.create_index("ix_bookings_nutritionist_id", "bookings", ["nutritionist_id"])

    # Create payments table
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "booking_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bookings.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_payment_id", sa.Text, nullable=True),
        sa.Column("amount_rub", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="created"),
        sa.Column("raw_payload", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_payments_booking_id", "payments", ["booking_id"])

    # Create nutritionist_documents table
    op.create_table(
        "nutritionist_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "nutritionist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("nutritionist_profiles.nutritionist_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("file_path", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="uploaded"),
        sa.Column("review_note", sa.Text, nullable=True),
        sa.Column("uploaded_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_nutritionist_documents_nutritionist_id", "nutritionist_documents", ["nutritionist_id"])

    # Create policies_acknowledgements table
    op.create_table(
        "policies_acknowledgements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("policy_code", sa.String(100), nullable=False),
        sa.Column("policy_version", sa.String(50), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_policies_acknowledgements_user_id", "policies_acknowledgements", ["user_id"])
    op.create_unique_constraint(
        "uq_user_policy_version",
        "policies_acknowledgements",
        ["user_id", "policy_code", "policy_version"],
    )

    # Create intakes table
    op.create_table(
        "intakes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("answers", postgresql.JSONB, nullable=False, default={}),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_intakes_client_id", "intakes", ["client_id"])


def downgrade() -> None:
    op.drop_table("intakes")
    op.drop_table("policies_acknowledgements")
    op.drop_table("nutritionist_documents")
    op.drop_table("payments")
    op.drop_table("bookings")
    op.drop_table("availability_slots")
    op.drop_table("services")
    op.drop_table("nutritionist_profiles")
    op.drop_table("profiles")

