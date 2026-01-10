"""
Nutritionist Routes
Handles nutritionist profile management (for Botpress integration).
"""

from datetime import datetime, date
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from pydantic import ValidationError

from app.extensions import db
from app.models import (
    Profile,
    NutritionistProfile,
    Service,
    AvailabilitySlot,
    NutritionistDocument,
    Booking,
    WorkingHoursTemplate,
    DateException,
    Review,
)
from app.models.google_calendar import GoogleCalendar
from app.schemas.nutritionist import (
    NutritionistUpsertRequest,
    DocumentUploadRequest,
    ServiceCreateRequest,
    BulkSlotCreateRequest,
    WorkingHoursTemplateUpdateRequest,
    DateExceptionCreateRequest,
    DateExceptionUpdateRequest,
    TimeRange,
)


nutritionists_bp = Blueprint("nutritionists", __name__)


def require_nutritionist_or_admin(nutritionist_id: str):
    """Check if current user can modify nutritionist data."""
    claims = get_jwt()
    current_user_id = get_jwt_identity()
    role = claims.get("role", "client")

    if role == "admin":
        return True, None

    if role == "nutritionist" and current_user_id == nutritionist_id:
        return True, None

    return False, jsonify({"error": "Not authorized"}), 403


@nutritionists_bp.route("/upsert", methods=["POST"])
def upsert_nutritionist():
    """
    Создать или обновить профиль нутрициолога
    ---
    tags:
      - Nutritionists
    description: |
      Создаёт новый или обновляет существующий профиль нутрициолога.
      Используется Botpress для онбординга нутрициологов.
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/NutritionistUpsertRequest'
    responses:
      200:
        description: Профиль создан/обновлён
        schema:
          type: object
          properties:
            nutritionist:
              $ref: '#/definitions/Nutritionist'
            is_new:
              type: boolean
              description: true если это новый профиль
      400:
        description: Ошибка валидации
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        data = request.get_json() or {}
        schema = NutritionistUpsertRequest(**data)
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    # Check if profile exists
    profile = Profile.query.filter_by(
        telegram_user_id=schema.telegram_user_id
    ).first()

    is_new = False

    if not profile:
        # Create new profile
        profile = Profile(
            telegram_user_id=schema.telegram_user_id,
            full_name=schema.full_name,
            photo_url=schema.photo_url,
            role="nutritionist",
            telegram_username=schema.telegram_username,
        )
        db.session.add(profile)
        db.session.flush()
        is_new = True
    else:
        # Update existing profile
        profile.full_name = schema.full_name
        if schema.photo_url:
            profile.photo_url = schema.photo_url
        if schema.telegram_username:
            profile.telegram_username = schema.telegram_username
        if profile.role != "nutritionist":
            profile.role = "nutritionist"
    if schema.nutritionist_intent:
        now = datetime.utcnow()
        if not profile.first_nutritionist_intent_at:
            profile.first_nutritionist_intent_at = now
        profile.last_nutritionist_intent_at = now

    # Get or create nutritionist profile
    nutritionist = NutritionistProfile.query.get(profile.id)
    if not nutritionist:
        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
            verification_status="draft",
        )
        db.session.add(nutritionist)
        is_new = True

    # Update nutritionist fields
    if schema.bio is not None:
        nutritionist.bio = schema.bio
    if schema.tags:
        nutritionist.tags = schema.tags
    if schema.specializations:
        nutritionist.specializations = schema.specializations

    # Submit for verification if requested
    if schema.submit_for_verification:
        if nutritionist.verification_status in ("draft", "needs_update"):
            nutritionist.verification_status = "pending"
            nutritionist.submitted_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "nutritionist": nutritionist.to_dict(include_profile=True),
        "is_new": is_new,
    })


@nutritionists_bp.route("/<nutritionist_id>/documents", methods=["POST"])
@jwt_required(optional=True)
def upload_document(nutritionist_id: str):
    """
    Добавить документ нутрициолога
    ---
    tags:
      - Nutritionists
    description: Добавляет метаданные документа для верификации нутрициолога
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/DocumentCreateRequest'
    responses:
      201:
        description: Документ добавлен
        schema:
          type: object
          properties:
            document:
              $ref: '#/definitions/Document'
      400:
        description: Ошибка валидации
      404:
        description: Нутрициолог не найден
    """
    try:
        data = request.get_json() or {}
        schema = DocumentUploadRequest(**data)
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    # Verify nutritionist exists
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    # Create document record
    document = NutritionistDocument(
        nutritionist_id=nutritionist_id,
        type=schema.type,
        file_path=schema.file_path,
        status="uploaded",
    )

    db.session.add(document)
    db.session.commit()

    return jsonify({"document": document.to_dict()}), 201


@nutritionists_bp.route("/<nutritionist_id>/services", methods=["POST"])
@jwt_required(optional=True)
def create_service(nutritionist_id: str):
    """
    Создать услугу нутрициолога
    ---
    tags:
      - Nutritionists
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/ServiceCreateRequest'
    responses:
      201:
        description: Услуга создана
        schema:
          type: object
          properties:
            service:
              $ref: '#/definitions/Service'
      400:
        description: Ошибка валидации
      404:
        description: Нутрициолог не найден
    """
    try:
        data = request.get_json() or {}
        schema = ServiceCreateRequest(**data)
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    # Verify nutritionist exists
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    # Create service
    service = Service(
        nutritionist_id=nutritionist_id,
        title=schema.title,
        description=schema.description,
        duration_minutes=schema.duration_minutes,
        price_rub=schema.price_rub,
        is_active=schema.is_active,
    )

    db.session.add(service)
    db.session.commit()

    return jsonify({"service": service.to_dict()}), 201


@nutritionists_bp.route("/<nutritionist_id>/slots", methods=["POST"])
@jwt_required(optional=True)
def create_slots(nutritionist_id: str):
    """
    Создать слоты доступности (массово)
    ---
    tags:
      - Nutritionists
    description: Массовое создание слотов доступности для нутрициолога
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/SlotCreateRequest'
    responses:
      201:
        description: Слоты созданы
        schema:
          type: object
          properties:
            slots:
              type: array
              items:
                $ref: '#/definitions/Slot'
            created_count:
              type: integer
              example: 2
      400:
        description: Ошибка валидации
      404:
        description: Нутрициолог не найден
    """
    try:
        data = request.get_json() or {}
        schema = BulkSlotCreateRequest(**data)
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    # Verify nutritionist exists
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    created_slots = []
    for slot_data in schema.slots:
        slot = AvailabilitySlot(
            nutritionist_id=nutritionist_id,
            start_at=slot_data.start_at,
            end_at=slot_data.end_at,
            status="free",
        )
        db.session.add(slot)
        created_slots.append(slot)

    db.session.commit()

    return jsonify({
        "slots": [s.to_dict() for s in created_slots],
        "created_count": len(created_slots),
    }), 201


@nutritionists_bp.route("/<nutritionist_id>/dashboard", methods=["GET"])
@jwt_required(optional=True)
def get_dashboard(nutritionist_id: str):
    """
    Дашборд нутрициолога
    ---
    tags:
      - Nutritionists
    description: Возвращает профиль, услуги, ближайшие слоты и статистику
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
    responses:
      200:
        description: Данные дашборда
        schema:
          type: object
          properties:
            nutritionist:
              $ref: '#/definitions/Nutritionist'
            services:
              type: array
              items:
                $ref: '#/definitions/Service'
            upcoming_slots:
              type: array
              items:
                $ref: '#/definitions/Slot'
            stats:
              type: object
              properties:
                total_bookings:
                  type: integer
                completed_bookings:
                  type: integer
                total_earnings_rub:
                  type: integer
      404:
        description: Нутрициолог не найден
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    # Get services
    services = Service.query.filter_by(
        nutritionist_id=nutritionist_id
    ).all()

    # Get upcoming slots
    upcoming_slots = AvailabilitySlot.query.filter(
        AvailabilitySlot.nutritionist_id == nutritionist_id,
        AvailabilitySlot.start_at > datetime.utcnow(),
        AvailabilitySlot.status.in_(["free", "booked"]),
    ).order_by(AvailabilitySlot.start_at).limit(20).all()

    # Calculate stats
    bookings = Booking.query.filter_by(nutritionist_id=nutritionist_id).all()
    total_bookings = len(bookings)
    completed_bookings = len([b for b in bookings if b.status == "completed"])
    paid_bookings = [b for b in bookings if b.status in ("paid", "completed")]
    total_earnings = sum(b.price_rub for b in paid_bookings)

    return jsonify({
        "nutritionist": nutritionist.to_dict(include_profile=True),
        "services": [s.to_dict() for s in services],
        "upcoming_slots": [s.to_dict() for s in upcoming_slots],
        "stats": {
            "total_bookings": total_bookings,
            "completed_bookings": completed_bookings,
            "total_earnings_rub": total_earnings,
        },
    })


