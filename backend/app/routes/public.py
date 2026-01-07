"""
Public Routes
Public endpoints for browsing nutritionists (no auth required).
"""

from datetime import datetime
from flask import Blueprint, request, jsonify

from app.models import NutritionistProfile, Service, AvailabilitySlot
from app.services.matching import MatchingService
from app.services.filters import FILTER_OPTIONS, validate_filters, get_empty_filters


public_bp = Blueprint("public", __name__)


@public_bp.route("/nutritionists", methods=["GET"])
def list_nutritionists():
    """
    Список нутрициологов
    ---
    tags:
      - Public
    description: Получить список одобренных нутрициологов с возможностью фильтрации
    parameters:
      - name: specialization
        in: query
        schema:
          type: string
        description: Фильтр по специализации (weight_loss, diabetes, etc.)
        example: weight_loss
      - name: budget
        in: query
        schema:
          type: integer
        description: Максимальный бюджет (фильтр по цене)
        example: 5000
      - name: tags
        in: query
        schema:
          type: array
          items:
            type: string
        description: Фильтр по тегам (можно указать несколько)
        example: ["vegetarian"]
    responses:
      200:
        description: Список нутрициологов
        content:
          application/json:
            schema:
              type: object
              properties:
                nutritionists:
                  type: array
                  items:
                    $ref: '#/components/schemas/Nutritionist'
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
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
        description: UUID нутрициолога
    responses:
      200:
        description: Данные нутрициолога
        content:
          application/json:
            schema:
              type: object
              properties:
                nutritionist:
                  $ref: '#/components/schemas/Nutritionist'
      404:
        description: Нутрициолог не найден
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
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
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
        description: UUID нутрициолога
    responses:
      200:
        description: Список активных услуг
        content:
          application/json:
            schema:
              type: object
              properties:
                services:
                  type: array
                  items:
                    $ref: '#/components/schemas/Service'
      404:
        description: Нутрициолог не найден
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
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


@public_bp.route("/nutritionists/<nutritionist_id>/slots", methods=["GET"])
def list_slots(nutritionist_id: str):
    """
    Доступные слоты нутрициолога
    ---
    tags:
      - Public
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
        description: UUID нутрициолога
      - name: service_id
        in: query
        schema:
          type: string
          format: uuid
        description: UUID услуги (опционально)
    responses:
      200:
        description: Список свободных слотов
        content:
          application/json:
            schema:
              type: object
              properties:
                slots:
                  type: array
                  items:
                    $ref: '#/components/schemas/Slot'
      404:
        description: Нутрициолог или услуга не найдены
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
    """
    service_id = request.args.get("service_id")

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

    # Get available slots (free slots in the future)
    slots = AvailabilitySlot.query.filter(
        AvailabilitySlot.nutritionist_id == nutritionist_id,
        AvailabilitySlot.status == "free",
        AvailabilitySlot.start_at > datetime.utcnow(),
    ).order_by(AvailabilitySlot.start_at).all()

    return jsonify({
        "slots": [s.to_dict() for s in slots],
    })


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
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              filters:
                $ref: '#/components/schemas/SearchFilters'
          example:
            filters:
              goals: ["weight_loss"]
              budget_max_rub: 5000
              dietary: ["vegetarian"]
              help_mode: "one_time"
    responses:
      200:
        description: Результаты поиска со скорингом
        content:
          application/json:
            schema:
              type: object
              properties:
                nutritionists:
                  type: array
                  items:
                    $ref: '#/components/schemas/NutritionistSearchResult'
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
    responses:
      200:
        description: Опции фильтров
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FilterOptions'
    """
    return jsonify(FILTER_OPTIONS)


