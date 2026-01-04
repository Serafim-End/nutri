"""
Bot API Routes
Endpoints for Telegram bot integration.
Protected by service token authentication.
"""

import os
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models import Profile, NutritionistProfile, Service, Booking


logger = logging.getLogger(__name__)
bot_bp = Blueprint("bot", __name__)


def require_service_token(f):
    """
    Decorator to require valid service token.
    Token is passed via X-Service-Token header.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Service-Token")
        expected_token = os.environ.get("BOT_SERVICE_TOKEN", "")
        
        if not expected_token:
            logger.warning("BOT_SERVICE_TOKEN not configured")
            return jsonify({"error": "Service not configured"}), 503
        
        if not token or token != expected_token:
            logger.warning(f"Invalid service token attempt")
            return jsonify({"error": "Invalid service token"}), 401
        
        return f(*args, **kwargs)
    
    return decorated


@bot_bp.route("/resolve-telegram-user", methods=["GET"])
@require_service_token
def resolve_telegram_user():
    """
    Resolve Telegram user to get profile and role.
    Used by bot to determine user state on /start.
    
    Request:
        GET /api/bot/resolve-telegram-user?telegram_user_id=123
        X-Service-Token: <token>
    
    Response:
        200: {
            "profile": {...} or null,
            "nutritionist": {...} or null,
            "role": "client" | "nutritionist" | "admin"
        }
    """
    telegram_user_id = request.args.get("telegram_user_id", type=int)
    
    if not telegram_user_id:
        return jsonify({"error": "telegram_user_id required"}), 400
    
    # Find profile
    profile = Profile.query.filter_by(telegram_user_id=telegram_user_id).first()
    
    if not profile:
        return jsonify({
            "profile": None,
            "nutritionist": None,
            "role": "client",
        })
    
    # Check if nutritionist
    nutritionist = None
    if profile.role == "nutritionist":
        nutritionist_profile = NutritionistProfile.query.get(profile.id)
        if nutritionist_profile:
            nutritionist = nutritionist_profile.to_dict(include_profile=True)
    
    return jsonify({
        "profile": profile.to_dict(),
        "nutritionist": nutritionist,
        "role": profile.role,
    })


@bot_bp.route("/nutritionists/<nutritionist_id>/services", methods=["GET"])
@require_service_token
def list_nutritionist_services(nutritionist_id: str):
    """
    List nutritionist's services.
    
    Request:
        GET /api/bot/nutritionists/<id>/services
        X-Service-Token: <token>
    
    Response:
        200: { "services": [...] }
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404
    
    services = Service.query.filter_by(nutritionist_id=nutritionist_id).all()
    
    return jsonify({
        "services": [s.to_dict() for s in services],
    })


@bot_bp.route("/nutritionists/<nutritionist_id>/services/<service_id>", methods=["PUT"])
@require_service_token
def update_service(nutritionist_id: str, service_id: str):
    """
    Update a service.
    
    Request:
        PUT /api/bot/nutritionists/<id>/services/<service_id>
        X-Service-Token: <token>
        {
            "title": "...",
            "description": "...",
            "duration_minutes": 60,
            "price_rub": 3000,
            "is_active": true
        }
    
    Response:
        200: { "service": {...} }
    """
    service = Service.query.get(service_id)
    
    if not service:
        return jsonify({"error": "Service not found"}), 404
    
    if str(service.nutritionist_id) != nutritionist_id:
        return jsonify({"error": "Service does not belong to this nutritionist"}), 403
    
    data = request.get_json() or {}
    
    if "title" in data:
        service.title = data["title"]
    if "description" in data:
        service.description = data["description"]
    if "duration_minutes" in data:
        service.duration_minutes = data["duration_minutes"]
    if "price_rub" in data:
        service.price_rub = data["price_rub"]
    if "is_active" in data:
        service.is_active = data["is_active"]
    
    db.session.commit()
    
    return jsonify({"service": service.to_dict()})


@bot_bp.route("/nutritionists/<nutritionist_id>/services/<service_id>", methods=["DELETE"])
@require_service_token
def delete_service(nutritionist_id: str, service_id: str):
    """
    Delete a service.
    
    Request:
        DELETE /api/bot/nutritionists/<id>/services/<service_id>
        X-Service-Token: <token>
    
    Response:
        200: { "message": "Service deleted" }
    """
    service = Service.query.get(service_id)
    
    if not service:
        return jsonify({"error": "Service not found"}), 404
    
    if str(service.nutritionist_id) != nutritionist_id:
        return jsonify({"error": "Service does not belong to this nutritionist"}), 403
    
    db.session.delete(service)
    db.session.commit()
    
    return jsonify({"message": "Service deleted"})


