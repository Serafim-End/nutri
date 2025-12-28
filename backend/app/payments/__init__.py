"""
Payment Provider Abstraction Layer

This module provides a unified interface for payment providers.
To add a new payment provider:
1. Create a new file in app/payments/ (e.g., telegram.py)
2. Implement the PaymentProvider abstract class
3. Register it in get_provider() below
4. Set PAYMENT_PROVIDER=<provider_name> in environment

See README.md section "How to plug a real payment provider" for details.
"""

from app.payments.base import PaymentProvider, PaymentResult
from app.payments.mock import MockPaymentProvider

__all__ = [
    "PaymentProvider",
    "PaymentResult",
    "MockPaymentProvider",
    "get_provider",
]


# Registry of available payment providers
_PROVIDERS: dict[str, type[PaymentProvider]] = {
    "mock": MockPaymentProvider,
}


def get_provider(provider_name: str | None = None) -> PaymentProvider:
    """
    Get a payment provider instance by name.
    
    Args:
        provider_name: Provider name (mock, telegram, yookassa, cloudpayments).
                      If None, uses PAYMENT_PROVIDER env var or defaults to mock.
    
    Returns:
        Configured PaymentProvider instance.
    
    Raises:
        ValueError: If provider is not registered.
    
    Example:
        >>> provider = get_provider("mock")
        >>> intent = provider.create_payment_intent(booking)
    """
    from flask import current_app
    import os
    
    if provider_name is None:
        # Get from config or env, default to mock in development
        provider_name = current_app.config.get("PAYMENT_PROVIDER")
        if not provider_name:
            provider_name = os.environ.get("PAYMENT_PROVIDER", "mock")
    
    provider_name = provider_name.lower()
    
    if provider_name not in _PROVIDERS:
        available = ", ".join(_PROVIDERS.keys())
        raise ValueError(
            f"Unknown payment provider: {provider_name}. "
            f"Available providers: {available}"
        )
    
    provider_class = _PROVIDERS[provider_name]
    return provider_class()


def register_provider(name: str, provider_class: type[PaymentProvider]) -> None:
    """
    Register a new payment provider.
    
    Args:
        name: Provider name (e.g., "telegram", "yookassa")
        provider_class: PaymentProvider subclass
    
    Example:
        >>> from app.payments import register_provider
        >>> from app.payments.telegram import TelegramPaymentProvider
        >>> register_provider("telegram", TelegramPaymentProvider)
    """
    _PROVIDERS[name.lower()] = provider_class

