"""
Booking Hold Service
Manages slot holds and releases expired holds with race-condition safety.
Uses row-level locks (SELECT FOR UPDATE) for atomic operations.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.extensions import db
from app.models import AvailabilitySlot, Booking, Payment, Service
from app.services.notifications import NotificationService
from app.services.booking_calendar_sync import BookingCalendarSync
from app.utils.timezone import normalize_to_utc


logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class BookingHoldService:
    """
    Service for managing booking holds.
    Implements 10-minute hold window for payment processing.
    All operations are atomic and race-condition safe.
    """

    # Valid slot state transitions
    SLOT_TRANSITIONS = {
        "free": ["held"],
        "held": ["booked", "free"],
        "booked": ["cancelled"],  # admin only
        "cancelled": [],
    }

    # Valid booking state transitions
    BOOKING_TRANSITIONS = {
        "pending_payment": ["paid", "cancelled"],
        "paid": ["completed", "refunded"],
        "cancelled": [],
        "completed": [],
        "refunded": [],
        "no_show": [],
    }

    @classmethod
    def _can_transition_slot(cls, from_status: str, to_status: str) -> bool:
        """Check if slot transition is valid."""
        return to_status in cls.SLOT_TRANSITIONS.get(from_status, [])

    @classmethod
    def _can_transition_booking(cls, from_status: str, to_status: str) -> bool:
        """Check if booking transition is valid."""
        return to_status in cls.BOOKING_TRANSITIONS.get(from_status, [])

    @staticmethod
    def create_booking_with_hold(
        client_id: str,
        service_id: str,
        slot_id: str,
        client_note: Optional[str] = None,
    ) -> Tuple[Optional[Booking], Optional[str]]:
        """
        Create a booking and hold the slot for payment.
        Uses SELECT FOR UPDATE to prevent race conditions.

        Args:
            client_id: UUID of the client
            service_id: UUID of the service
            slot_id: UUID of the availability slot
            client_note: Optional note from client

        Returns:
            Tuple of (booking or None, error message or None)
        """
        hold_minutes = current_app.config.get("BOOKING_HOLD_MINUTES", 10)
        now = utc_now()

        try:
            # Start transaction
            # Verify service exists and is active
            service = Service.query.get(service_id)
            if not service or not service.is_active:
                return None, "Service not found or inactive"

            # Lock the slot row for update (prevents concurrent modifications)
            slot = db.session.query(AvailabilitySlot).filter(
                AvailabilitySlot.id == slot_id
            ).with_for_update(nowait=True).first()

            if not slot:
                return None, "Slot not found"

            if slot.status != "free":
                logger.info(f"Slot {slot_id} not available, status={slot.status}")
                return None, "Slot is not available (already held or booked)"

            # Verify slot belongs to the service's nutritionist
            if str(slot.nutritionist_id) != str(service.nutritionist_id):
                return None, "Slot does not belong to this nutritionist"

            # Check if slot is in the future
            slot_start = slot.start_at
            slot_start = normalize_to_utc(slot_start)
            if slot_start <= now:
                return None, "Cannot book a slot in the past"

            # Transition slot to held state
            if not BookingHoldService._can_transition_slot("free", "held"):
                return None, "Invalid slot state transition"

            slot.status = "held"
            slot.hold_expires_at = now + timedelta(minutes=hold_minutes)

            # Create booking
            booking = Booking(
                client_id=client_id,
                nutritionist_id=service.nutritionist_id,
                service_id=service_id,
                slot_id=slot_id,
                status="pending_payment",
                price_rub=service.price_rub,
                currency="RUB",
            )

            db.session.add(booking)
            db.session.commit()

            logger.info(
                f"Booking created: id={booking.id}, slot={slot_id}, "
                f"hold_expires_at={slot.hold_expires_at.isoformat()}"
            )

            # Send notification (async/non-blocking in production)
            try:
                NotificationService.booking_created(booking)
            except Exception as e:
                logger.warning(f"Failed to send booking notification: {e}")

            return booking, None

        except OperationalError as e:
            db.session.rollback()
            # Lock acquisition failed - slot is being modified by another transaction
            if "could not obtain lock" in str(e) or "LockNotAvailable" in str(e):
                logger.warning(f"Slot {slot_id} locked by concurrent transaction")
                return None, "Slot is currently being booked by another user"
            logger.error(f"Database error creating booking: {e}")
            return None, "Failed to create booking"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating booking: {e}")
            return None, "Failed to create booking"

    @staticmethod
    def release_expired_holds() -> int:
        """
        Release all expired slot holds and cancel associated bookings.
        This is designed to be called by a cron job.
        Idempotent and safe for concurrent execution.

        Returns:
            Number of slots released
        """
        now = utc_now()
        released_count = 0

        try:
            # Find expired held slots with lock
            expired_slots = db.session.query(AvailabilitySlot).filter(
                AvailabilitySlot.status == "held",
                AvailabilitySlot.hold_expires_at <= now,
            ).with_for_update(skip_locked=True).all()

            for slot in expired_slots:
                try:
                    # Find and cancel associated pending booking
                    booking = Booking.query.filter(
                        Booking.slot_id == slot.id,
                        Booking.status == "pending_payment",
                    ).first()

                    if booking:
                        booking.status = "cancelled"
                        booking.cancelled_at = now
                        logger.info(
                            f"Booking cancelled due to hold expiry: id={booking.id}"
                        )
                        payment = Payment.query.filter_by(booking_id=booking.id).first()
                        if payment and payment.status == "created":
                            payment.status = "expired"
                        try:
                            NotificationService.booking_cancelled(booking, "Payment timeout")
                        except Exception as e:
                            logger.warning(f"Failed to send cancellation notification: {e}")
                        
                        # Sync to Google Calendar (non-blocking, idempotent)
                        try:
                            BookingCalendarSync.sync_booking_cancelled(booking)
                        except Exception as e:
                            logger.warning(f"Failed to sync booking cancellation to calendar: {e}")

                    # Release the slot
                    slot.status = "free"
                    slot.hold_expires_at = None

                    logger.info(f"Slot released from expired hold: id={slot.id}")
                    released_count += 1

                except Exception as e:
                    logger.error(f"Error releasing slot {slot.id}: {e}")
                    continue

            if released_count > 0:
                db.session.commit()
                logger.info(f"Released {released_count} expired holds")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in release_expired_holds: {e}")

        return released_count

    @staticmethod
    def cancel_booking(
        booking_id: str, user_id: str, reason: str = None
    ) -> Tuple[Optional[Booking], Optional[str]]:
        """
        Cancel a booking and release the slot.
        Only pending_payment bookings can be cancelled by clients.

        Args:
            booking_id: UUID of the booking
            user_id: UUID of the user cancelling
            reason: Optional cancellation reason

        Returns:
            Tuple of (booking or None, error message or None)
        """
        now = utc_now()

        try:
            # Lock booking row
            booking = db.session.query(Booking).filter(
                Booking.id == booking_id
            ).with_for_update(nowait=True).first()

            if not booking:
                return None, "Booking not found"

            # Verify ownership
            if str(booking.client_id) != user_id:
                return None, "Not authorized to cancel this booking"

            # Check if already cancelled or completed
            if booking.status in ("cancelled", "completed", "refunded"):
                return None, f"Booking already {booking.status}"

            # Only allow cancellation of pending_payment bookings by clients
            if booking.status == "paid":
                return None, "Cannot cancel a paid booking. Please contact support for refunds."

            # Validate transition
            if not BookingHoldService._can_transition_booking(booking.status, "cancelled"):
                return None, f"Cannot cancel booking with status {booking.status}"

            # Lock and release the slot
            slot = db.session.query(AvailabilitySlot).filter(
                AvailabilitySlot.id == booking.slot_id
            ).with_for_update(nowait=True).first()

            if slot and slot.status == "held":
                if BookingHoldService._can_transition_slot("held", "free"):
                    slot.status = "free"
                    slot.hold_expires_at = None
                    logger.info(f"Slot released due to booking cancellation: id={slot.id}")

            # Cancel booking
            booking.status = "cancelled"
            booking.cancelled_at = now

            db.session.commit()

            logger.info(
                f"Booking cancelled: id={booking.id}, reason={reason or 'not specified'}"
            )

            # Send notification
            try:
                NotificationService.booking_cancelled(booking, reason)
            except Exception as e:
                logger.warning(f"Failed to send cancellation notification: {e}")

            # Sync to Google Calendar (non-blocking, idempotent)
            try:
                BookingCalendarSync.sync_booking_cancelled(booking)
            except Exception as e:
                logger.warning(f"Failed to sync booking cancellation to calendar: {e}")

            return booking, None

        except OperationalError as e:
            db.session.rollback()
            if "could not obtain lock" in str(e) or "LockNotAvailable" in str(e):
                logger.warning(f"Booking {booking_id} locked by concurrent transaction")
                return None, "Booking is being processed, please try again"
            logger.error(f"Database error cancelling booking: {e}")
            return None, "Failed to cancel booking"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cancelling booking: {e}")
            return None, "Failed to cancel booking"
