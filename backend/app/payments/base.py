"""
Payment Provider Base Classes

Abstract interface for payment providers.
All payment providers must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class PaymentStatus(str, Enum):
    """Payment status enum."""
    CREATED = "created"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class PaymentResult:
    """
    Result of processing a payment webhook.
    
    Attributes:
        booking_id: UUID of the associated booking
        provider_payment_id: Provider's unique payment identifier
        status: Payment status (succeeded or failed)
        raw_payload: Original webhook payload for audit
    """
    booking_id: str
    provider_payment_id: str
    status: PaymentStatus
    raw_payload: dict | None = None
    
    @property
    def is_success(self) -> bool:
        """Check if payment succeeded."""
        return self.status == PaymentStatus.SUCCEEDED


@dataclass
class PaymentIntent:
    """
    Payment intent created for a booking.
    
    Attributes:
        payment_id: Our internal payment ID
        provider: Provider name (mock, telegram, yookassa, etc.)
        payment_url: URL to redirect user for payment (or mock URL)
        amount_rub: Amount in rubles
        currency: Currency code (RUB)
        expires_at: ISO timestamp when hold expires
        provider_data: Additional provider-specific data
    """
    payment_id: str
    provider: str
    payment_url: str
    amount_rub: int
    currency: str = "RUB"
    expires_at: str | None = None
    provider_data: dict | None = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "payment_id": self.payment_id,
            "provider": self.provider,
            "payment_url": self.payment_url,
            "amount_rub": self.amount_rub,
            "currency": self.currency,
            "expires_at": self.expires_at,
        }


class PaymentProvider(ABC):
    """
    Abstract base class for payment providers.
    
    To implement a new provider:
    1. Subclass PaymentProvider
    2. Implement all abstract methods
    3. Register with register_provider() in __init__.py
    
    Example implementation:
    
        class TelegramPaymentProvider(PaymentProvider):
            name = "telegram"
            
            def create_payment_intent(self, booking) -> PaymentIntent:
                # Call Telegram Payments API
                # Create invoice link
                return PaymentIntent(...)
            
            def handle_webhook(self, payload, headers) -> PaymentResult:
                # Verify Telegram signature
                # Parse successful_payment update
                return PaymentResult(...)
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique provider name.
        
        Returns:
            Provider identifier (e.g., "mock", "telegram", "yookassa")
        """
        pass
    
    @abstractmethod
    def create_payment_intent(self, booking: Any) -> PaymentIntent:
        """
        Create a payment intent for the booking.
        
        This method should:
        1. Call the provider's API to create payment/invoice
        2. Return a PaymentIntent with the payment URL
        
        Args:
            booking: Booking model instance
        
        Returns:
            PaymentIntent with payment_url for redirecting user
        
        Raises:
            PaymentProviderError: If provider API call fails
        """
        pass
    
    @abstractmethod
    def handle_webhook(
        self,
        payload: dict,
        headers: dict,
    ) -> PaymentResult:
        """
        Process incoming webhook from the payment provider.
        
        This method should:
        1. Verify the webhook signature/authenticity
        2. Extract payment information
        3. Return PaymentResult with status
        
        Args:
            payload: Webhook request body (parsed JSON)
            headers: Request headers for signature verification
        
        Returns:
            PaymentResult with booking_id and status
        
        Raises:
            PaymentWebhookError: If signature verification fails
            PaymentWebhookError: If payload is invalid
        """
        pass
    
    def verify_signature(self, payload: dict, headers: dict) -> bool:
        """
        Verify webhook signature.
        
        Override this method if your provider requires signature verification.
        Default implementation returns True (no verification).
        
        Args:
            payload: Webhook request body
            headers: Request headers
        
        Returns:
            True if signature is valid
        """
        return True
    
    def refund_payment(self, payment_id: str, amount: int | None = None) -> bool:
        """
        Refund a payment.
        
        Optional method - not all providers may support refunds.
        Default implementation raises NotImplementedError.
        
        Args:
            payment_id: Provider's payment ID
            amount: Amount to refund (None = full refund)
        
        Returns:
            True if refund was successful
        
        Raises:
            NotImplementedError: If provider doesn't support refunds
        """
        raise NotImplementedError(
            f"Refunds are not implemented for {self.name} provider"
        )


class PaymentProviderError(Exception):
    """Base exception for payment provider errors."""
    pass


class PaymentWebhookError(PaymentProviderError):
    """Exception for webhook processing errors."""
    pass

