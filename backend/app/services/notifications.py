"""
Notification Service
Placeholder for sending notifications to users.
Currently logs events; can be extended for Telegram, email, etc.
"""

import logging
from typing import Optional

from app.models import Booking, Payment


logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications.
    Currently a placeholder that logs events.
    Can be extended to send Telegram messages, emails, push notifications, etc.
    """

    @staticmethod
    def booking_created(booking: Booking) -> None:
        """Notify about new booking creation."""
        logger.info(
            f"[NOTIFICATION] Booking created: {booking.id} "
            f"for client {booking.client_id}, "
            f"nutritionist {booking.nutritionist_id}"
        )
        # TODO: Send Telegram message to client with payment instructions
        # TODO: Optionally notify nutritionist about pending booking

    @staticmethod
    def booking_confirmed(booking: Booking) -> None:
        """Notify about booking confirmation after payment."""
        logger.info(
            f"[NOTIFICATION] Booking confirmed: {booking.id} "
            f"- Payment received, consultation scheduled"
        )
        # TODO: Send Telegram message to client with confirmation and meeting link
        # TODO: Send Telegram message to nutritionist with client details

    @staticmethod
    def booking_cancelled(booking: Booking, reason: Optional[str] = None) -> None:
        """Notify about booking cancellation."""
        reason_msg = f" Reason: {reason}" if reason else ""
        logger.info(
            f"[NOTIFICATION] Booking cancelled: {booking.id}{reason_msg}"
        )
        # TODO: Send Telegram message to client about cancellation
        # TODO: Send Telegram message to nutritionist about slot becoming available

    @staticmethod
    def booking_reminder(booking: Booking, minutes_before: int) -> None:
        """Send reminder before scheduled consultation."""
        logger.info(
            f"[NOTIFICATION] Booking reminder: {booking.id} "
            f"- Consultation in {minutes_before} minutes"
        )
        # TODO: Send Telegram reminder to both client and nutritionist

    @staticmethod
    def payment_received(booking: Booking, payment: Payment) -> None:
        """Notify about successful payment."""
        logger.info(
            f"[NOTIFICATION] Payment received: {payment.id} "
            f"for booking {booking.id}, amount {payment.amount_rub} RUB"
        )
        # TODO: Send payment confirmation to client

    @staticmethod
    def payment_failed(booking: Booking, payment: Payment) -> None:
        """Notify about failed payment."""
        logger.warning(
            f"[NOTIFICATION] Payment failed: {payment.id} "
            f"for booking {booking.id}"
        )
        # TODO: Send Telegram message to client about failed payment
        # TODO: Suggest retry

    @staticmethod
    def nutritionist_approved(nutritionist_id: str) -> None:
        """Notify nutritionist about profile approval."""
        logger.info(
            f"[NOTIFICATION] Nutritionist approved: {nutritionist_id}"
        )
        # TODO: Send Telegram message to nutritionist about approval

    @staticmethod
    def nutritionist_rejected(nutritionist_id: str, reason: Optional[str] = None) -> None:
        """Notify nutritionist about profile rejection."""
        reason_msg = f" Reason: {reason}" if reason else ""
        logger.info(
            f"[NOTIFICATION] Nutritionist rejected: {nutritionist_id}{reason_msg}"
        )
        # TODO: Send Telegram message to nutritionist with rejection reason

    @staticmethod
    def document_reviewed(document_id: str, status: str, note: Optional[str] = None) -> None:
        """Notify about document review result."""
        logger.info(
            f"[NOTIFICATION] Document reviewed: {document_id} - Status: {status}"
        )
        # TODO: Notify nutritionist about document review result


