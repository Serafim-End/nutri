"""
Authentication Routes
Handles Telegram Mini App authentication and JWT token generation.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from pydantic import ValidationError

from app.schemas.auth import TelegramAuthRequest
from app.services.telegram_auth import TelegramAuthService


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/telegram/verify", methods=["POST"])
def verify_telegram():
    """
    Verify Telegram Mini App initData and return JWT token.

    Request:
        POST /api/auth/telegram/verify
        {
            "init_data": "query_id=...&user=...&hash=..."
        }

    Response:
        200: { "access_token": "...", "token_type": "bearer", "profile": {...} }
        400: { "error": "Invalid init_data" }
        401: { "error": "Authentication failed" }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        schema = TelegramAuthRequest(**data)
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    # Verify Telegram signature
    is_valid, user_data = TelegramAuthService.verify_init_data(schema.init_data)

    if not is_valid or not user_data:
        return jsonify({"error": "Invalid or expired initData"}), 401

    # Build full name
    first_name = user_data.get("first_name", "")
    last_name = user_data.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip() or "User"

    # Get or create profile
    profile = TelegramAuthService.get_or_create_profile(
        telegram_user_id=user_data["id"],
        full_name=full_name,
        photo_url=user_data.get("photo_url"),
    )

    # Create JWT token
    access_token = create_access_token(
        identity=str(profile.id),
        additional_claims={
            "role": profile.role,
            "telegram_user_id": profile.telegram_user_id,
        },
    )

    return jsonify({
        "access_token": access_token,
        "token_type": "bearer",
        "profile": profile.to_dict(),
    })


