"""
Booking Routes
Handles booking creation, cancellation, payment confirmation, and hold management.
All slot operations are atomic and race-condition safe.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from app.schemas.booking import BookingCreateRequest
from app.services.booking_hold import BookingHoldService
from app.services.payments import PaymentService
from app.models import Booking


logger = logging.getLogger(__name__)
bookings_bp = Blueprint("bookings", __name__)


@bookings_bp.route("", methods=["POST"])
@jwt_required()
def create_booking():
    """
    Создать бронирование
    ---
    tags:
      - Bookings
    security:
      - BearerAuth: []
    description: |
      Создаёт бронирование и удерживает слот на 10 минут для оплаты.
      Использует блокировку на уровне строки для защиты от race conditions.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/BookingCreateRequest'
    responses:
      201:
        description: Бронирование создано
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BookingCreateResponse'
      400:
        description: Ошибка валидации или слот недоступен
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
      401:
        description: Требуется авторизация
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
      409:
        description: Слот уже занят (race condition)
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
    """
    current_user_id = get_jwt_identity()

    try:
        data = request.get_json() or {}
        schema = BookingCreateRequest(**data)
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    # Create booking with slot hold (atomic operation)
    booking, error = BookingHoldService.create_booking_with_hold(
        client_id=current_user_id,
        service_id=schema.service_id,
        slot_id=schema.slot_id,
        client_note=getattr(schema, "client_note", None),
    )

    if error:
        # Determine status code based on error type
        if "not available" in error.lower() or "already" in error.lower():
            return jsonify({"error": error}), 409
        return jsonify({"error": error}), 400

    # Create payment intent via payment service abstraction
    payment_data, payment_error = PaymentService.create_payment_for_booking(booking)
    
    if payment_error:
        # Log but don't fail - booking is already created
        logger.warning(f"Failed to create payment intent: {payment_error}")
        payment_data = None

    logger.info(f"Booking created: id={booking.id}, client={current_user_id}")

    return jsonify({
        "booking": booking.to_dict(include_relations=True),
        "payment": payment_data,
    }), 201


@bookings_bp.route("/<booking_id>", methods=["GET"])
@jwt_required()
def get_booking(booking_id: str):
    """
    Получить бронирование по ID
    ---
    tags:
      - Bookings
    security:
      - BearerAuth: []
    parameters:
      - name: booking_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
        description: UUID бронирования
    responses:
      200:
        description: Данные бронирования
        content:
          application/json:
            schema:
              type: object
              properties:
                booking:
                  $ref: '#/components/schemas/Booking'
      401:
        description: Требуется авторизация
      403:
        description: Нет доступа к этому бронированию
      404:
        description: Бронирование не найдено
    """
    current_user_id = get_jwt_identity()

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    # Verify ownership (client or nutritionist)
    if str(booking.client_id) != current_user_id and str(booking.nutritionist_id) != current_user_id:
        return jsonify({"error": "Not authorized"}), 403

    return jsonify({
        "booking": booking.to_dict(include_relations=True),
    })


@bookings_bp.route("/<booking_id>/mark-paid", methods=["POST"])
@jwt_required()
def mark_booking_paid(booking_id: str):
    """
    Отметить бронирование как оплаченное (DEV)
    ---
    tags:
      - Bookings
    security:
      - BearerAuth: []
    description: |
      **⚠️ ТОЛЬКО ДЛЯ РАЗРАБОТКИ!**
      
      Симулирует успешную оплату бронирования.
      В production с реальным платёжным провайдером этот эндпоинт отключён.
      
      Атомарная операция:
      - Блокирует booking, проверяет статус pending_payment
      - Блокирует slot, проверяет hold не истёк
      - booking → paid, устанавливает paid_at
      - slot → booked, очищает hold_expires_at
    parameters:
      - name: booking_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
        description: UUID бронирования
    responses:
      200:
        description: Оплата подтверждена
        content:
          application/json:
            schema:
              type: object
              properties:
                booking:
                  $ref: '#/components/schemas/Booking'
                payment:
                  type: object
                message:
                  type: string
                  example: "Payment confirmed successfully"
      400:
        description: Невозможно подтвердить оплату (неверный статус или истёк hold)
      403:
        description: Недоступно в production
      404:
        description: Бронирование не найдено
    """
    from flask import current_app
    from app.services.payments import PaymentService
    
    current_user_id = get_jwt_identity()

    # First verify ownership
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if str(booking.client_id) != current_user_id:
        return jsonify({"error": "Not authorized"}), 403

    # Use payment service abstraction for consistency
    # This ensures the same code path is used regardless of entry point
    payment, error = PaymentService.simulate_payment_success(booking_id)
    
    if error:
        status_code = 404 if "not found" in error.lower() else 400
        if "only available" in error.lower():
            status_code = 403
        return jsonify({"error": error}), status_code

    # Refresh booking to get updated state
    booking = Booking.query.get(booking_id)
    
    logger.info(f"Booking marked as paid via abstraction: id={booking.id}, client={current_user_id}")

    return jsonify({
        "booking": booking.to_dict(include_relations=True),
        "payment": payment.to_dict() if payment else None,
        "message": "Payment confirmed successfully",
    })


@bookings_bp.route("/<booking_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_booking(booking_id: str):
    """
    Отменить бронирование
    ---
    tags:
      - Bookings
    security:
      - BearerAuth: []
    description: |
      Отменяет бронирование и освобождает слот.
      Можно отменить только бронирования в статусе pending_payment.
      Оплаченные бронирования нельзя отменить (нужно обращаться в поддержку).
    parameters:
      - name: booking_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
        description: UUID бронирования
    requestBody:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/BookingCancelRequest'
    responses:
      200:
        description: Бронирование отменено
        content:
          application/json:
            schema:
              type: object
              properties:
                booking:
                  $ref: '#/components/schemas/Booking'
                message:
                  type: string
                  example: "Booking cancelled successfully"
      400:
        description: Невозможно отменить (оплаченное бронирование)
      401:
        description: Требуется авторизация
      404:
        description: Бронирование не найдено
    """
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    reason = data.get("reason")

    booking, error = BookingHoldService.cancel_booking(
        booking_id=booking_id,
        user_id=current_user_id,
        reason=reason,
    )

    if error:
        status_code = 404 if "not found" in error.lower() else 400
        return jsonify({"error": error}), status_code

    logger.info(f"Booking cancelled: id={booking.id}, client={current_user_id}")

    return jsonify({
        "booking": booking.to_dict(include_relations=True),
        "message": "Booking cancelled successfully",
    })


@bookings_bp.route("/release-expired-holds", methods=["POST"])
def release_expired_holds():
    """
    Освободить истёкшие hold'ы (CRON)
    ---
    tags:
      - Bookings
    description: |
      Освобождает слоты, hold которых истёк.
      Предназначен для вызова из cron job.
      Идемпотентен и безопасен для параллельного выполнения.
    responses:
      200:
        description: Hold'ы освобождены
        content:
          application/json:
            schema:
              type: object
              properties:
                released_count:
                  type: integer
                  example: 5
                message:
                  type: string
                  example: "Released 5 expired holds"
    """
    # In production, this should be protected by a secret key or internal network
    # For now, we allow it for simplicity

    released_count = BookingHoldService.release_expired_holds()

    logger.info(f"Released {released_count} expired holds via cron endpoint")

    return jsonify({
        "released_count": released_count,
        "message": f"Released {released_count} expired holds",
    })