# ==========================================
# Working Hours Template Endpoints
# ==========================================

@nutritionists_bp.route("/<nutritionist_id>/working-hours-template", methods=["GET"])
@jwt_required(optional=True)
def get_working_hours_template(nutritionist_id: str):
    """
    Получить шаблон рабочих часов
    ---
    tags:
      - Nutritionists
    description: |
      Возвращает шаблон рабочих часов нутрициолога.
      Используется в Calendar Settings (UX_MAP screen 17).
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
    responses:
      200:
        description: Шаблон рабочих часов
        schema:
          type: object
          properties:
            template:
              $ref: '#/definitions/WorkingHoursTemplate'
      404:
        description: Нутрициолог не найден
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    template = WorkingHoursTemplate.query.filter_by(
        nutritionist_id=nutritionist_id
    ).first()

    if not template:
        # Return empty template
        return jsonify({
            "template": {
                "id": None,
                "nutritionist_id": nutritionist_id,
                "weekly_schedule": {},
                "created_at": None,
                "updated_at": None,
            }
        })

    return jsonify({"template": template.to_dict()})


@nutritionists_bp.route("/<nutritionist_id>/working-hours-template", methods=["PUT"])
@jwt_required(optional=True)
def update_working_hours_template(nutritionist_id: str):
    """
    Создать или обновить шаблон рабочих часов
    ---
    tags:
      - Nutritionists
    description: |
      Создаёт или обновляет шаблон рабочих часов нутрициолога.
      Используется в Calendar Settings (UX_MAP screen 17).
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/WorkingHoursTemplateUpdateRequest'
    responses:
      200:
        description: Шаблон создан/обновлён
        schema:
          type: object
          properties:
            template:
              $ref: '#/definitions/WorkingHoursTemplate'
      400:
        description: Ошибка валидации
      404:
        description: Нутрициолог не найден
    """
    try:
        data = request.get_json() or {}
        schema = WorkingHoursTemplateUpdateRequest(**data)
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    # Verify nutritionist exists
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    # Convert TimeRange objects to dicts for JSONB storage
    weekly_schedule = {}
    for day, time_ranges in schema.weekly_schedule.items():
        weekly_schedule[str(day)] = [
            {"start": tr.start, "end": tr.end} for tr in time_ranges
        ]

    # Get or create template
    template = WorkingHoursTemplate.query.filter_by(
        nutritionist_id=nutritionist_id
    ).first()

    if not template:
        template = WorkingHoursTemplate(
            nutritionist_id=nutritionist_id,
            weekly_schedule=weekly_schedule,
        )
        db.session.add(template)
    else:
        template.weekly_schedule = weekly_schedule

    db.session.commit()

    return jsonify({"template": template.to_dict()})


# ==========================================
# Date Exceptions Endpoints
# ==========================================

@nutritionists_bp.route("/<nutritionist_id>/date-exceptions", methods=["GET"])
@jwt_required(optional=True)
def list_date_exceptions(nutritionist_id: str):
    """
    Получить список исключений по датам
    ---
    tags:
      - Nutritionists
    description: |
      Возвращает список исключений для рабочих часов по датам.
      Используется в Calendar Settings (UX_MAP screen 17).
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - name: start_date
        in: query
        type: string
        format: date
        description: Начальная дата для фильтрации (опционально)
      - name: end_date
        in: query
        type: string
        format: date
        description: Конечная дата для фильтрации (опционально)
    responses:
      200:
        description: Список исключений
        schema:
          type: object
          properties:
            exceptions:
              type: array
              items:
                $ref: '#/definitions/DateException'
            total:
              type: integer
      404:
        description: Нутрициолог не найден
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    query = DateException.query.filter_by(nutritionist_id=nutritionist_id)

    # Optional date filtering
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(DateException.exception_date >= start_date_obj)
        except ValueError:
            return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(DateException.exception_date <= end_date_obj)
        except ValueError:
            return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}), 400

    exceptions = query.order_by(DateException.exception_date).all()

    return jsonify({
        "exceptions": [e.to_dict() for e in exceptions],
        "total": len(exceptions),
    })


