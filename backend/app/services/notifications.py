"""
Notification Service
Placeholder for sending notifications to users.
Currently logs events; can be extended for Telegram, email, etc.
"""

import json
import logging
from datetime import datetime
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import current_app

from app.models import Booking, Payment
from app.models.profile import Profile
from app.utils.timezone import get_default_tzinfo


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
        NotificationService._notify_nutritionist_paid_booking(booking, payment)
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

    @staticmethod
    def _notify_nutritionist_paid_booking(booking: Booking, payment: Payment) -> None:
        if booking.status != "paid":
            logger.debug(
                f"Skip nutritionist notification for booking {booking.id}: status={booking.status}"
            )
            return

        if not booking.nutritionist_id:
            logger.warning(f"Booking {booking.id} has no nutritionist_id")
            return

        nutritionist_profile = None
        if booking.nutritionist_profile:
            nutritionist_profile = booking.nutritionist_profile

        nutritionist = (
            nutritionist_profile.profile
            if nutritionist_profile and nutritionist_profile.profile
            else Profile.query.get(booking.nutritionist_id)
        )
        if not nutritionist:
            logger.warning(f"Nutritionist profile not found for booking {booking.id}")
            return

        chat_id = nutritionist.telegram_user_id
        if not chat_id:
            logger.warning(
                f"Nutritionist {nutritionist.id} has no telegram_user_id; "
                f"cannot send notification for booking {booking.id}"
            )
            return

        message = NotificationService._build_paid_booking_message(booking, payment)
        NotificationService._send_telegram_message(chat_id, message)

    @staticmethod
    def _build_paid_booking_message(booking: Booking, payment: Payment) -> str:
        client = booking.client
        client_full_name = "Клиент"
        client_id = "—"
        client_username = None
        client_phone = None
        client_email = None

        if client:
            client_full_name = client.full_name or client_full_name
            client_id = str(client.id)
            client_username = client.telegram_username
            client_phone = getattr(client, "phone", None) or getattr(
                client, "phone_number", None
            )
            client_email = getattr(client, "email", None)

        contacts = []
        if client_username:
            contacts.append(
                client_username if client_username.startswith("@") else f"@{client_username}"
            )
        if client_phone:
            contacts.append(str(client_phone))
        if client_email:
            contacts.append(str(client_email))

        contacts_line = "контакты: " + ("  ".join(contacts) if contacts else "нет")

        service_name = booking.service.title if booking.service else "Консультация"
        price_paid = payment.amount_rub if payment and payment.amount_rub else booking.price_rub

        booking_date = "—"
        booking_time = "—"
        if booking.slot and isinstance(booking.slot.start_at, datetime):
            tzinfo = get_default_tzinfo()
            start_at = booking.slot.start_at
            if start_at.tzinfo is None:
                start_at = start_at.replace(tzinfo=tzinfo)
            local_dt = start_at.astimezone(tzinfo)
            booking_date = local_dt.strftime("%d.%m.%Y")
            booking_time = local_dt.strftime("%H:%M")

        return (
            "✅ Новая оплаченная запись\n\n"
            f"Клиент: {client_full_name} (ID: {client_id})\n"
            f"{contacts_line}\n"
            f"Услуга: {service_name}\n"
            f"Дата: {booking_date}\n"
            f"Время: {booking_time}\n"
            f"Оплата: {price_paid} ₽"
        )

    @staticmethod
    def _send_telegram_message(chat_id: int, text: str) -> None:
        token = current_app.config.get("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.warning("TELEGRAM_BOT_TOKEN not configured; cannot send Telegram message")
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        data = json.dumps(payload).encode("utf-8")
        request = Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urlopen(request, timeout=10) as response:
                if response.status >= 400:
                    logger.warning(
                        "Telegram sendMessage failed: status=%s chat_id=%s",
                        response.status,
                        chat_id,
                    )
        except (HTTPError, URLError) as exc:
            logger.warning("Telegram sendMessage error: %s", exc)
        except Exception as exc:
            logger.error("Unexpected Telegram sendMessage error: %s", exc)

