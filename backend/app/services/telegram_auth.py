"""
Telegram Authentication Service
Handles verification of Telegram Mini App initData and Bot identity.
"""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qs, unquote
from typing import Optional, Tuple
from flask import current_app

from app.extensions import db
from app.models import Profile


class TelegramAuthService:
    """
    Service for Telegram authentication.
    Verifies initData signature and manages user sessions.
    """

    @staticmethod
    def verify_init_data(init_data: str) -> Tuple[bool, Optional[dict]]:
        """
        Verify Telegram Mini App initData signature.

        Args:
            init_data: The initData string from Telegram WebApp

        Returns:
            Tuple of (is_valid, user_data or None)
        """
        bot_token = current_app.config.get("TELEGRAM_BOT_TOKEN", "")

        if not bot_token:
            # In development, allow bypass with special test data
            if current_app.debug and init_data.startswith("test_"):
                return TelegramAuthService._parse_test_data(init_data)
            current_app.logger.error(
                "TELEGRAM_BOT_TOKEN not set. Real Telegram auth requires the bot token."
            )
            return False, None

        try:
            # Parse the initData
            parsed = parse_qs(init_data)

            # Extract hash
            received_hash = parsed.get("hash", [None])[0]
            if not received_hash:
                return False, None

            # Build data check string (sorted alphabetically, excluding hash)
            data_check_parts = []
            for key, value in sorted(parsed.items()):
                if key != "hash":
                    data_check_parts.append(f"{key}={value[0]}")
            data_check_string = "\n".join(data_check_parts)

            # Compute secret key: HMAC-SHA256(bot_token, "WebAppData")
            secret_key = hmac.new(
                b"WebAppData", bot_token.encode(), hashlib.sha256
            ).digest()

            # Compute hash: HMAC-SHA256(secret_key, data_check_string)
            computed_hash = hmac.new(
                secret_key, data_check_string.encode(), hashlib.sha256
            ).hexdigest()

            # Compare hashes
            if not hmac.compare_digest(computed_hash, received_hash):
                return False, None

            # Check auth_date freshness (allow 24 hours)
            auth_date = int(parsed.get("auth_date", [0])[0])
            if time.time() - auth_date > 86400:
                return False, None

            # Parse user data
            user_data_str = parsed.get("user", [None])[0]
            if not user_data_str:
                return False, None

            user_data = json.loads(unquote(user_data_str))
            return True, user_data

        except Exception as e:
            current_app.logger.error(f"Error verifying initData: {e}")
            return False, None

    @staticmethod
    def _parse_test_data(init_data: str) -> Tuple[bool, Optional[dict]]:
        """
        Parse test data for development.
        Format: test_<telegram_user_id>_<first_name>
        """
        try:
            parts = init_data.split("_")
            if len(parts) >= 3:
                return True, {
                    "id": int(parts[1]),
                    "first_name": parts[2],
                    "last_name": parts[3] if len(parts) > 3 else None,
                }
        except (ValueError, IndexError):
            pass
        return False, None

    @staticmethod
    def get_or_create_profile(
        telegram_user_id: int,
        full_name: str,
        photo_url: Optional[str] = None,
        role: str = "client",
    ) -> Profile:
        """
        Get existing profile or create a new one.

        Args:
            telegram_user_id: Telegram user ID
            full_name: User's full name
            photo_url: Optional photo URL
            role: User role (client/nutritionist/admin)

        Returns:
            Profile instance
        """
        profile = Profile.query.filter_by(telegram_user_id=telegram_user_id).first()

        if profile:
            # Update name and photo if changed
            if profile.full_name != full_name:
                profile.full_name = full_name
            if photo_url and profile.photo_url != photo_url:
                profile.photo_url = photo_url
            db.session.commit()
        else:
            # Create new profile
            profile = Profile(
                telegram_user_id=telegram_user_id,
                full_name=full_name,
                photo_url=photo_url,
                role=role,
            )
            db.session.add(profile)
            db.session.commit()

        return profile