@nutritionists_bp.route("/<nutritionist_id>/date-exceptions", methods=["POST"])
@jwt_required(optional=True)
def create_date_exception(nutritionist_id: str):
    """
    Создать исключение по дате
    ---
    tags:
      - Nutritionists
    description: |
      Создаёт исключение для рабочего времени на конкретную дату.
      Используется в Calendar Settings (UX_MAP screen 17).
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/DateExceptionCreateRequest'
    responses:
      201:
        description: Исключение создано
        schema:
          type: object
          properties:
            exception:
              $ref: '#/definitions/DateException'
      400:
        description: Ошибка валидации
      404:
        description: Нутрициолог не найден
      409:
        description: Исключение для этой даты уже существует
    """
    try:
        data = request.get_json() or {}
        schema = DateExceptionCreateRequest(**data)
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    # Verify nutritionist exists
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    # Check if exception already exists for this date
    existing = DateException.query.filter_by(
        nutritionist_id=nutritionist_id,
        exception_date=schema.exception_date,
    ).first()

    if existing:
        return jsonify({
            "error": "Exception already exists for this date",
            "exception": existing.to_dict(),
        }), 409

    # Convert TimeRange objects to dicts for JSONB storage
    custom_hours = None
    if schema.exception_type == "custom" and schema.custom_hours:
        custom_hours = [
            {"start": tr.start, "end": tr.end} for tr in schema.custom_hours
        ]

    exception = DateException(
        nutritionist_id=nutritionist_id,
        exception_date=schema.exception_date,
        exception_type=schema.exception_type,
        custom_hours=custom_hours,
    )

    db.session.add(exception)
    db.session.commit()

    return jsonify({"exception": exception.to_dict()}), 201


