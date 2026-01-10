"""
Public Routes
Public endpoints for browsing nutritionists (no auth required).
"""

from datetime import datetime, date, time, timedelta, timezone
from flask import Blueprint, request, jsonify
from flask import current_app

from app.models import (
    NutritionistProfile,
    Service,
    WorkingHoursTemplate,
    DateException,
    GoogleCalendar,
    AvailabilitySlot,
    Review,
)
from app.extensions import db
from app.services.matching import MatchingService
from app.services.filters import FILTER_OPTIONS, validate_filters, get_empty_filters
from app.services.availability import (
    calculate_availability,
    parse_google_calendar_busy,
    TimeRange,
)
from app.services.google_calendar import GoogleCalendarService


public_bp = Blueprint("public", __name__)


@public_bp.route("/nutritionists", methods=["GET"])
def list_nutritionists():
    """
    Список нутрициологов
    ---
    tags:
      - Public
    description: Получить список одобренных нутрициологов с возможностью фильтрации
    produces:
      - application/json
    parameters:
      - name: specialization
        in: query
        type: string
        description: Фильтр по специализации (weight_loss, diabetes, etc.)
      - name: budget
        in: query
        type: integer
        description: Максимальный бюджет (фильтр по цене)
      - name: tags
        in: query
        type: array
        items:
          type: string
        collectionFormat: multi
        description: Фильтр по тегам (можно указать несколько)
    responses:
      200:
        description: Список нутрициологов
        schema:
          type: object
          properties:
            nutritionists:
              type: array
              items:
                $ref: '#/definitions/Nutritionist'
            total:
              type: integer
              example: 10
    """
    specialization = request.args.get("specialization")
    budget = request.args.get("budget", type=int)
    tags = request.args.getlist("tags")

    nutritionists = MatchingService.search_nutritionists(
        specialization=specialization,
        budget_max=budget,
        tags=tags if tags else None,
    )

    return jsonify({
        "nutritionists": [n.to_dict(include_profile=True) for n in nutritionists],
        "total": len(nutritionists),
    })


@public_bp.route("/nutritionists/<nutritionist_id>", methods=["GET"])
def get_nutritionist(nutritionist_id: str):
    """
    Получить нутрициолога по ID
    ---
    tags:
      - Public
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
        description: Данные нутрициолога
        schema:
          type: object
          properties:
            nutritionist:
              $ref: '#/definitions/Nutritionist'
      404:
        description: Нутрициолог не найден
        schema:
          $ref: '#/definitions/Error'
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)

    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    # Only show approved and active nutritionists publicly
    if nutritionist.verification_status != "approved" or not nutritionist.is_active:
        return jsonify({"error": "Nutritionist not found"}), 404

    return jsonify({
        "nutritionist": nutritionist.to_dict(include_profile=True),
    })


@public_bp.route("/nutritionists/<nutritionist_id>/services", methods=["GET"])
def list_services(nutritionist_id: str):
    """
    Список услуг нутрициолога
    ---
    tags:
      - Public
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
        description: Список активных услуг
        schema:
          type: object
          properties:
            services:
              type: array
              items:
                $ref: '#/definitions/Service'
      404:
        description: Нутрициолог не найден
        schema:
          $ref: '#/definitions/Error'
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)

    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    # Only show approved and active nutritionists publicly
    if nutritionist.verification_status != "approved" or not nutritionist.is_active:
        return jsonify({"error": "Nutritionist not found"}), 404

    services = Service.query.filter(
        Service.nutritionist_id == nutritionist_id,
        Service.is_active == True,  # noqa: E712
    ).all()

    return jsonify({
        "services": [s.to_dict() for s in services],
    })


