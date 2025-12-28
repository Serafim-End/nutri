"""
Application Configuration

Handles database connection setup for Supabase PostgreSQL with SSL support.
"""

import os
import sys
import logging
from datetime import timedelta
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

logger = logging.getLogger(__name__)


def _normalize_database_url(url: str | None) -> str:
    """
    Normalize DATABASE_URL for SQLAlchemy compatibility with Supabase.
    
    - Converts 'postgresql://' to 'postgresql+psycopg2://'
    - Ensures sslmode=require is present for Supabase connections
    - Validates URL format
    
    Returns normalized URL string.
    Raises ValueError if URL is missing or invalid.
    """
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Set it to your Supabase PostgreSQL connection string."
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
    
    # Parse existing query parameters
    query_params = parse_qs(parsed.query)
    
    # Check if this is a Supabase connection (contains supabase.co or supabase.com)
    is_supabase = "supabase" in (parsed.hostname or "").lower()
    
    # Ensure sslmode=require for Supabase connections
    if is_supabase or "supabase" in url.lower():
        if "sslmode" not in query_params:
            query_params["sslmode"] = ["require"]
            logger.info("Added sslmode=require for Supabase connection")
    
    # Rebuild query string
    new_query = urlencode({k: v[0] for k, v in query_params.items()})
    
    # Rebuild URL
    normalized = urlunparse((
        scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
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
        
        # Determine if Supabase
        is_supabase = "supabase" in host.lower()
        provider = "Supabase PostgreSQL" if is_supabase else "PostgreSQL"
        
        logger.info(f"Database: {provider} @ {host}:{port}/{database}")
        if is_supabase:
            logger.info("SSL: enabled (sslmode=require)")
    except Exception:
        pass  # Don't fail on logging issues
    
    return normalized_url


class Config:
    """Base configuration class."""

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

    # Database - normalized for Supabase with SSL
    SQLALCHEMY_DATABASE_URI = _get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # Verify connections before use
        "pool_recycle": 300,    # Recycle connections after 5 minutes
        "pool_size": 5,         # Number of connections to keep
        "max_overflow": 10,     # Max additional connections
        "connect_args": {
            "connect_timeout": 10,  # Connection timeout in seconds
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

    # CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

    # Booking Configuration
    SLOT_HOLD_MINUTES = int(os.environ.get("SLOT_HOLD_MINUTES", "10"))
    BOOKING_HOLD_MINUTES = int(os.environ.get("BOOKING_HOLD_MINUTES", "10"))

    # Payment Providers (stubs for now)
    PAYMENT_WEBHOOK_SECRET = os.environ.get("PAYMENT_WEBHOOK_SECRET", "webhook-secret")

    # Development mode flag
    DEV_MODE = os.environ.get("FLASK_ENV", "production") == "development"


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