@nutritionists_bp.route("/<nutritionist_id>/date-exceptions/<exception_id>", methods=["GET"])
@jwt_required(optional=True)
def get_date_exception(nutritionist_id: str, exception_id: str):
    """
    Получить исключение по дате
    ---
    tags:
      - Nutritionists
    description: Возвращает конкретное исключение по ID
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
      - name: exception_id
        in: path
        required: true
        type: string
    responses:
      200:
        description: Исключение
        schema:
          type: object
          properties:
            exception:
              $ref: '#/definitions/DateException'
      404:
        description: Исключение не найдено
    """
    exception = DateException.query.filter_by(
        id=exception_id,
        nutritionist_id=nutritionist_id,
    ).first()

    if not exception:
        return jsonify({"error": "Exception not found"}), 404

    return jsonify({"exception": exception.to_dict()})


@nutritionists_bp.route("/<nutritionist_id>/date-exceptions/<exception_id>", methods=["PUT"])
@jwt_required(optional=True)
def update_date_exception(nutritionist_id: str, exception_id: str):
    """
    Обновить исключение по дате
    ---
    tags:
      - Nutritionists
    description: Обновляет существующее исключение
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
      - name: exception_id
        in: path
        required: true
        type: string
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/DateExceptionUpdateRequest'
    responses:
      200:
        description: Исключение обновлено
        schema:
          type: object
          properties:
            exception:
              $ref: '#/definitions/DateException'
      400:
        description: Ошибка валидации
      404:
        description: Исключение не найдено
    """
    try:
        data = request.get_json() or {}
        schema = DateExceptionUpdateRequest(**data)
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    exception = DateException.query.filter_by(
        id=exception_id,
        nutritionist_id=nutritionist_id,
    ).first()

    if not exception:
        return jsonify({"error": "Exception not found"}), 404

    # Convert TimeRange objects to dicts for JSONB storage
    custom_hours = None
    if schema.exception_type == "custom" and schema.custom_hours:
        custom_hours = [
            {"start": tr.start, "end": tr.end} for tr in schema.custom_hours
        ]

    exception.exception_type = schema.exception_type
    exception.custom_hours = custom_hours

    db.session.commit()

    return jsonify({"exception": exception.to_dict()})


