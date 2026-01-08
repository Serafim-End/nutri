"""
Authentication Routes
Handles Telegram Mini App authentication and JWT token generation.
Includes development-only endpoints for testing without Telegram.
"""

import os
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token
from pydantic import ValidationError

from app.schemas.auth import TelegramAuthRequest
from app.services.telegram_auth import TelegramAuthService
from app.models import Profile


logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


def is_dev_mode() -> bool:
    """Check if running in development mode."""
    flask_env = os.environ.get("FLASK_ENV", "production")
    return flask_env == "development" or current_app.config.get("DEV_MODE", False)


@auth_bp.route("/telegram/verify", methods=["POST"])
def verify_telegram():
    """
    Аутентификация через Telegram Mini App
    ---
    tags:
      - Auth
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/TelegramAuthRequest'
    responses:
      200:
        description: Успешная аутентификация
        schema:
          $ref: '#/definitions/AuthResponse'
      400:
        description: Некорректный запрос
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Неверная или истекшая initData
        schema:
          $ref: '#/definitions/Error'
      500:
        description: TELEGRAM_BOT_TOKEN не настроен
        schema:
          $ref: '#/definitions/Error'
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
        bot_token = current_app.config.get("TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            logger.error("Auth failed: TELEGRAM_BOT_TOKEN not configured")
            return jsonify({
                "error": "Server misconfiguration: TELEGRAM_BOT_TOKEN not set"
            }), 500
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

    logger.info(f"User authenticated: id={profile.id}, telegram_id={profile.telegram_user_id}")

    return jsonify({
        "access_token": access_token,
        "token_type": "bearer",
        "profile": profile.to_dict(),
    })


@auth_bp.route("/dev-login", methods=["POST"])
def dev_login():
    """
    Вход для разработки (без Telegram)
    ---
    tags:
      - Auth
    description: |
      **⚠️ ТОЛЬКО ДЛЯ РАЗРАБОТКИ!**
      
      Возвращает JWT токен для тестового пользователя без верификации Telegram.
      В production этот эндпоинт отключён.
      
      По умолчанию используется telegram_user_id=300000001 (seeded client).
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          $ref: '#/definitions/DevLoginRequest'
    responses:
      200:
        description: Успешный вход
        schema:
          $ref: '#/definitions/AuthResponse'
      403:
        description: Dev login отключён в production
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Пользователь не найден. Запустите make seed
        schema:
          $ref: '#/definitions/Error'
    """
    # SECURITY: Only allow in development mode
    if not is_dev_mode():
        logger.warning("Attempted dev-login in production mode")
        return jsonify({
            "error": "Dev login is disabled in production. Use Telegram authentication."
        }), 403

    data = request.get_json() or {}
    
    # Default to seeded client user (telegram_user_id=300000001)
    telegram_user_id = data.get("telegram_user_id", 300000001)

    # Find existing profile
    profile = Profile.query.filter_by(telegram_user_id=telegram_user_id).first()
    
    if not profile:
        return jsonify({
            "error": f"User with telegram_user_id={telegram_user_id} not found. "
                     "Run 'make seed' to create test users."
        }), 404

    # Create JWT token
    access_token = create_access_token(
        identity=str(profile.id),
        additional_claims={
            "role": profile.role,
            "telegram_user_id": profile.telegram_user_id,
        },
    )

    logger.info(f"Dev login: id={profile.id}, telegram_id={profile.telegram_user_id}")

    return jsonify({
        "access_token": access_token,
        "token_type": "bearer",
        "profile": profile.to_dict(),
    })
