"""
Bot API Routes
Endpoints for Telegram bot integration.
Protected by service token authentication.
"""

import os
import logging
from functools import wraps
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from app.extensions import db
from app.models import Profile, NutritionistProfile, Service, Booking, AvailabilitySlot, GoogleCalendar
from app.schemas.nutritionist import SlotCreateRequest


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
    Определить пользователя Telegram
    ---
    tags:
      - Bot
    description: |
      Определяет профиль и роль пользователя по telegram_user_id.
      Используется ботом для определения состояния на /start.
      
      **Требуется заголовок:** `X-Service-Token`
    produces:
      - application/json
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        type: string
        description: Сервисный токен бота
      - name: telegram_user_id
        in: query
        required: true
        type: integer
        description: Telegram User ID
    responses:
      200:
        description: Данные пользователя
        schema:
          type: object
          properties:
            profile:
              $ref: '#/definitions/Profile'
            nutritionist:
              $ref: '#/definitions/Nutritionist'
            role:
              type: string
              enum: [client, nutritionist, admin]
      400:
        description: telegram_user_id не указан
      401:
        description: Неверный сервисный токен
      503:
        description: BOT_SERVICE_TOKEN не настроен
    """
    telegram_user_id = request.args.get("telegram_user_id", type=int)
    telegram_username = request.args.get("telegram_username")
    full_name = request.args.get("full_name")
    
    if not telegram_user_id:
        return jsonify({"error": "telegram_user_id required"}), 400
    
    # Find or create profile
    profile = Profile.query.filter_by(telegram_user_id=telegram_user_id).first()
    
    if not profile:
        profile = Profile(
            telegram_user_id=telegram_user_id,
            full_name=full_name or "User",
            telegram_username=telegram_username,
            role="client",
        )
        db.session.add(profile)
        db.session.flush()

    now = datetime.utcnow()
    if telegram_username and profile.telegram_username != telegram_username:
        profile.telegram_username = telegram_username
    if full_name and profile.full_name != full_name:
        profile.full_name = full_name
    if not profile.first_bot_start_at:
        profile.first_bot_start_at = now
    profile.last_bot_start_at = now
    db.session.commit()
    
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
    
    calendar = GoogleCalendar.query.filter_by(nutritionist_id=nutritionist_id).first()
    if not calendar or not calendar.is_connected:
        return jsonify({
            "connected": False,
            "email": None,
            "selected_calendar_id": None,
            "selected_calendar_summary": None,
        })

    return jsonify({
        "connected": True,
        "email": calendar.selected_calendar_summary,
        "selected_calendar_id": calendar.selected_calendar_id,
        "selected_calendar_summary": calendar.selected_calendar_summary,
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
    
    try:
        from app.services.google_calendar import GoogleCalendarService
        authorization_url = GoogleCalendarService.get_authorization_url(nutritionist_id)
        return jsonify({"url": authorization_url})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


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
    Статистика нутрициолога
    ---
    tags:
      - Bot
    description: |
      Возвращает статистику нутрициолога за указанный период.
      
      **Требуется заголовок:** `X-Service-Token`
    produces:
      - application/json
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        type: string
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - name: days
        in: query
        type: integer
        default: 30
        description: Период в днях
    responses:
      200:
        description: Статистика
        schema:
          type: object
          properties:
            income_30d:
              type: integer
              example: 50000
            consultations_30d:
              type: integer
              example: 15
            avg_rating:
              type: number
              format: float
              example: 4.8
            total_clients:
              type: integer
              example: 25
      401:
        description: Неверный сервисный токен
      404:
        description: Нутрициолог не найден
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


# ==========================================
# Slot Management (Manual slots are PRIMARY)
# ==========================================

def check_slot_overlap(nutritionist_id: str, start_at: datetime, end_at: datetime, exclude_slot_id: str = None) -> bool:
    """
    Check if a slot overlaps with existing slots.
    Returns True if there's an overlap.
    """
    query = AvailabilitySlot.query.filter(
        AvailabilitySlot.nutritionist_id == nutritionist_id,
        AvailabilitySlot.status.in_(["free", "held", "booked"]),
        # Overlap check: new slot starts before existing ends AND new slot ends after existing starts
        AvailabilitySlot.start_at < end_at,
        AvailabilitySlot.end_at > start_at,
    )
    
    if exclude_slot_id:
        query = query.filter(AvailabilitySlot.id != exclude_slot_id)
    
    return query.first() is not None


@bot_bp.route("/nutritionists/<nutritionist_id>/slots", methods=["POST"])
@require_service_token
def create_slot(nutritionist_id: str):
    """
    Создать слот доступности
    ---
    tags:
      - Bot
    description: |
      Создаёт новый слот доступности для нутрициолога.
      Слот создаётся с source=manual и status=free.
      
      **Требуется заголовок:** `X-Service-Token`
      
      **Валидация:**
      - start_at < end_at
      - start_at в будущем
      - Нет пересечений с существующими слотами
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        type: string
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - start_at
            - end_at
          properties:
            start_at:
              type: string
              format: date-time
              example: "2024-01-15T12:00:00+00:00"
            end_at:
              type: string
              format: date-time
              example: "2024-01-15T13:00:00+00:00"
    responses:
      201:
        description: Слот создан
        schema:
          type: object
          properties:
            slot:
              $ref: '#/definitions/Slot'
      400:
        description: Ошибка валидации
      404:
        description: Нутрициолог не найден
      409:
        description: Слот пересекается с существующим
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Нутрициолог не найден"}), 404
    
    try:
        data = request.get_json() or {}
        schema = SlotCreateRequest(**data)
    except ValidationError as e:
        # Extract user-friendly error messages
        errors = e.errors()
        if errors:
            first_error = errors[0]
            msg = first_error.get("msg", "Ошибка валидации")
            if "future" in msg.lower():
                return jsonify({"error": "Слот должен быть в будущем"}), 400
            if "after" in msg.lower():
                return jsonify({"error": "Время окончания должно быть после времени начала"}), 400
        return jsonify({"error": "Ошибка валидации данных", "details": errors}), 400
    
    # Check for overlapping slots
    if check_slot_overlap(nutritionist_id, schema.start_at, schema.end_at):
        return jsonify({
            "error": "Этот слот пересекается с существующим. Выберите другое время."
        }), 409
    
    # Create slot
    slot = AvailabilitySlot(
        nutritionist_id=nutritionist_id,
        start_at=schema.start_at,
        end_at=schema.end_at,
        status="free",
        source="manual",
    )
    
    db.session.add(slot)
    db.session.commit()
    
    logger.info(f"Slot created: {slot.id} for nutritionist {nutritionist_id}")
    
    return jsonify({"slot": slot.to_dict()}), 201