@nutritionists_bp.route("/<nutritionist_id>/date-exceptions/<exception_id>", methods=["DELETE"])
@jwt_required(optional=True)
def delete_date_exception(nutritionist_id: str, exception_id: str):
    """
    Удалить исключение по дате
    ---
    tags:
      - Nutritionists
    description: Удаляет исключение для рабочего времени
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
      - name: exception_id
        in: path
        required: true
        type: string
    responses:
      200:
        description: Исключение удалено
        schema:
          type: object
          properties:
            message:
              type: string
      404:
        description: Исключение не найдено
    """
    exception = DateException.query.filter_by(
        id=exception_id,
        nutritionist_id=nutritionist_id,
    ).first()

    if not exception:
        return jsonify({"error": "Exception not found"}), 404

    db.session.delete(exception)
    db.session.commit()

    return jsonify({"message": "Exception deleted"})


# ==========================================
# Google Calendar Endpoints
# ==========================================

@nutritionists_bp.route("/<nutritionist_id>/calendar/connect", methods=["GET"])
@jwt_required(optional=True)
def connect_google_calendar(nutritionist_id: str):
    """
    Get Google Calendar OAuth authorization URL
    ---
    tags:
      - Nutritionists
    description: |
      Returns the Google OAuth authorization URL for connecting Google Calendar.
      The user should be redirected to this URL to authorize access.
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
    responses:
      200:
        description: Authorization URL
        schema:
          type: object
          properties:
            authorization_url:
              type: string
              description: Google OAuth authorization URL
      400:
        description: Google Calendar not configured
      404:
        description: Нутрициолог не найден
    """
    # Verify nutritionist exists
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    try:
        from app.services.google_calendar import GoogleCalendarService
        authorization_url = GoogleCalendarService.get_authorization_url(nutritionist_id)
        return jsonify({"authorization_url": authorization_url})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


def _handle_google_calendar_callback(authorization_code: str, nutritionist_id: str):
    from app.services.google_calendar import GoogleCalendarService
    try:
        calendar = GoogleCalendarService.handle_oauth_callback(
            authorization_code, nutritionist_id
        )
    except Exception as exc:
        current_app.logger.exception(
            f"Calendar callback exception: nutritionist_id={nutritionist_id} error={exc}"
        )
        return jsonify({"error": "Calendar connection failed"}), 500

    if calendar:
        return jsonify({"calendar": calendar.to_dict()})
        return jsonify({"error": "Не удалось подключить календарь"}), 400


def _render_calendar_callback_page(
    success: bool,
    message: str,
    webapp_url: str | None = None,
):
    status_title = "Google Calendar подключён" if success else "Ошибка подключения календаря"
    button_label = "Вернуться в бот"
    button_href = "https://t.me/nutritionstagebot"

    html = f"""
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{status_title}</title>
    <style>
      body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #f7f8fb;
        color: #0f172a;
        margin: 0;
        padding: 48px 16px;
      }}
      .card {{
        max-width: 520px;
        margin: 0 auto;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 28px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
      }}
      h1 {{
        font-size: 20px;
        margin: 0 0 12px 0;
      }}
      p {{
        margin: 0 0 18px 0;
        line-height: 1.5;
        color: #334155;
      }}
      a.button {{
        display: inline-block;
        background: #2563eb;
        color: #ffffff;
        text-decoration: none;
        padding: 10px 18px;
        border-radius: 10px;
        font-weight: 600;
      }}
      .error a.button {{
        background: #f59e0b;
      }}
    </style>
  </head>
  <body>
    <div class="card {'error' if not success else ''}">
      <h1>{status_title}</h1>
      <p>{message}</p>
      <a class="button" href="{button_href}">{button_label}</a>
    </div>
  </body>
</html>
"""
    return current_app.response_class(html, mimetype="text/html")


