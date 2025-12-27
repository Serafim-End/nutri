"""
Booking Hold Service
Manages slot holds and releases expired holds.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from flask import current_app

from app.extensions import db
from app.models import AvailabilitySlot, Booking, Service
from app.services.notifications import NotificationService


class BookingHoldService:
    """
    Service for managing booking holds.
    Implements 10-minute hold window for payment processing.
    """

    @staticmethod
    def create_booking_with_hold(
        client_id: str,
        service_id: str,
        slot_id: str,
    ) -> Tuple[Optional[Booking], Optional[str]]:
        """
        Create a booking and hold the slot for payment.

        Args:
            client_id: UUID of the client
            service_id: UUID of the service
            slot_id: UUID of the availability slot

        Returns:
            Tuple of (booking or None, error message or None)
        """
        hold_minutes = current_app.config.get("SLOT_HOLD_MINUTES", 10)

        # Verify service exists and is active
        service = Service.query.get(service_id)
        if not service or not service.is_active:
            return None, "Service not found or inactive"

        # Verify slot exists and is free
        slot = AvailabilitySlot.query.get(slot_id)
        if not slot:
            return None, "Slot not found"

        if slot.status != "free":
            return None, "Slot is not available"

        # Verify slot belongs to the service's nutritionist
        if str(slot.nutritionist_id) != str(service.nutritionist_id):
            return None, "Slot does not belong to this nutritionist"

        # Check if slot is in the future
        if slot.start_at <= datetime.utcnow():
            return None, "Cannot book a slot in the past"

        try:
            # Hold the slot
            slot.status = "held"
            slot.hold_expires_at = datetime.utcnow() + timedelta(minutes=hold_minutes)

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

            # Send notification (placeholder)
            NotificationService.booking_created(booking)

            return booking, None

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating booking: {e}")
            return None, "Failed to create booking"

    @staticmethod
    def release_expired_holds() -> int:
        """
        Release all expired slot holds and cancel associated bookings.
        This is designed to be called by a cron job.

        Returns:
            Number of slots released
        """
        now = datetime.utcnow()

        # Find expired held slots
        expired_slots = AvailabilitySlot.query.filter(
            AvailabilitySlot.status == "held",
            AvailabilitySlot.hold_expires_at <= now,
        ).all()

        released_count = 0

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
                    NotificationService.booking_cancelled(booking, "Payment timeout")

                # Release the slot
                slot.status = "free"
                slot.hold_expires_at = None

                released_count += 1

            except Exception as e:
                current_app.logger.error(f"Error releasing slot {slot.id}: {e}")
                continue

        if released_count > 0:
            db.session.commit()
            current_app.logger.info(f"Released {released_count} expired holds")

        return released_count

    @staticmethod
    def confirm_booking(booking_id: str) -> Tuple[Optional[Booking], Optional[str]]:
        """
        Confirm a booking after successful payment.

        Args:
            booking_id: UUID of the booking

        Returns:
            Tuple of (booking or None, error message or None)
        """
        booking = Booking.query.get(booking_id)

        if not booking:
            return None, "Booking not found"

        if booking.status != "pending_payment":
            return None, f"Booking status is {booking.status}, cannot confirm"

        slot = AvailabilitySlot.query.get(booking.slot_id)
        if not slot:
            return None, "Slot not found"

        try:
            # Update booking status
            booking.status = "paid"
            booking.paid_at = datetime.utcnow()

            # Update slot status
            slot.status = "booked"
            slot.hold_expires_at = None

            db.session.commit()

            # Send notifications
            NotificationService.booking_confirmed(booking)

            return booking, None

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error confirming booking: {e}")
            return None, "Failed to confirm booking"

    @staticmethod
    def cancel_booking(
        booking_id: str, user_id: str, reason: str = None
    ) -> Tuple[Optional[Booking], Optional[str]]:
        """
        Cancel a booking and release the slot.

        Args:
            booking_id: UUID of the booking
            user_id: UUID of the user cancelling
            reason: Optional cancellation reason

        Returns:
            Tuple of (booking or None, error message or None)
        """
        booking = Booking.query.get(booking_id)

        if not booking:
            return None, "Booking not found"

        # Verify ownership
        if str(booking.client_id) != user_id:
            return None, "Not authorized to cancel this booking"

        if booking.status in ("cancelled", "completed", "refunded"):
            return None, f"Booking already {booking.status}"

        try:
            # Release the slot
            slot = AvailabilitySlot.query.get(booking.slot_id)
            if slot:
                slot.status = "free"
                slot.hold_expires_at = None

            # Cancel booking
            booking.status = "cancelled"
            booking.cancelled_at = datetime.utcnow()

            db.session.commit()

            # Send notification
            NotificationService.booking_cancelled(booking, reason)

            return booking, None

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error cancelling booking: {e}")
            return None, "Failed to cancel booking"


