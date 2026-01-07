"""
Payment Routes
Unified payment API with provider abstraction.

Endpoints:
    POST /api/payments/create          - Create payment intent
    POST /api/payments/webhook/{provider} - Provider webhook handler
    POST /api/payments/mock-pay/{booking_id} - Mock payment endpoint (dev)
    GET  /api/payments/{booking_id}/status - Get payment status
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import Booking
from app.services.payments import PaymentService

logger = logging.getLogger(__name__)
payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/create", methods=["POST"])
@jwt_required()
def create_payment_intent():
    """
    Создать платёжное намерение
    ---
    tags:
      - Payments
    security:
      - BearerAuth: []
    description: Создаёт платёжное намерение (payment intent) для бронирования
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - booking_id
            properties:
              booking_id:
                type: string
                format: uuid
    responses:
      200:
        description: Payment intent создан
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PaymentIntent'
      400:
        description: Ошибка валидации или неверный статус бронирования
      401:
        description: Требуется авторизация
      403:
        description: Нет доступа к бронированию
      404:
        description: Бронирование не найдено
    """
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    booking_id = data.get("booking_id")
    if not booking_id:
        return jsonify({"error": "booking_id is required"}), 400
    
    # Get booking
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
    # Verify ownership
    if str(booking.client_id) != current_user_id:
        return jsonify({"error": "Not authorized"}), 403
    
    # Create payment intent
    intent_data, error = PaymentService.create_payment_for_booking(booking)
    
    if error:
        status_code = 400
        if "not found" in error.lower():
            status_code = 404
        return jsonify({"error": error}), status_code
    
    logger.info(
        f"Payment intent created: "
        f"booking_id={booking_id}, "
        f"user={current_user_id}"
    )
    
    return jsonify(intent_data)


@payments_bp.route("/webhook/<provider>", methods=["POST"])
def payment_webhook(provider: str):
    """
    Webhook для платёжного провайдера
    ---
    tags:
      - Payments
    description: |
      Обрабатывает webhooks от платёжных провайдеров при изменении статуса платежа.
      Каждый провайдер имеет свой URL: `/api/payments/webhook/telegram`, 
      `/api/payments/webhook/yookassa`, etc.
    parameters:
      - name: provider
        in: path
        required: true
        schema:
          type: string
          enum: [telegram, yookassa, mock]
        description: Название платёжного провайдера
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PaymentWebhookRequest'
    responses:
      200:
        description: Webhook обработан
        content:
          application/json:
            schema:
              type: object
              properties:
                payment:
                  type: object
                message:
                  type: string
      400:
        description: Неверный payload
      401:
        description: Неверная подпись
      404:
        description: Бронирование не найдено
    """
    payload = request.get_json() or {}
    headers = dict(request.headers)
    
    payment, error = PaymentService.process_provider_webhook(
        provider_name=provider,
        payload=payload,
        headers=headers,
    )
    
    if error:
        if "Invalid signature" in error:
            return jsonify({"error": error}), 401
        if "not found" in error.lower():
            return jsonify({"error": error}), 404
        if "Unknown payment provider" in error:
            return jsonify({"error": error}), 400
        return jsonify({"error": error}), 400
    
    return jsonify({
        "payment": payment.to_dict() if payment else None,
        "message": f"Payment {payment.status}" if payment else "Processed",
    })


@payments_bp.route("/mock-pay/<booking_id>", methods=["POST"])
def mock_payment(booking_id: str):
    """
    Симуляция оплаты (DEV)
    ---
    tags:
      - Payments
    description: |
      **⚠️ ТОЛЬКО ДЛЯ РАЗРАБОТКИ!**
      
      Симулирует успешную оплату через mock webhook.
      Доступно только в dev-режиме или когда PAYMENT_PROVIDER=mock.
    parameters:
      - name: booking_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
    responses:
      200:
        description: Оплата симулирована
        content:
          application/json:
            schema:
              type: object
              properties:
                payment:
                  type: object
                booking:
                  $ref: '#/components/schemas/Booking'
                message:
                  type: string
                  example: "Payment simulated successfully"
      403:
        description: Недоступно в production
      404:
        description: Бронирование не найдено
    """
    # Check if mock payments are allowed
    is_dev = current_app.debug or current_app.config.get("TESTING")
    provider = current_app.config.get("PAYMENT_PROVIDER", "mock")
    
    if not is_dev and provider != "mock":
        return jsonify({
            "error": "Mock payments only available in development mode"
        }), 403
    
    # Process as mock webhook
    payload = {
        "booking_id": booking_id,
        "status": "succeeded",
    }
    
    payment, error = PaymentService.process_provider_webhook(
        provider_name="mock",
        payload=payload,
        headers={},
    )
    
    if error:
        status_code = 404 if "not found" in error.lower() else 400
        return jsonify({"error": error}), status_code
    
    logger.info(f"Mock payment processed: booking_id={booking_id}")
    
    return jsonify({
        "payment": payment.to_dict() if payment else None,
        "booking": Booking.query.get(booking_id).to_dict(include_relations=True),
        "message": "Payment simulated successfully",
    })


@payments_bp.route("/<booking_id>/status", methods=["GET"])
@jwt_required()
def get_payment_status(booking_id: str):
    """
    Статус платежа по бронированию
    ---
    tags:
      - Payments
    security:
      - BearerAuth: []
    parameters:
      - name: booking_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
    responses:
      200:
        description: Данные платежа
        content:
          application/json:
            schema:
              type: object
              properties:
                payment:
                  type: object
      401:
        description: Требуется авторизация
      403:
        description: Нет доступа к бронированию
      404:
        description: Платёж не найден
    """
    current_user_id = get_jwt_identity()
    
    # Get booking to verify ownership
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
    # Verify ownership
    if str(booking.client_id) != current_user_id and str(booking.nutritionist_id) != current_user_id:
        return jsonify({"error": "Not authorized"}), 403
    
    payment_data = PaymentService.get_payment_status(booking_id)
    
    if not payment_data:
        return jsonify({"error": "Payment not found"}), 404
    
    return jsonify({"payment": payment_data})


# Legacy webhook endpoint for backward compatibility
@payments_bp.route("/webhook", methods=["POST"])
def legacy_payment_webhook():
    """
    Legacy webhook (deprecated)
    ---
    tags:
      - Payments
    deprecated: true
    description: |
      **DEPRECATED:** Используйте `/api/payments/webhook/{provider}` вместо этого.
      
      Определяет провайдера из payload.
    requestBody:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PaymentWebhookRequest'
    responses:
      200:
        description: Webhook обработан
      400:
        description: Ошибка
    """
    payload = request.get_json() or {}
    provider = payload.get("provider", "mock")
    headers = dict(request.headers)
    
    payment, error = PaymentService.process_provider_webhook(
        provider_name=provider,
        payload=payload,
        headers=headers,
    )
    
    if error:
        if "Invalid signature" in error:
            return jsonify({"error": error}), 401
        if "not found" in error.lower():
            return jsonify({"error": error}), 404
        return jsonify({"error": error}), 400
    
    return jsonify({
        "payment": payment.to_dict() if payment else None,
        "message": f"Payment {payment.status}" if payment else "Processed",
    })
