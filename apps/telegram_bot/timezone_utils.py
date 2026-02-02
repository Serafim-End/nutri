"""
Timezone helpers for Telegram bot.
All user-facing times should be displayed in Moscow time.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def now_moscow() -> datetime:
    """Current datetime in Moscow timezone."""
    return datetime.now(MOSCOW_TZ)


def to_moscow(value: datetime) -> datetime:
    """
    Convert datetime to Moscow timezone.
    If datetime is naive, treat it as UTC.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(MOSCOW_TZ)