@nutritionists_bp.route("/calendar/callback", methods=["GET"])
@jwt_required(optional=True)
def google_calendar_callback_global():
    """
    Handle Google Calendar OAuth callback (fixed redirect URI)
    ---
    tags:
      - Nutritionists
    description: |
      Handles the OAuth callback from Google after user authorization.
      This endpoint is called by Google with authorization code.
    produces:
      - application/json
    parameters:
      - name: code
        in: query
        required: true
        type: string
        description: OAuth authorization code
      - name: state
        in: query
        required: true
        type: string
        description: Nutritionist ID (state)
    responses:
      200:
        description: Calendar connected successfully
      400:
        description: Invalid authorization code or error
      404:
        description: Нутрициолог не найден
    """
    authorization_code = request.args.get("code")
    state = request.args.get("state")

    webapp_url = current_app.config.get("WEBAPP_URL")

    if not authorization_code:
        current_app.logger.warning("Calendar callback missing code")
        return _render_calendar_callback_page(
            False,
            "Код авторизации отсутствует. Попробуйте ещё раз.",
            webapp_url,
        ), 400
    if not state:
        current_app.logger.warning("Calendar callback missing state")
        return _render_calendar_callback_page(
            False,
            "Параметр state отсутствует. Попробуйте ещё раз.",
            webapp_url,
        ), 400
    try:
        uuid.UUID(state)
    except ValueError:
        current_app.logger.warning(f"Calendar callback invalid state: {state}")
        return _render_calendar_callback_page(
            False,
            "Неверный параметр state. Попробуйте ещё раз.",
            webapp_url,
        ), 400

    nutritionist = NutritionistProfile.query.get(state)
    if not nutritionist:
        current_app.logger.warning(f"Calendar callback nutritionist not found: {state}")
        return _render_calendar_callback_page(
            False,
            "Профиль нутрициолога не найден. Обратитесь в поддержку.",
            webapp_url,
        ), 404

    response = _handle_google_calendar_callback(authorization_code, state)
    if isinstance(response, tuple):
        body, status = response
        if status >= 400:
            current_app.logger.error(
                f"Calendar callback failed: nutritionist_id={state} status={status}"
            )
            return _render_calendar_callback_page(
                False,
                "Не удалось подключить Google Calendar. Попробуйте ещё раз.",
                webapp_url,
            ), status

    current_app.logger.info(f"Calendar connected: nutritionist_id={state}")
    return _render_calendar_callback_page(
        True,
        "Google Calendar подключён. Можете вернуться в бот.",
        webapp_url,
    )


@nutritionists_bp.route("/<nutritionist_id>/calendar/callback", methods=["GET"])
@jwt_required(optional=True)
def google_calendar_callback(nutritionist_id: str):
    """
    Handle Google Calendar OAuth callback
    ---
    tags:
      - Nutritionists
    description: |
      Handles the OAuth callback from Google after user authorization.
      This endpoint is called by Google with authorization code.
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
      - name: code
        in: query
        required: true
        type: string
        description: OAuth authorization code
      - name: state
        in: query
        required: false
        type: string
        description: State parameter (should match nutritionist_id)
    responses:
      200:
        description: Calendar connected successfully
        schema:
          type: object
          properties:
            calendar:
              $ref: '#/definitions/GoogleCalendarConnection'
      400:
        description: Invalid authorization code or error
      404:
        description: Нутрициолог не найден
    """
    # Verify nutritionist exists
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    authorization_code = request.args.get("code")
    state = request.args.get("state", nutritionist_id)
    webapp_url = current_app.config.get("WEBAPP_URL")

    if not authorization_code:
        current_app.logger.warning("Calendar callback (legacy) missing code")
        return _render_calendar_callback_page(
            False,
            "Код авторизации отсутствует. Попробуйте ещё раз.",
            webapp_url,
        ), 400

    if state != nutritionist_id:
        current_app.logger.warning(
            f"Calendar callback (legacy) invalid state: {state} != {nutritionist_id}"
        )
        return _render_calendar_callback_page(
            False,
            "Неверный параметр state. Попробуйте ещё раз.",
            webapp_url,
        ), 400

    try:
        response = _handle_google_calendar_callback(authorization_code, nutritionist_id)
        if isinstance(response, tuple):
            body, status = response
            if status >= 400:
                current_app.logger.error(
                    f"Calendar callback failed: nutritionist_id={nutritionist_id} status={status}"
                )
                return _render_calendar_callback_page(
                    False,
                    "Не удалось подключить Google Calendar. Попробуйте ещё раз.",
                    webapp_url,
                ), status
        current_app.logger.info(f"Calendar connected (legacy): nutritionist_id={nutritionist_id}")
        return _render_calendar_callback_page(
            True,
            "Google Calendar подключён. Можете вернуться в бот.",
            webapp_url,
        )
    except ValueError as e:
        current_app.logger.error(
            f"Calendar callback error: nutritionist_id={nutritionist_id} error={e}"
        )
        return _render_calendar_callback_page(
            False,
            "Не удалось подключить Google Calendar. Попробуйте ещё раз.",
            webapp_url,
        ), 400


