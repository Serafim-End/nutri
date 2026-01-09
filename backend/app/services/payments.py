"""
Payment Service - Central Payment Logic

This service is the single point of entry for all payment operations.
It orchestrates:
    1. Payment intent creation (delegates to provider)
    2. Payment finalization (webhook processing)
    3. Payment status transitions

All booking state changes related to payments go through this service.
This ensures consistent behavior regardless of payment provider.
"""

import logging
from typing import Optional, Tuple
from datetime import datetime, timezone
from flask import current_app
from sqlalchemy.exc import OperationalError

from app.extensions import db
from app.models import Payment, Booking, AvailabilitySlot
from app.payments import get_provider, PaymentResult
from app.payments.base import PaymentStatus, PaymentIntent
from app.services.notifications import NotificationService
from app.services.booking_calendar_sync import BookingCalendarSync

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class PaymentService:
    """
    Central service for payment operations.
    
    This service handles:
        - Payment intent creation (with provider delegation)
        - Payment finalization (booking confirmation after webhook)
        - Idempotent webhook processing
        - Transactional state changes
    
    All payment operations are logged with booking_id, payment_id, provider, and status.
    """

    @staticmethod
    def create_payment_for_booking(
        booking: Booking,
        provider_name: str | None = None,
    ) -> Tuple[Optional[dict], Optional[str]]:
        """
        Create a payment record and get payment intent from provider.
        
        This is the main entry point for initiating payment.
        
        Args:
            booking: Booking model instance (must be pending_payment)
            provider_name: Optional provider override (uses config if None)
        
        Returns:
            Tuple of (payment_intent_dict, error_message)
        
        Flow:
            1. Validate booking status
            2. Create Payment record with status=created
            3. Get provider instance
            4. Delegate to provider.create_payment_intent()
            5. Return payment URL and info
        """
        # Validate booking status
        if booking.status != "pending_payment":
            return None, f"Booking status is {booking.status}, expected pending_payment"
        
        # Check for existing payment
        existing_payment = Payment.query.filter_by(booking_id=booking.id).first()
        if existing_payment:
            if existing_payment.status == "succeeded":
                return None, "Payment already completed"
            # Return existing payment intent if still pending
            if existing_payment.status == "created":
                logger.info(
                    f"Returning existing payment intent: "
                    f"booking_id={booking.id}, payment_id={existing_payment.id}"
                )
                provider = get_provider(existing_payment.provider)
                intent = provider.create_payment_intent(booking)
                return intent.to_dict(), None
        
        try:
            # Get provider
            provider = get_provider(provider_name)
            
            # Create payment record
            payment = Payment(
                booking_id=booking.id,
                provider=provider.name,
                amount_rub=booking.price_rub,
                currency=booking.currency,
                status="created",
            )
            db.session.add(payment)
            db.session.flush()  # Get payment.id without committing
            
            # Create payment intent via provider
            intent = provider.create_payment_intent(booking)
            
            db.session.commit()
            
            logger.info(
                f"Payment created: "
                f"booking_id={booking.id}, "
                f"payment_id={payment.id}, "
                f"provider={provider.name}, "
                f"amount={payment.amount_rub} {payment.currency}"
            )
            
            return intent.to_dict(), None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create payment: {e}")
            return None, f"Failed to create payment: {str(e)}"

    @staticmethod
    def finalize_payment(
        result: PaymentResult,
    ) -> Tuple[Optional[Payment], Optional[str]]:
        """
        Finalize payment after webhook confirmation.
        
        This is the ONLY method that should transition:
            - booking: pending_payment -> paid
            - slot: held -> booked
            - payment: created -> succeeded
        
        Transactional with row-level locking.
        Idempotent - safe to call multiple times.
        
        Args:
            result: PaymentResult from provider.handle_webhook()
        
        Returns:
            Tuple of (Payment, error_message)
        
        Flow:
            1. Lock booking row
            2. Lock slot row
            3. Validate states
            4. Update payment status
            5. Update booking status
            6. Update slot status
            7. Send notifications
        """
        booking_id = result.booking_id
        now = utc_now()
        
        try:
            # Lock booking row for update
            booking = db.session.query(Booking).filter(
                Booking.id == booking_id
            ).with_for_update(nowait=True).first()
            
            if not booking:
                return None, "Booking not found"
            
            # Get or create payment record
            payment = Payment.query.filter_by(booking_id=booking_id).first()
            
            if not payment:
                # Payment record doesn't exist - create it (backward compatibility)
                payment = Payment(
                    booking_id=booking_id,
                    provider=result.raw_payload.get("provider", "unknown") if result.raw_payload else "unknown",
                    amount_rub=booking.price_rub,
                    currency=booking.currency,
                    status="created",
                )
                db.session.add(payment)
            
            # Idempotency: if already succeeded, return existing
            if payment.status == "succeeded":
                logger.info(
                    f"Payment already succeeded (idempotent): "
                    f"booking_id={booking_id}, payment_id={payment.id}"
                )
                return payment, None
            
            # Update payment with provider data
            payment.provider_payment_id = result.provider_payment_id
            payment.raw_payload = result.raw_payload
            
            if result.status == PaymentStatus.SUCCEEDED:
                # Validate booking state
                if booking.status != "pending_payment":
                    logger.warning(
                        f"Booking state unexpected: "
                        f"booking_id={booking_id}, status={booking.status}"
                    )
                    if booking.status == "paid":
                        payment.status = "succeeded"
                        db.session.commit()
                        return payment, None
                    return None, f"Booking status is {booking.status}, expected pending_payment"
                
                # Lock and update slot
                slot = db.session.query(AvailabilitySlot).filter(
                    AvailabilitySlot.id == booking.slot_id
                ).with_for_update(nowait=True).first()
                
                if not slot:
                    logger.error(f"Slot not found for booking: {booking_id}")
                    return None, "Slot not found"
                
                # Check hold expiration (allow some grace period)
                if slot.status == "held" and slot.hold_expires_at:
                    hold_expires = slot.hold_expires_at
                    if hold_expires.tzinfo is None:
                        hold_expires = hold_expires.replace(tzinfo=timezone.utc)
                    # If hold expired, we still process payment but log warning
                    if hold_expires < now:
                        logger.warning(
                            f"Processing payment for expired hold: "
                            f"booking_id={booking_id}, expired_at={hold_expires}"
                        )
                
                # Update all states atomically
                payment.status = "succeeded"
                booking.status = "paid"
                booking.paid_at = now
                
                if slot.status == "held":
                    slot.status = "booked"
                    slot.hold_expires_at = None
                
                db.session.commit()
                
                logger.info(
                    f"Payment finalized: "
                    f"booking_id={booking_id}, "
                    f"payment_id={payment.id}, "
                    f"provider={payment.provider}, "
                    f"status=succeeded"
                )
                
                # Send notifications (non-blocking)
                try:
                    NotificationService.payment_received(booking, payment)
                    NotificationService.booking_confirmed(booking)
                except Exception as e:
                    logger.warning(f"Failed to send payment notification: {e}")
                
                # Sync to Google Calendar (non-blocking, idempotent)
                try:
                    BookingCalendarSync.sync_booking_paid(booking)
                except Exception as e:
                    logger.warning(f"Failed to sync booking to calendar: {e}")
                
                return payment, None
                
            elif result.status == PaymentStatus.FAILED:
                payment.status = "failed"
                db.session.commit()
                
                logger.info(
                    f"Payment failed: "
                    f"booking_id={booking_id}, "
                    f"payment_id={payment.id}"
                )
                
                try:
                    NotificationService.payment_failed(booking, payment)
                except Exception as e:
                    logger.warning(f"Failed to send failure notification: {e}")
                
                return payment, None
            
            else:
                return None, f"Unknown payment status: {result.status}"
                
        except OperationalError as e:
            db.session.rollback()
            if "could not obtain lock" in str(e) or "LockNotAvailable" in str(e):
                logger.warning(f"Booking locked: {booking_id}")
                return None, "Booking is being processed, please retry"
            logger.error(f"Database error finalizing payment: {e}")
            return None, "Failed to process payment"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error finalizing payment: {e}")
            return None, f"Failed to process payment: {str(e)}"

    @staticmethod
    def process_provider_webhook(
        provider_name: str,
        payload: dict,
        headers: dict,
    ) -> Tuple[Optional[Payment], Optional[str]]:
        """
        Process webhook from a payment provider.
        
        This method:
            1. Gets the provider by name
            2. Verifies signature (if applicable)
            3. Delegates to provider.handle_webhook()
            4. Calls finalize_payment() with result
        
        Args:
            provider_name: Provider identifier (mock, telegram, yookassa, etc.)
            payload: Webhook request body
            headers: Request headers for signature verification
        
        Returns:
            Tuple of (Payment, error_message)
        """
        try:
            provider = get_provider(provider_name)
        except ValueError as e:
            return None, str(e)
        
        # Verify signature
        if not provider.verify_signature(payload, headers):
            logger.warning(
                f"Invalid webhook signature: provider={provider_name}"
            )
            return None, "Invalid signature"
        
        try:
            # Parse webhook and get result
            result = provider.handle_webhook(payload, headers)
            
            logger.info(
                f"Webhook processed: "
                f"provider={provider_name}, "
                f"booking_id={result.booking_id}, "
                f"status={result.status.value}"
            )
            
            # Finalize payment
            return PaymentService.finalize_payment(result)
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return None, f"Failed to process webhook: {str(e)}"

    @staticmethod
    def simulate_payment_success(booking_id: str) -> Tuple[Optional[Payment], Optional[str]]:
        """
        Simulate successful payment (DEV ONLY).
        
        This is a convenience method for development that:
            1. Creates a mock PaymentResult
            2. Calls finalize_payment()
        
        IMPORTANT: This should only be used in development mode.
        In production, payments must go through proper webhook flow.
        
        Args:
            booking_id: UUID of the booking
        
        Returns:
            Tuple of (Payment, error_message)
        """
        if not current_app.debug and not current_app.config.get("TESTING"):
            env = current_app.config.get("FLASK_ENV", "production")
            if env not in ("development", "testing"):
                return None, "Payment simulation only available in development"
        
        result = PaymentResult(
            booking_id=booking_id,
            provider_payment_id=f"mock_simulated_{booking_id}",
            status=PaymentStatus.SUCCEEDED,
            raw_payload={"simulated": True, "method": "mark-paid"},
        )
        
        logger.info(f"Simulating payment success: booking_id={booking_id}")
        
        return PaymentService.finalize_payment(result)

    @staticmethod
    def get_payment_status(booking_id: str) -> dict | None:
        """
        Get payment status for a booking.
        
        Args:
            booking_id: UUID of the booking
        
        Returns:
            Payment status dict or None if not found
        """
        payment = Payment.query.filter_by(booking_id=booking_id).first()
        if payment:
            return payment.to_dict()
        return None