@bot_bp.route("/nutritionists/<nutritionist_id>/calendar/status", methods=["GET"])
@require_service_token
def get_calendar_status(nutritionist_id: str):
    """
    Get calendar connection status.
    
    Request:
        GET /api/bot/nutritionists/<id>/calendar/status
        X-Service-Token: <token>
    
    Response:
        200: { "connected": false, "email": null }
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404
    
    # TODO: Implement actual calendar integration
    # For now, return not connected
    return jsonify({
        "connected": False,
        "email": None,
    })


@bot_bp.route("/nutritionists/<nutritionist_id>/calendar/oauth-url", methods=["GET"])
@require_service_token
def get_calendar_oauth_url(nutritionist_id: str):
    """
    Get Google OAuth URL for calendar connection.
    
    Request:
        GET /api/bot/nutritionists/<id>/calendar/oauth-url
        X-Service-Token: <token>
    
    Response:
        200: { "url": "https://..." }
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404
    
    # TODO: Implement actual Google OAuth
    # For now, return placeholder
    return jsonify({
        "url": None,
        "message": "Calendar integration coming soon",
    })


@bot_bp.route("/nutritionists/<nutritionist_id>/reviews", methods=["GET"])
@require_service_token
def get_reviews(nutritionist_id: str):
    """
    Get nutritionist reviews.
    
    Request:
        GET /api/bot/nutritionists/<id>/reviews?limit=5&offset=0
        X-Service-Token: <token>
    
    Response:
        200: { "reviews": [...], "total": 10 }
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404
    
    limit = request.args.get("limit", 5, type=int)
    offset = request.args.get("offset", 0, type=int)
    
    # TODO: Implement reviews model
    # For now, return empty list
    return jsonify({
        "reviews": [],
        "total": 0,
    })


@bot_bp.route("/nutritionists/<nutritionist_id>/statistics", methods=["GET"])
@require_service_token
def get_statistics(nutritionist_id: str):
    """
    Get nutritionist statistics.
    
    Request:
        GET /api/bot/nutritionists/<id>/statistics?days=30
        X-Service-Token: <token>
    
    Response:
        200: {
            "income_30d": 50000,
            "consultations_30d": 15,
            "avg_rating": 4.8,
            "total_clients": 25
        }
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404
    
    days = request.args.get("days", 30, type=int)
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Calculate statistics from bookings
    bookings = Booking.query.filter(
        Booking.nutritionist_id == nutritionist_id,
        Booking.created_at >= since_date,
    ).all()
    
    # Income from paid/completed bookings
    paid_bookings = [b for b in bookings if b.status in ("paid", "completed")]
    income = sum(b.price_rub for b in paid_bookings)
    
    # Completed consultations
    completed = len([b for b in bookings if b.status == "completed"])
    
    # Unique clients
    client_ids = set(b.client_id for b in bookings if b.client_id)
    
    return jsonify({
        "income_30d": income,
        "consultations_30d": completed,
        "avg_rating": float(nutritionist.rating) if nutritionist.rating else 0.0,
        "total_clients": len(client_ids),
    })


@bot_bp.route("/nutritionists/<nutritionist_id>/upload-photo", methods=["POST"])
@require_service_token
def upload_photo(nutritionist_id: str):
    """
    Upload photo for nutritionist profile.
    
    Request:
        POST /api/bot/nutritionists/<id>/upload-photo
        X-Service-Token: <token>
        Content-Type: multipart/form-data
        photo: <file>
    
    Response:
        200: { "photo_url": "https://..." }
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404
    
    if "photo" not in request.files:
        return jsonify({"error": "No photo provided"}), 400
    
    photo = request.files["photo"]
    
    # TODO: Implement actual file storage (S3, local, etc.)
    # For now, return placeholder URL
    
    # In production, you would:
    # 1. Validate file type and size
    # 2. Upload to storage (S3, GCS, etc.)
    # 3. Return the public URL
    
    # Placeholder implementation
    photo_url = f"https://storage.example.com/photos/{nutritionist_id}/{photo.filename}"
    
    # Update profile
    if nutritionist.profile:
        nutritionist.profile.photo_url = photo_url
        db.session.commit()
    
    return jsonify({
        "photo_url": photo_url,
        "message": "Photo uploaded (placeholder)",
    })


@bot_bp.route("/support/messages", methods=["POST"])
@require_service_token
def create_support_message():
    """
    Create support message.
    
    Request:
        POST /api/bot/support/messages
        X-Service-Token: <token>
        {
            "telegram_user_id": 123,
            "message": "Help needed..."
        }
    
    Response:
        201: { "message": "Support request received" }
    """
    data = request.get_json() or {}
    
    telegram_user_id = data.get("telegram_user_id")
    message = data.get("message", "")
    
    if not telegram_user_id or not message:
        return jsonify({"error": "telegram_user_id and message required"}), 400
    
    # TODO: Implement support ticket system
    # For now, just log the message
    logger.info(
        f"Support message from user {telegram_user_id}: {message[:200]}"
    )
    
    return jsonify({
        "message": "Support request received",
        "ticket_id": None,  # Would be real ticket ID
    }), 201