@nutritionists_bp.route("/<nutritionist_id>/calendar/disconnect", methods=["POST"])
@jwt_required(optional=True)
def disconnect_google_calendar(nutritionist_id: str):
    """
    Disconnect Google Calendar
    ---
    tags:
      - Nutritionists
    description: Disconnects Google Calendar for the nutritionist
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
    responses:
      200:
        description: Calendar disconnected
        schema:
          type: object
          properties:
            message:
              type: string
      404:
        description: Нутрициолог не найден или календарь не подключен
    """
    # Verify nutritionist exists
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    try:
        from app.services.google_calendar import GoogleCalendarService
        success = GoogleCalendarService.disconnect(nutritionist_id)
        if success:
            return jsonify({"message": "Calendar disconnected"})
        else:
            return jsonify({"error": "Calendar not connected"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@nutritionists_bp.route("/<nutritionist_id>/calendar/status", methods=["GET"])
@jwt_required(optional=True)
def get_calendar_status(nutritionist_id: str):
    """
    Get Google Calendar connection status
    ---
    tags:
      - Nutritionists
    description: Returns the current Google Calendar connection status
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
    responses:
      200:
        description: Calendar connection status
        schema:
          type: object
          properties:
            calendar:
              $ref: '#/definitions/GoogleCalendarConnection'
      404:
        description: Нутрициолог не найден
    """
    # Verify nutritionist exists
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    calendar = GoogleCalendar.query.filter_by(nutritionist_id=nutritionist_id).first()

    if not calendar:
        return jsonify({
            "calendar": {
                "id": None,
                "nutritionist_id": nutritionist_id,
                "is_connected": False,
                "selected_calendar_id": None,
                "selected_calendar_summary": None,
                "connected_at": None,
                "disconnected_at": None,
            }
        })

    return jsonify({"calendar": calendar.to_dict()})


@nutritionists_bp.route("/<nutritionist_id>/calendar/calendars", methods=["GET"])
@jwt_required(optional=True)
def list_calendars(nutritionist_id: str):
    """
    List available Google Calendars
    ---
    tags:
      - Nutritionists
    description: |
      Lists all calendars available to the nutritionist.
      Requires Google Calendar to be connected.
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
    responses:
      200:
        description: List of calendars
        schema:
          type: object
          properties:
            calendars:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  summary:
                    type: string
                  primary:
                    type: boolean
                  accessRole:
                    type: string
      400:
        description: Calendar not connected or invalid credentials
      404:
        description: Нутрициолог не найден
    """
    # Verify nutritionist exists
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    try:
        from app.services.google_calendar import GoogleCalendarService
        calendars = GoogleCalendarService.list_calendars(nutritionist_id)
        return jsonify({"calendars": calendars})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@nutritionists_bp.route("/<nutritionist_id>/calendar/select", methods=["POST"])
@jwt_required(optional=True)
def select_calendar(nutritionist_id: str):
    """
    Select a Google Calendar
    ---
    tags:
      - Nutritionists
    description: |
      Selects a calendar to use for freebusy queries.
      Requires Google Calendar to be connected.
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - calendar_id
          properties:
            calendar_id:
              type: string
    responses:
      200:
        description: Calendar selected
        schema:
          type: object
          properties:
            calendar:
              $ref: '#/definitions/GoogleCalendarConnection'
      400:
        description: Invalid request or calendar not connected
      404:
        description: Нутрициолог не найден
    """
    # Verify nutritionist exists
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    try:
        data = request.get_json() or {}
        calendar_id = data.get("calendar_id")
        if not calendar_id:
            return jsonify({"error": "calendar_id is required"}), 400

        from app.services.google_calendar import GoogleCalendarService
        calendar = GoogleCalendarService.select_calendar(nutritionist_id, calendar_id)
        if calendar:
            return jsonify({"calendar": calendar.to_dict()})
        else:
            return jsonify({"error": "Failed to select calendar"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400


@nutritionists_bp.route("/<nutritionist_id>/calendar/freebusy", methods=["POST"])
@jwt_required(optional=True)
def get_freebusy(nutritionist_id: str):
    """
    Get free/busy information from Google Calendar
    ---
    tags:
      - Nutritionists
    description: |
      Returns free/busy information for the selected calendar.
      This data can be used to:
      - Generate availability slots (source="calendar")
      - Filter out busy times when showing available slots
      - Sync calendar events with availability slots
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - time_min
            - time_max
          properties:
            time_min:
              type: string
              format: date-time
              description: Start time for freebusy query (ISO 8601)
            time_max:
              type: string
              format: date-time
              description: End time for freebusy query (ISO 8601)
    responses:
      200:
        description: Freebusy data
        schema:
          type: object
          properties:
            calendars:
              type: object
              description: Freebusy data per calendar ID
              additionalProperties:
                type: object
                properties:
                  busy:
                    type: array
                    items:
                      type: object
                      properties:
                        start:
                          type: string
                          format: date-time
                        end:
                          type: string
                          format: date-time
            timeMin:
              type: string
              format: date-time
            timeMax:
              type: string
              format: date-time
      400:
        description: Invalid request, calendar not connected, or no calendar selected
      404:
        description: Нутрициолог не найден
    """
    # Verify nutritionist exists
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    try:
        data = request.get_json() or {}
        time_min_str = data.get("time_min")
        time_max_str = data.get("time_max")

        if not time_min_str or not time_max_str:
            return jsonify({"error": "time_min and time_max are required"}), 400

        # Parse datetime strings
        try:
            time_min = datetime.fromisoformat(time_min_str.replace("Z", "+00:00"))
            time_max = datetime.fromisoformat(time_max_str.replace("Z", "+00:00"))
        except ValueError:
            return jsonify({"error": "Invalid datetime format. Use ISO 8601 format."}), 400

        if time_max <= time_min:
            return jsonify({"error": "time_max must be after time_min"}), 400

        from app.services.google_calendar import GoogleCalendarService
        freebusy_result = GoogleCalendarService.get_freebusy(
            nutritionist_id, time_min, time_max
        )
        return jsonify(freebusy_result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@nutritionists_bp.route("/<nutritionist_id>/reviews", methods=["GET"])
@jwt_required(optional=True)
def list_reviews(nutritionist_id: str):
    """
    Получить отзывы нутрициолога
    ---
    tags:
      - Nutritionists
    description: |
      Возвращает список отзывов для нутрициолога.
      Скрытые отзывы исключены из результатов.
      Только сам нутрициолог или админ могут просматривать отзывы.
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - name: page
        in: query
        type: integer
        default: 1
        description: Номер страницы
      - name: limit
        in: query
        type: integer
        default: 20
        description: Количество результатов на странице
    responses:
      200:
        description: Список отзывов
        schema:
          type: object
          properties:
            reviews:
              type: array
              items:
                $ref: '#/definitions/Review'
            total:
              type: integer
            page:
              type: integer
            pages:
              type: integer
            average_rating:
              type: number
            rating_count:
              type: integer
      403:
        description: Нет доступа (только нутрициолог или админ)
      404:
        description: Нутрициолог не найден
    """
    # Verify nutritionist exists
    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    # Check permissions: nutritionist can view their own reviews, admin can view any
    claims = get_jwt()
    current_user_id = get_jwt_identity()
    role = claims.get("role", "client") if claims else "client"

    if role != "admin":
        if role != "nutritionist" or current_user_id != nutritionist_id:
            return jsonify({"error": "Not authorized"}), 403

    # Parse pagination
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    page = max(1, page)
    limit = min(100, max(1, limit))  # Clamp between 1 and 100

    # Query reviews (exclude hidden ones)
    query = Review.query.filter_by(
        nutritionist_id=nutritionist_id,
        is_hidden=False,
    ).order_by(Review.created_at.desc())

    # Get total count
    total = query.count()
    pages = (total + limit - 1) // limit

    # Paginate
    reviews = query.offset((page - 1) * limit).limit(limit).all()

    # Calculate average rating and count
    all_reviews = Review.query.filter_by(
        nutritionist_id=nutritionist_id,
        is_hidden=False,
    ).all()
    rating_count = len(all_reviews)
    average_rating = (
        sum(r.rating for r in all_reviews) / rating_count
        if rating_count > 0
        else 0.0
    )

    return jsonify({
        "reviews": [r.to_dict(include_relations=True) for r in reviews],
        "total": total,
        "page": page,
        "pages": pages,
        "average_rating": round(average_rating, 2),
        "rating_count": rating_count,
    })
