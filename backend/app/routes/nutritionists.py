"""
Nutritionist Routes
Handles nutritionist profile management (for Botpress integration).
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
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
)
from app.schemas.nutritionist import (
    NutritionistUpsertRequest,
    DocumentUploadRequest,
    ServiceCreateRequest,
    BulkSlotCreateRequest,
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
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/NutritionistUpsertRequest'
    responses:
      200:
        description: Профиль создан/обновлён
        content:
          application/json:
            schema:
              type: object
              properties:
                nutritionist:
                  $ref: '#/components/schemas/Nutritionist'
                is_new:
                  type: boolean
                  description: true если это новый профиль
      400:
        description: Ошибка валидации
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
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
        )
        db.session.add(profile)
        db.session.flush()
        is_new = True
    else:
        # Update existing profile
        profile.full_name = schema.full_name
        if schema.photo_url:
            profile.photo_url = schema.photo_url
        if profile.role != "nutritionist":
            profile.role = "nutritionist"

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
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/DocumentCreateRequest'
    responses:
      201:
        description: Документ добавлен
        content:
          application/json:
            schema:
              type: object
              properties:
                document:
                  $ref: '#/components/schemas/Document'
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
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ServiceCreateRequest'
    responses:
      201:
        description: Услуга создана
        content:
          application/json:
            schema:
              type: object
              properties:
                service:
                  $ref: '#/components/schemas/Service'
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
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/SlotCreateRequest'
    responses:
      201:
        description: Слоты созданы
        content:
          application/json:
            schema:
              type: object
              properties:
                slots:
                  type: array
                  items:
                    $ref: '#/components/schemas/Slot'
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
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
    responses:
      200:
        description: Данные дашборда
        content:
          application/json:
            schema:
              type: object
              properties:
                nutritionist:
                  $ref: '#/components/schemas/Nutritionist'
                services:
                  type: array
                  items:
                    $ref: '#/components/schemas/Service'
                upcoming_slots:
                  type: array
                  items:
                    $ref: '#/components/schemas/Slot'
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


