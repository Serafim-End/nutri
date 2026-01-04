"""
Bot Configuration
Handles environment variables and settings.
"""

import os
from dataclasses import dataclass
from typing import Literal


@dataclass
class BotConfig:
    """Bot configuration loaded from environment variables."""
    
    # Telegram Bot
    bot_token: str
    
    # Backend API
    backend_url: str
    service_token: str
    
    # Mode: polling (dev) or webhook (prod)
    mode: Literal["polling", "webhook"]
    webhook_url: str | None
    webhook_path: str
    webhook_host: str
    webhook_port: int
    
    # Database for FSM state storage
    database_url: str
    
    # Mini App URL
    webapp_url: str
    
    # Logging
    log_level: str
    
    @classmethod
    def from_env(cls) -> "BotConfig":
        """Load configuration from environment variables."""
        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        backend_url = os.environ.get("BACKEND_URL", "http://localhost:5000")
        service_token = os.environ.get("BOT_SERVICE_TOKEN", "")
        if not service_token:
            raise ValueError("BOT_SERVICE_TOKEN environment variable is required")
        
        mode = os.environ.get("TELEGRAM_MODE", "polling")
        if mode not in ("polling", "webhook"):
            raise ValueError("TELEGRAM_MODE must be 'polling' or 'webhook'")
        
        webhook_url = os.environ.get("WEBHOOK_URL")
        webhook_path = os.environ.get("WEBHOOK_PATH", "/webhook")
        webhook_host = os.environ.get("WEBHOOK_HOST", "0.0.0.0")
        webhook_port = int(os.environ.get("WEBHOOK_PORT", "8443"))
        
        database_url = os.environ.get("DATABASE_URL", "")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        webapp_url = os.environ.get("WEBAPP_URL", "https://t.me/your_bot/app")
        log_level = os.environ.get("LOG_LEVEL", "INFO")
        
        return cls(
            bot_token=bot_token,
            backend_url=backend_url.rstrip("/"),
            service_token=service_token,
            mode=mode,
            webhook_url=webhook_url,
            webhook_path=webhook_path,
            webhook_host=webhook_host,
            webhook_port=webhook_port,
            database_url=database_url,
            webapp_url=webapp_url,
            log_level=log_level,
        )


# Global config instance (lazy loaded)
_config: BotConfig | None = None


def get_config() -> BotConfig:
    """Get or create bot configuration."""
    global _config
    if _config is None:
        _config = BotConfig.from_env()
    return _config

