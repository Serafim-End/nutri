"""
Timezone utilities.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

try:
    from flask import current_app
except Exception:  # pragma: no cover - flask may not be available in some contexts
    current_app = None


def _get_timezone_name() -> str:
    if current_app is not None:
        try:
            return current_app.config.get("DEFAULT_TIMEZONE", "UTC")
        except RuntimeError:
            # Outside application context
            pass
    return os.environ.get("DEFAULT_TIMEZONE", "UTC")


def get_default_tzinfo() -> timezone | ZoneInfo:
    """Return configured timezone, fallback to UTC on errors."""
    tz_name = _get_timezone_name()
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return timezone.utc


def normalize_to_utc(value: datetime) -> datetime:
    """Ensure datetime is timezone-aware and converted to UTC."""
    tzinfo = get_default_tzinfo()
    if value.tzinfo is None:
        value = value.replace(tzinfo=tzinfo)
    return value.astimezone(timezone.utc)
