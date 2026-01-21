"""
Application Configuration

Handles database connection setup for PostgreSQL.
"""

import os
import sys
import logging
from datetime import timedelta
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)


def _normalize_database_url(url: str | None) -> str:
    """
    Normalize DATABASE_URL for SQLAlchemy compatibility.
    
    - Converts 'postgresql://' to 'postgresql+psycopg2://'
    - Validates URL format
    
    Returns normalized URL string.
    Raises ValueError if URL is missing or invalid.
    """
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Set it to your PostgreSQL connection string."
        )
    
    url = url.strip()
    
    # Parse the URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid DATABASE_URL format: {e}")
    
    if not parsed.scheme or not parsed.hostname:
        raise ValueError(
            "Invalid DATABASE_URL: must be a valid PostgreSQL connection string "
            "(e.g., postgresql://user:pass@host:port/dbname)"
        )
    
    # Normalize scheme: postgresql:// -> postgresql+psycopg2://
    scheme = parsed.scheme
    if scheme == "postgresql":
        scheme = "postgresql+psycopg2"
    elif scheme == "postgres":
        scheme = "postgresql+psycopg2"
    elif scheme != "postgresql+psycopg2":
        raise ValueError(
            f"Invalid DATABASE_URL scheme: {parsed.scheme}. "
            "Expected 'postgresql' or 'postgresql+psycopg2'."
        )
    
    # Rebuild URL (preserve existing query parameters if any)
    normalized = urlunparse((
        scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))
    
    return normalized


def _get_database_url() -> str:
    """
    Get and validate DATABASE_URL from environment.
    Logs connection info (without secrets) on success.
    Fails fast with clear error on failure.
    """
    raw_url = os.environ.get("DATABASE_URL")
    
    try:
        normalized_url = _normalize_database_url(raw_url)
    except ValueError as e:
        # Fail fast with clear error message
        print(f"\n❌ DATABASE CONFIGURATION ERROR: {e}\n", file=sys.stderr)
        sys.exit(1)
    
    # Log connection info (without password)
    try:
        parsed = urlparse(normalized_url)
        host = parsed.hostname or "unknown"
        port = parsed.port or 5432
        database = parsed.path.lstrip("/") or "unknown"
        
        logger.info(f"Database: PostgreSQL @ {host}:{port}/{database}")
    except Exception:
        pass  # Don't fail on logging issues
    
    return normalized_url


class Config:
    """Base configuration class."""

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

    # Database - normalized PostgreSQL connection
    SQLALCHEMY_DATABASE_URI = _get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # Verify connections before use
        "pool_recycle": 300,    # Recycle connections after 5 minutes
        "pool_size": 5,         # Number of connections to keep
        "max_overflow": 10,     # Max additional connections
        "connect_args": {
            "connect_timeout": 10,  # Connection timeout in seconds
            "options": "-c statement_timeout=30000",  # 30 second statement timeout
        },
    }

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
    )
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    WEBAPP_URL = os.environ.get("WEBAPP_URL", "")

    # CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

    # Booking Configuration
    SLOT_HOLD_MINUTES = int(os.environ.get("SLOT_HOLD_MINUTES", "10"))
    BOOKING_HOLD_MINUTES = int(os.environ.get("BOOKING_HOLD_MINUTES", "10"))

    # Payment Configuration
    # Available providers: mock, prodamus, telegram, yookassa, cloudpayments
    # Default: mock (for development)
    PAYMENT_PROVIDER = os.environ.get("PAYMENT_PROVIDER", "mock")
    PAYMENT_WEBHOOK_SECRET = os.environ.get("PAYMENT_WEBHOOK_SECRET", "webhook-secret")

    # Prodamus Payform (when PAYMENT_PROVIDER=prodamus)
    PAYFORM_FORM_URL = os.environ.get(
        "PAYFORM_FORM_URL",
        "https://vitakotsarenko.payform.ru/",
    )
    PAYFORM_SECRET = os.environ.get("PAYFORM_SECRET", "")
    PAYFORM_SYS = os.environ.get("PAYFORM_SYS", "")
    PAYFORM_SUCCESS_URL = os.environ.get(
        "PAYFORM_SUCCESS_URL",
        "https://tma.nutrutioncoach.com/payment/success",
    )
    PAYFORM_RETURN_URL = os.environ.get(
        "PAYFORM_RETURN_URL",
        "https://tma.nutrutioncoach.com/payment/fail",
    )
    PAYFORM_NOTIFICATION_URL = os.environ.get(
        "PAYFORM_NOTIFICATION_URL",
        "https://api.nutrutioncoach.com/api/payments/webhook/prodamus",
    )
    PAYFORM_LINK_EXPIRE_MINUTES = int(os.environ.get("PAYFORM_LINK_EXPIRE_MINUTES", "15"))
    
    # Provider-specific configuration (used when provider is implemented)
    # TELEGRAM_PAYMENTS_TOKEN - Telegram Bot Payments token (same as TELEGRAM_BOT_TOKEN)
    # YOOKASSA_SHOP_ID - YooKassa shop identifier
    # YOOKASSA_SECRET_KEY - YooKassa secret key
    # CLOUDPAYMENTS_PUBLIC_ID - CloudPayments public ID
    # CLOUDPAYMENTS_API_SECRET - CloudPayments API secret

    # Development mode flag
    DEV_MODE = os.environ.get("FLASK_ENV", "production") == "development"

    # Google Calendar OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.environ.get(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:5000/api/nutritionists/{nutritionist_id}/calendar/callback"
    )


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    
    # Stricter settings for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        "pool_size": 10,
        "max_overflow": 20,
    }


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    # Override to use test database URL if provided, otherwise SQLite in-memory
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", 
        "sqlite:///:memory:"
    )


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
