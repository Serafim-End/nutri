"""
Booking Calendar Sync Service
Handles synchronization of bookings with Google Calendar.

Idempotent operations:
- Creating events when bookings are paid (checks if event_id exists)
- Deleting events when bookings are cancelled (checks if event_id exists)

No side effects if Google Calendar is not connected.
"""

import logging
from typing import Optional
from flask import current_app

from app.extensions import db
from app.models import Booking, Profile
from app.services.google_calendar import GoogleCalendarService

logger = logging.getLogger(__name__)


class BookingCalendarSync:
    """
    Service for syncing bookings with Google Calendar.
    
    All operations are idempotent and safe to call multiple times.
    No side effects if Google Calendar is not connected.
    """

    @staticmethod
    def sync_booking_paid(booking: Booking) -> None:
        """
        Sync booking to Google Calendar when paid.
        
        Idempotent: If event_id already exists, skips creation.
        No side effects if Google Calendar not connected.
        
        Args:
            booking: Booking instance with status='paid'
        """
        if booking.status != "paid":
            logger.warning(
                f"sync_booking_paid called for booking {booking.id} with status {booking.status}"
            )
            return

        if not booking.nutritionist_id:
            logger.warning(f"Booking {booking.id} has no nutritionist_id")
            return

        if not booking.slot:
            logger.warning(f"Booking {booking.id} has no slot")
            return

        # Idempotency check: if event already exists, skip
        if booking.google_calendar_event_id:
            logger.debug(
                f"Booking {booking.id} already has calendar event {booking.google_calendar_event_id}, skipping"
            )
            return

        # Get client info for event description
        client_name = "Client"
        client_email = None
        if booking.client_id:
            client = Profile.query.get(booking.client_id)
            if client:
                client_name = client.full_name or "Client"
                # Note: Profile model doesn't have email, but we can add it to description

        # Get service info
        service_title = "Consultation"
        if booking.service:
            service_title = booking.service.title or "Consultation"

        # Build event details
        summary = f"{service_title} - {client_name}"
        description = f"Booking ID: {booking.id}\n"
        if booking.service:
            description += f"Service: {service_title}\n"
        description += f"Client: {client_name}\n"
        if booking.price_rub:
            description += f"Price: {booking.price_rub} {booking.currency}"

        # Create event
        event_id = GoogleCalendarService.create_event(
            nutritionist_id=str(booking.nutritionist_id),
            summary=summary,
            start_time=booking.slot.start_at,
            end_time=booking.slot.end_at,
            description=description,
            attendee_email=client_email,
        )

        if event_id:
            # Update booking with event ID
            booking.google_calendar_event_id = event_id
            db.session.commit()
            logger.info(
                f"Created calendar event for booking {booking.id}: event_id={event_id}"
            )
        else:
            # Not connected or error - no side effects, just log
            logger.debug(
                f"Could not create calendar event for booking {booking.id} "
                "(Google Calendar not connected or error)"
            )

    @staticmethod
    def sync_booking_cancelled(booking: Booking) -> None:
        """
        Sync booking cancellation to Google Calendar.
        
        Idempotent: If event_id doesn't exist, skips deletion.
        No side effects if Google Calendar not connected.
        
        Args:
            booking: Booking instance with status='cancelled'
        """
        if booking.status != "cancelled":
            logger.warning(
                f"sync_booking_cancelled called for booking {booking.id} with status {booking.status}"
            )
            return

        if not booking.nutritionist_id:
            logger.warning(f"Booking {booking.id} has no nutritionist_id")
            return

        # Idempotency check: if no event_id, nothing to delete
        if not booking.google_calendar_event_id:
            logger.debug(
                f"Booking {booking.id} has no calendar event, skipping deletion"
            )
            return

        event_id = booking.google_calendar_event_id

        # Delete event
        deleted = GoogleCalendarService.delete_event(
            nutritionist_id=str(booking.nutritionist_id),
            event_id=event_id,
        )

        if deleted:
            # Clear event ID from booking
            booking.google_calendar_event_id = None
            db.session.commit()
            logger.info(
                f"Deleted calendar event for booking {booking.id}: event_id={event_id}"
            )
        else:
            # Not connected or error - no side effects, just log
            logger.debug(
                f"Could not delete calendar event for booking {booking.id} "
                "(Google Calendar not connected or error)"
            )