@bot_bp.route("/nutritionists/<nutritionist_id>/slots", methods=["GET"])
@require_service_token
def list_slots(nutritionist_id: str):
    """
    Получить слоты нутрициолога
    ---
    tags:
      - Bot
    description: |
      Возвращает слоты нутрициолога в заданном диапазоне дат.
      По умолчанию: от сейчас до +14 дней.
      
      **Требуется заголовок:** `X-Service-Token`
    produces:
      - application/json
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        type: string
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - name: from
        in: query
        type: string
        format: date-time
        description: Начало диапазона (по умолчанию - сейчас)
      - name: to
        in: query
        type: string
        format: date-time
        description: Конец диапазона (по умолчанию - +14 дней)
    responses:
      200:
        description: Список слотов
        schema:
          type: object
          properties:
            slots:
              type: array
              items:
                $ref: '#/definitions/Slot'
            total:
              type: integer
      404:
        description: Нутрициолог не найден
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Нутрициолог не найден"}), 404
    
    # Parse date range
    now = datetime.now(timezone.utc)
    
    from_str = request.args.get("from")
    to_str = request.args.get("to")
    
    if from_str:
        try:
            from_date = datetime.fromisoformat(from_str.replace('Z', '+00:00'))
        except ValueError:
            from_date = now
    else:
        from_date = now
    
    if to_str:
        try:
            to_date = datetime.fromisoformat(to_str.replace('Z', '+00:00'))
        except ValueError:
            to_date = now + timedelta(days=14)
    else:
        to_date = now + timedelta(days=14)
    
    # Query slots
    slots = AvailabilitySlot.query.filter(
        AvailabilitySlot.nutritionist_id == nutritionist_id,
        AvailabilitySlot.start_at >= from_date,
        AvailabilitySlot.start_at <= to_date,
        AvailabilitySlot.status.in_(["free", "held", "booked"]),  # Exclude cancelled
    ).order_by(AvailabilitySlot.start_at).all()
    
    return jsonify({
        "slots": [s.to_dict() for s in slots],
        "total": len(slots),
    })


@bot_bp.route("/nutritionists/<nutritionist_id>/slots/<slot_id>", methods=["DELETE"])
@require_service_token
def delete_slot(nutritionist_id: str, slot_id: str):
    """
    Удалить слот доступности
    ---
    tags:
      - Bot
    description: |
      Удаляет слот доступности.
      Можно удалить только слоты со статусом 'free'.
      
      **Требуется заголовок:** `X-Service-Token`
    produces:
      - application/json
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        type: string
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - name: slot_id
        in: path
        required: true
        type: string
        description: UUID слота
    responses:
      200:
        description: Слот удалён
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Слот удалён"
      400:
        description: Слот нельзя удалить (не свободен)
      404:
        description: Слот не найден
    """
    slot = AvailabilitySlot.query.get(slot_id)
    
    if not slot:
        return jsonify({"error": "Слот не найден"}), 404
    
    if str(slot.nutritionist_id) != nutritionist_id:
        return jsonify({"error": "Слот не принадлежит этому нутрициологу"}), 403
    
    if slot.status != "free":
        return jsonify({
            "error": "Слот уже используется и не может быть удалён"
        }), 400
    
    # Delete the slot
    db.session.delete(slot)
    db.session.commit()
    
    logger.info(f"Slot deleted: {slot_id} by nutritionist {nutritionist_id}")
    
    return jsonify({"message": "Слот удалён"})


# ==========================================
# Nutritionist Bookings (read-only)
# ==========================================

@bot_bp.route("/nutritionists/<nutritionist_id>/bookings", methods=["GET"])
@require_service_token
def get_nutritionist_bookings(nutritionist_id: str):
    """
    Получить бронирования нутрициолога
    ---
    tags:
      - Bot
    description: |
      Возвращает предстоящие бронирования нутрициолога.
      Включает данные о клиенте и услуге.
      
      **Требуется заголовок:** `X-Service-Token`
    produces:
      - application/json
    parameters:
      - name: X-Service-Token
        in: header
        required: true
        type: string
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - name: limit
        in: query
        type: integer
        default: 20
        description: Максимальное количество
      - name: offset
        in: query
        type: integer
        default: 0
        description: Смещение для пагинации
    responses:
      200:
        description: Список бронирований
        schema:
          type: object
          properties:
            bookings:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  client_name:
                    type: string
                  service_title:
                    type: string
                  start_at:
                    type: string
                  end_at:
                    type: string
                  status:
                    type: string
            total:
              type: integer
      404:
        description: Нутрициолог не найден
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Нутрициолог не найден"}), 404
    
    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)
    now = datetime.now(timezone.utc)
    
    # Get upcoming bookings with paid status
    bookings_query = Booking.query.filter(
        Booking.nutritionist_id == nutritionist_id,
        Booking.status.in_(["paid", "completed"]),
    ).order_by(Booking.created_at.desc())
    
    total = bookings_query.count()
    bookings = bookings_query.offset(offset).limit(limit).all()
    
    result = []
    for booking in bookings:
        # Get slot info
        slot = booking.slot
        if not slot:
            continue
        
        # Only include upcoming bookings
        if slot.start_at < now and booking.status != "completed":
            continue
        
        # Get client info
        client = Profile.query.get(booking.client_id) if booking.client_id else None
        client_name = client.full_name if client else "Клиент"
        
        # Get service info
        service = Service.query.get(booking.service_id) if booking.service_id else None
        service_title = service.title if service else "Консультация"
        
        result.append({
            "id": str(booking.id),
            "client_name": client_name,
            "service_title": service_title,
            "start_at": slot.start_at.isoformat(),
            "end_at": slot.end_at.isoformat(),
            "status": booking.status,
            "price_rub": booking.price_rub,
            "meeting_link": booking.meeting_link,
        })
    
    return jsonify({
        "bookings": result,
        "total": len(result),
    })
