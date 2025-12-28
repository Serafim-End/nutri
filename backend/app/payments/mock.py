"""
Mock Payment Provider

Development-only payment provider for testing the payment flow.
Simulates immediate payment success without real money transfer.

Usage:
    Set PAYMENT_PROVIDER=mock in environment (default in development)
    
Flow:
    1. create_payment_intent returns a fake payment URL
    2. Client shows "Simulate payment success" button
    3. Button triggers webhook or mark-paid endpoint
    4. handle_webhook always returns status=succeeded
"""

import logging
from typing import Any
from flask import current_app, url_for

from app.payments.base import (
    PaymentProvider,
    PaymentIntent,
    PaymentResult,
    PaymentStatus,
)

logger = logging.getLogger(__name__)


class MockPaymentProvider(PaymentProvider):
    """
    Mock payment provider for development and testing.
    
    This provider:
    - Creates fake payment URLs pointing to internal endpoints
    - Always succeeds on webhook (simulates successful payment)
    - Logs all operations for debugging
    
    IMPORTANT: This provider should ONLY be used in development.
    """
    
    @property
    def name(self) -> str:
        return "mock"
    
    def create_payment_intent(self, booking: Any) -> PaymentIntent:
        """
        Create a mock payment intent.
        
        Returns a PaymentIntent with:
        - payment_url: URL that can trigger payment success
        - provider_data: Contains mock payment info
        
        Args:
            booking: Booking model instance
        
        Returns:
            PaymentIntent for mock payment flow
        """
        # Get payment record from booking (created by PaymentService)
        payment = booking.payment
        
        # Build mock payment URL
        # In dev mode, this points to an endpoint that simulates success
        try:
            # Try to build URL with application context
            payment_url = f"/api/payments/mock-pay/{booking.id}"
        except RuntimeError:
            # Outside request context, use relative URL
            payment_url = f"/api/payments/mock-pay/{booking.id}"
        
        # Get hold expiration time
        expires_at = None
        if booking.slot and booking.slot.hold_expires_at:
            expires_at = booking.slot.hold_expires_at.isoformat()
        
        logger.info(
            f"[MockPayment] Created payment intent: "
            f"booking_id={booking.id}, "
            f"payment_id={payment.id if payment else 'N/A'}, "
            f"amount={booking.price_rub} RUB"
        )
        
        return PaymentIntent(
            payment_id=str(payment.id) if payment else str(booking.id),
            provider=self.name,
            payment_url=payment_url,
            amount_rub=booking.price_rub,
            currency=booking.currency,
            expires_at=expires_at,
            provider_data={
                "mock": True,
                "instructions": "Call webhook endpoint or use mark-paid to simulate success",
            },
        )
    
    def handle_webhook(
        self,
        payload: dict,
        headers: dict,
    ) -> PaymentResult:
        """
        Process mock webhook - always succeeds.
        
        This simulates a successful payment callback.
        In production, this would verify the signature and parse the payload.
        
        Expected payload format:
            {
                "booking_id": "uuid",
                "status": "succeeded" | "failed"  # optional, defaults to succeeded
            }
        
        Args:
            payload: Webhook payload with booking_id
            headers: Request headers (ignored for mock)
        
        Returns:
            PaymentResult with succeeded status
        """
        booking_id = payload.get("booking_id")
        
        if not booking_id:
            raise ValueError("booking_id is required in webhook payload")
        
        # Status is configurable for testing, defaults to succeeded
        status_str = payload.get("status", "succeeded")
        status = (
            PaymentStatus.SUCCEEDED 
            if status_str == "succeeded" 
            else PaymentStatus.FAILED
        )
        
        # Generate mock payment ID
        provider_payment_id = f"mock_{booking_id}"
        
        logger.info(
            f"[MockPayment] Webhook processed: "
            f"booking_id={booking_id}, "
            f"status={status.value}"
        )
        
        return PaymentResult(
            booking_id=booking_id,
            provider_payment_id=provider_payment_id,
            status=status,
            raw_payload=payload,
        )
    
    def verify_signature(self, payload: dict, headers: dict) -> bool:
        """
        Mock signature verification - always returns True.
        
        In development mode with mock provider, we skip signature verification.
        Real providers must implement proper HMAC/signature verification.
        """
        # Check for test signature header (optional)
        signature = headers.get("X-Payment-Signature", "")
        
        if signature and signature != "test_signature":
            logger.warning(
                "[MockPayment] Non-test signature provided but accepted (dev mode)"
            )
        
        return True
    
    def refund_payment(self, payment_id: str, amount: int | None = None) -> bool:
        """
        Mock refund - logs and returns success.
        
        Args:
            payment_id: Payment ID to refund
            amount: Amount to refund (None = full)
        
        Returns:
            Always True for mock provider
        """
        logger.info(
            f"[MockPayment] Refund simulated: "
            f"payment_id={payment_id}, "
            f"amount={amount or 'full'}"
        )
        return True

