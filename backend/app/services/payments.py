"""
Payment Service
Handles payment webhook processing and verification.
"""

import hashlib
import hmac
from typing import Optional, Tuple
from flask import current_app

from app.extensions import db
from app.models import Payment, Booking
from app.services.booking_hold import BookingHoldService
from app.services.notifications import NotificationService


class PaymentService:
    """
    Service for handling payments.
    Currently a stub that accepts signed requests and marks payments as succeeded.
    """

    @staticmethod
    def verify_webhook_signature(
        provider: str,
        payload: dict,
        signature: str,
    ) -> bool:
        """
        Verify webhook signature from payment provider.

        Args:
            provider: Payment provider name
            payload: Webhook payload
            signature: Provided signature

        Returns:
            True if signature is valid
        """
        webhook_secret = current_app.config.get("PAYMENT_WEBHOOK_SECRET", "")

        if current_app.debug and signature == "test_signature":
            return True

        # Build message to sign
        message = f"{payload.get('booking_id')}:{payload.get('payment_id')}:{payload.get('amount_rub')}"

        # Compute expected signature
        expected = hmac.new(
            webhook_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    @staticmethod
    def process_webhook(
        provider: str,
        payment_id: str,
        booking_id: str,
        amount_rub: int,
        status: str,
        raw_payload: dict = None,
    ) -> Tuple[Optional[Payment], Optional[str]]:
        """
        Process payment webhook.

        Args:
            provider: Payment provider (telegram/yookassa/cloudpayments/manual)
            payment_id: Provider's payment ID
            booking_id: Our booking ID
            amount_rub: Payment amount in rubles
            status: Payment status (succeeded/failed)
            raw_payload: Raw webhook payload for audit

        Returns:
            Tuple of (payment or None, error message or None)
        """
        booking = Booking.query.get(booking_id)
        if not booking:
            return None, "Booking not found"

        # Check if payment already exists
        existing_payment = Payment.query.filter_by(booking_id=booking_id).first()
        if existing_payment:
            if existing_payment.status == "succeeded":
                return existing_payment, None  # Already processed
            payment = existing_payment
        else:
            payment = Payment(
                booking_id=booking_id,
                provider=provider,
                amount_rub=amount_rub,
            )
            db.session.add(payment)

        payment.provider_payment_id = payment_id
        payment.raw_payload = raw_payload

        try:
            if status == "succeeded":
                payment.status = "succeeded"

                # Confirm the booking
                confirmed_booking, error = BookingHoldService.confirm_booking(booking_id)
                if error:
                    current_app.logger.warning(
                        f"Payment succeeded but booking confirmation failed: {error}"
                    )

                NotificationService.payment_received(booking, payment)

            elif status == "failed":
                payment.status = "failed"
                NotificationService.payment_failed(booking, payment)

            db.session.commit()
            return payment, None

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error processing payment webhook: {e}")
            return None, "Failed to process payment"

    @staticmethod
    def create_payment_intent(booking: Booking, provider: str = "telegram") -> dict:
        """
        Create a payment intent/invoice for the booking.
        This is a stub that returns mock payment data.

        Args:
            booking: Booking to pay for
            provider: Payment provider to use

        Returns:
            Payment intent data
        """
        # Create pending payment record
        payment = Payment(
            booking_id=booking.id,
            provider=provider,
            amount_rub=booking.price_rub,
            status="created",
        )
        db.session.add(payment)
        db.session.commit()

        # Return mock payment intent
        # In production, this would call the provider's API
        return {
            "payment_id": str(payment.id),
            "provider": provider,
            "amount_rub": booking.price_rub,
            "currency": "RUB",
            # For Telegram payments, this would be a stars payment URL
            # For YooKassa, this would be a confirmation URL
            "payment_url": f"https://pay.example.com/{payment.id}",
            "expires_at": booking.slot.hold_expires_at.isoformat()
            if booking.slot
            else None,
        }