@public_bp.route("/nutritionists/<nutritionist_id>/reviews", methods=["GET"])
def list_public_reviews(nutritionist_id: str):
    """
    Публичные отзывы нутрициолога
    ---
    tags:
      - Public
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
      - name: limit
        in: query
        type: integer
        default: 10
    responses:
      200:
        description: Список отзывов
      404:
        description: Нутрициолог не найден
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)

    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    if nutritionist.verification_status != "approved" or not nutritionist.is_active:
        return jsonify({"error": "Nutritionist not found"}), 404

    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    page = max(1, page)
    limit = min(20, max(1, limit))

    query = Review.query.filter_by(
        nutritionist_id=nutritionist_id,
        is_hidden=False,
    ).order_by(Review.created_at.desc())

    total = query.count()
    pages = (total + limit - 1) // limit
    reviews = query.offset((page - 1) * limit).limit(limit).all()

    visible_reviews = Review.query.filter_by(
        nutritionist_id=nutritionist_id,
        is_hidden=False,
    ).all()
    rating_count = len(visible_reviews)
    average_rating = (
        sum(r.rating for r in visible_reviews) / rating_count
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


@public_bp.route("/nutritionists/<nutritionist_id>/slots", methods=["GET"])
def list_slots(nutritionist_id: str):
    """
    Доступные слоты нутрициолога
    ---
    tags:
      - Public
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - name: service_id
        in: query
        type: string
        description: UUID услуги (опционально)
      - name: days_ahead
        in: query
        type: integer
        description: "Number of days ahead to calculate availability (default: 30)"
    responses:
      200:
        description: Список свободных слотов
        schema:
          type: object
          properties:
            slots:
              type: array
              items:
                $ref: '#/definitions/Slot'
      404:
        description: Нутрициолог или услуга не найдены
        schema:
          $ref: '#/definitions/Error'
    """
    service_id = request.args.get("service_id")
    days_ahead = request.args.get("days_ahead", type=int, default=30)

    nutritionist = NutritionistProfile.query.get(nutritionist_id)

    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    # Only show approved and active nutritionists publicly
    if nutritionist.verification_status != "approved" or not nutritionist.is_active:
        return jsonify({"error": "Nutritionist not found"}), 404

    # If service_id provided, verify it belongs to this nutritionist
    if service_id:
        service = Service.query.get(service_id)
        if not service or str(service.nutritionist_id) != nutritionist_id:
            return jsonify({"error": "Service not found"}), 404

    # Determine date range and prefetch existing slots (manual/calendar) for booking
    try:
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)
        time_min = datetime.now(timezone.utc)
        time_max = datetime.combine(end_date, time(23, 59, 59)).replace(tzinfo=timezone.utc)

        existing_slots = AvailabilitySlot.query.filter(
            AvailabilitySlot.nutritionist_id == nutritionist_id,
            AvailabilitySlot.start_at >= time_min,
            AvailabilitySlot.start_at <= time_max,
            AvailabilitySlot.status.in_(["free", "held", "booked"]),
        ).order_by(AvailabilitySlot.start_at).all()

        free_slots = [slot for slot in existing_slots if slot.status == "free"]

        # Get working hours template
        working_hours = WorkingHoursTemplate.query.filter_by(
            nutritionist_id=nutritionist_id
        ).first()
        
        if not working_hours or not working_hours.weekly_schedule:
            # No working hours configured, return existing manual slots only
            return jsonify({"slots": [s.to_dict() for s in free_slots]})

        weekly_schedule = working_hours.weekly_schedule

        # Get date exceptions
        date_exceptions_query = DateException.query.filter(
            DateException.nutritionist_id == nutritionist_id,
            DateException.exception_date >= start_date,
            DateException.exception_date <= end_date,
        ).all()
        
        date_exceptions = {}
        for exc in date_exceptions_query:
            date_exceptions[exc.exception_date] = {
                "exception_type": exc.exception_type,
                "custom_hours": exc.custom_hours or [],
            }

        # Build busy intervals from existing slots to avoid overlaps with manual/calendar slots
        busy_intervals = [
            TimeRange(start=slot.start_at, end=slot.end_at) for slot in existing_slots
        ]

        # Get Google Calendar busy intervals (if connected)
        google_calendar = GoogleCalendar.query.filter_by(
            nutritionist_id=nutritionist_id
        ).first()
        
        if google_calendar and google_calendar.is_connected and google_calendar.selected_calendar_id:
            try:
                # Set time_max to end of end_date
                freebusy_result = GoogleCalendarService.get_freebusy(
                    nutritionist_id=nutritionist_id,
                    time_min=time_min,
                    time_max=time_max,
                )
                
                busy_intervals.extend(parse_google_calendar_busy(
                    freebusy_result,
                    calendar_id=google_calendar.selected_calendar_id,
                ))
            except Exception as e:
                # Log error but continue without Google Calendar data
                current_app.logger.warning(
                    f"Failed to fetch Google Calendar busy intervals for {nutritionist_id}: {e}"
                )

        # Calculate available slots
        available_ranges = calculate_availability(
            weekly_schedule=weekly_schedule,
            date_exceptions=date_exceptions,
            busy_intervals=busy_intervals,
            start_date=start_date,
            end_date=end_date,
        )

        # Create calculated slots in DB if they don't already exist
        existing_keys = {(s.start_at, s.end_at) for s in existing_slots}
        created_slots = []
        for tr in available_ranges:
            key = (tr.start, tr.end)
            if key in existing_keys:
                continue
            slot = AvailabilitySlot(
                nutritionist_id=nutritionist_id,
                start_at=tr.start,
                end_at=tr.end,
                status="free",
                source="calculated",
            )
            db.session.add(slot)
            created_slots.append(slot)
            existing_keys.add(key)

        if created_slots:
            db.session.commit()

        all_free_slots = free_slots + created_slots
        return jsonify({"slots": [s.to_dict() for s in all_free_slots]})

    except Exception as e:
        current_app.logger.error(f"Error calculating availability for {nutritionist_id}: {e}")
        # Fallback: return empty slots on error
        return jsonify({"slots": []})


@public_bp.route("/nutritionists/search", methods=["POST"])
def search_nutritionists():
    """
    Поиск нутрициологов с фильтрами и скорингом
    ---
    tags:
      - Public
    description: |
      Расширенный поиск нутрициологов с учётом целей, бюджета и предпочтений.
      Возвращает результаты отсортированные по релевантности (score).
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            filters:
              $ref: '#/definitions/SearchFilters'
    responses:
      200:
        description: Результаты поиска со скорингом
        schema:
          type: object
          properties:
            nutritionists:
              type: array
              items:
                $ref: '#/definitions/NutritionistSearchResult'
            total:
              type: integer
              example: 5
    """
    data = request.get_json() or {}
    raw_filters = data.get("filters", {})

    # Validate filters (or use empty defaults)
    filters = validate_filters(raw_filters) if raw_filters else get_empty_filters()

    # Search with scoring
    results = MatchingService.search_with_filters(filters)

    # Build response
    nutritionists = []
    for r in results:
        n = r["nutritionist"]
        nutritionist_data = n.to_dict(include_profile=True)
        nutritionist_data["score"] = r["score"]
        nutritionist_data["matched_reasons"] = r["matched_reasons"]
        nutritionists.append(nutritionist_data)

    return jsonify({
        "nutritionists": nutritionists,
        "total": len(nutritionists),
    })


@public_bp.route("/filters/options", methods=["GET"])
def get_filter_options():
    """
    Опции фильтров для UI
    ---
    tags:
      - Public
    description: Возвращает все доступные опции для фильтров поиска (для построения UI)
    produces:
      - application/json
    responses:
      200:
        description: Опции фильтров
        schema:
          $ref: '#/definitions/FilterOptions'
    """
    return jsonify(FILTER_OPTIONS)
