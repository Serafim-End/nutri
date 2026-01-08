"""
Client Routes
Handles client intake forms, nutritionist matching, and filter management.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from app.extensions import db
from app.models import Intake, Profile, ClientFilterState
from app.schemas.client import IntakeCreateRequest
from app.services.matching import MatchingService
from app.services.filters import normalize_filters_from_intake, validate_filters, get_empty_filters


clients_bp = Blueprint("clients", __name__)


@clients_bp.route("/intakes", methods=["POST"])
@jwt_required()
def create_intake():
    """
    Отправить анкету клиента
    ---
    tags:
      - Clients
    security:
      - BearerAuth: []
    description: |
      Отправляет анкету (intake) и создаёт/обновляет client_filter_state 
      с нормализованными фильтрами для поиска.
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/IntakeRequest'
    responses:
      201:
        description: Анкета успешно отправлена
        schema:
          type: object
          properties:
            intake:
              $ref: '#/definitions/Intake'
            intake_id:
              type: string
            normalized_filters:
              $ref: '#/definitions/SearchFilters'
            message:
              type: string
      400:
        description: Ошибка валидации
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Требуется авторизация
    """
    current_user_id = get_jwt_identity()

    try:
        data = request.get_json() or {}
        schema = IntakeCreateRequest(**data)
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    # Verify user exists
    profile = Profile.query.get(current_user_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    # Build answers dict
    answers = {
        "goals": schema.goals,
        "dietary_restrictions": schema.dietary_restrictions,
        "budget_min": schema.budget_min,
        "budget_max": schema.budget_max,
        "preferred_schedule": schema.preferred_schedule,
        "health_conditions": schema.health_conditions,
        "additional_notes": schema.additional_notes,
    }

    # Create intake
    intake = Intake(
        client_id=current_user_id,
        answers=answers,
    )

    db.session.add(intake)
    db.session.flush()  # Get the intake ID before committing

    # Normalize filters from answers
    normalized_filters = normalize_filters_from_intake(answers)

    # Upsert client_filter_state
    filter_state = ClientFilterState.query.get(current_user_id)
    if filter_state:
        filter_state.intake_id = intake.id
        filter_state.filters = normalized_filters
    else:
        filter_state = ClientFilterState(
            client_id=current_user_id,
            intake_id=intake.id,
            filters=normalized_filters,
        )
        db.session.add(filter_state)

    db.session.commit()

    return jsonify({
        "intake": intake.to_dict(),
        "intake_id": str(intake.id),
        "normalized_filters": normalized_filters,
        "message": "Intake submitted successfully",
    }), 201


@clients_bp.route("/matches", methods=["GET"])
@jwt_required()
def get_matches():
    """
    Получить подходящих нутрициологов по анкете
    ---
    tags:
      - Clients
    security:
      - BearerAuth: []
    produces:
      - application/json
    parameters:
      - name: intake_id
        in: query
        required: true
        type: string
        description: UUID анкеты (intake)
    responses:
      200:
        description: Список подходящих нутрициологов
        schema:
          type: object
          properties:
            matches:
              type: array
              items:
                $ref: '#/definitions/Nutritionist'
            total:
              type: integer
      400:
        description: intake_id не указан
      401:
        description: Требуется авторизация
      403:
        description: Анкета принадлежит другому пользователю
      404:
        description: Анкета не найдена
    """
    current_user_id = get_jwt_identity()
    intake_id = request.args.get("intake_id")

    if not intake_id:
        return jsonify({"error": "intake_id required"}), 400

    # Verify intake belongs to current user
    intake = Intake.query.get(intake_id)
    if not intake:
        return jsonify({"error": "Intake not found"}), 404

    if str(intake.client_id) != current_user_id:
        return jsonify({"error": "Not authorized"}), 403

    # Find matches
    matches = MatchingService.find_matches(intake)

    return jsonify({
        "matches": [m.to_dict(include_profile=True) for m in matches],
        "total": len(matches),
    })


@clients_bp.route("/intakes", methods=["GET"])
@jwt_required()
def list_intakes():
    """
    Список анкет клиента
    ---
    tags:
      - Clients
    security:
      - BearerAuth: []
    produces:
      - application/json
    responses:
      200:
        description: Список анкет
        schema:
          type: object
          properties:
            intakes:
              type: array
              items:
                $ref: '#/definitions/Intake'
      401:
        description: Требуется авторизация
    """
    current_user_id = get_jwt_identity()

    intakes = Intake.query.filter_by(client_id=current_user_id).order_by(
        Intake.created_at.desc()
    ).all()

    return jsonify({
        "intakes": [i.to_dict() for i in intakes],
    })


@clients_bp.route("/bookings", methods=["GET"])
@jwt_required()
def list_client_bookings():
    """
    Список бронирований клиента
    ---
    tags:
      - Clients
    security:
      - BearerAuth: []
    produces:
      - application/json
    responses:
      200:
        description: Список бронирований
        schema:
          type: object
          properties:
            bookings:
              type: array
              items:
                $ref: '#/definitions/Booking'
      401:
        description: Требуется авторизация
    """
    from app.models import Booking

    current_user_id = get_jwt_identity()

    bookings = Booking.query.filter_by(client_id=current_user_id).order_by(
        Booking.created_at.desc()
    ).all()

    return jsonify({
        "bookings": [b.to_dict(include_relations=True) for b in bookings],
    })


@clients_bp.route("/me/bookings", methods=["GET"])
@jwt_required()
def list_my_bookings():
    """
    Мои бронирования (с полной информацией)
    ---
    tags:
      - Clients
    security:
      - BearerAuth: []
    description: |
      Список бронирований текущего клиента с информацией об услуге, 
      слоте и нутрициологе. Отсортированы по дате создания (новые первые).
    produces:
      - application/json
    responses:
      200:
        description: Список бронирований с развёрнутыми данными
        schema:
          type: object
          properties:
            bookings:
              type: array
              items:
                $ref: '#/definitions/Booking'
      401:
        description: Требуется авторизация
    """
    from app.models import Booking

    current_user_id = get_jwt_identity()

    bookings = Booking.query.filter_by(client_id=current_user_id).order_by(
        Booking.created_at.desc()
    ).all()

    return jsonify({
        "bookings": [b.to_dict(include_relations=True) for b in bookings],
    })


@clients_bp.route("/me/filters", methods=["GET"])
@jwt_required()
def get_filters():
    """
    Получить текущие фильтры клиента
    ---
    tags:
      - Clients
    security:
      - BearerAuth: []
    description: Возвращает текущие фильтры и значения по умолчанию из анкеты
    produces:
      - application/json
    responses:
      200:
        description: Фильтры клиента
        schema:
          type: object
          properties:
            intake_id:
              type: string
            filters:
              $ref: '#/definitions/SearchFilters'
            defaults:
              $ref: '#/definitions/SearchFilters'
      401:
        description: Требуется авторизация
    """
    current_user_id = get_jwt_identity()

    # Get current filter state
    filter_state = ClientFilterState.query.get(current_user_id)
    
    # Get defaults from latest intake if exists
    defaults = get_empty_filters()
    intake_id = None
    
    if filter_state and filter_state.intake_id:
        intake = Intake.query.get(filter_state.intake_id)
        if intake:
            defaults = normalize_filters_from_intake(intake.answers or {})
            intake_id = str(filter_state.intake_id)
    else:
        # No filter state yet - check for any intake
        latest_intake = Intake.query.filter_by(
            client_id=current_user_id
        ).order_by(Intake.created_at.desc()).first()
        
        if latest_intake:
            defaults = normalize_filters_from_intake(latest_intake.answers or {})
            intake_id = str(latest_intake.id)

    # Current filters (or defaults if no filter state)
    filters = filter_state.filters if filter_state else defaults

    return jsonify({
        "intake_id": intake_id,
        "filters": filters,
        "defaults": defaults,
    })


@clients_bp.route("/me/filters", methods=["PUT"])
@jwt_required()
def update_filters():
    """
    Обновить фильтры клиента
    ---
    tags:
      - Clients
    security:
      - BearerAuth: []
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
        description: Фильтры обновлены
        schema:
          type: object
          properties:
            intake_id:
              type: string
            filters:
              $ref: '#/definitions/SearchFilters'
            updated_at:
              type: string
              format: date-time
      400:
        description: Ошибка валидации
      401:
        description: Требуется авторизация
    """
    current_user_id = get_jwt_identity()

    data = request.get_json() or {}
    raw_filters = data.get("filters", {})

    # Validate filters
    validated_filters = validate_filters(raw_filters)

    # Get or create filter state
    filter_state = ClientFilterState.query.get(current_user_id)
    
    if filter_state:
        filter_state.filters = validated_filters
    else:
        # Get latest intake if exists
        latest_intake = Intake.query.filter_by(
            client_id=current_user_id
        ).order_by(Intake.created_at.desc()).first()
        
        filter_state = ClientFilterState(
            client_id=current_user_id,
            intake_id=latest_intake.id if latest_intake else None,
            filters=validated_filters,
        )
        db.session.add(filter_state)

    db.session.commit()

    return jsonify({
        "intake_id": str(filter_state.intake_id) if filter_state.intake_id else None,
        "filters": filter_state.filters,
        "updated_at": filter_state.updated_at.isoformat() if filter_state.updated_at else None,
    })
