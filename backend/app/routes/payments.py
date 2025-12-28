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
    Create a payment intent for a booking.
    
    Request:
        POST /api/payments/create
        Authorization: Bearer <token>
        {
            "booking_id": "uuid"
        }
    
    Response:
        200: {
            "provider": "mock",
            "payment_url": "/api/payments/mock-pay/...",
            "payment_id": "uuid",
            "amount_rub": 3000,
            "currency": "RUB",
            "expires_at": "2024-12-28T12:00:00Z"
        }
        400: Validation error or invalid booking state
        403: Not authorized
        404: Booking not found
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
    Handle payment provider webhooks.
    
    This endpoint is called by payment providers when payment status changes.
    Each provider has its own URL: /api/payments/webhook/telegram,
    /api/payments/webhook/yookassa, etc.
    
    Request:
        POST /api/payments/webhook/{provider}
        Headers: Provider-specific (e.g., X-YooKassa-Signature)
        Body: Provider-specific payload
    
    Response:
        200: { "payment": {...}, "message": "Payment processed" }
        400: Invalid payload
        401: Invalid signature
        404: Booking not found
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
    Mock payment endpoint for development.
    Simulates successful payment via mock webhook.
    
    Only available in development mode or when PAYMENT_PROVIDER=mock.
    
    Request:
        POST /api/payments/mock-pay/{booking_id}
    
    Response:
        200: { "payment": {...}, "message": "Payment simulated" }
        403: Not available in production
        404: Booking not found
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
    Get payment status for a booking.
    
    Request:
        GET /api/payments/{booking_id}/status
        Authorization: Bearer <token>
    
    Response:
        200: { "payment": {...} }
        404: Payment not found
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
    Legacy webhook endpoint (backward compatibility).
    
    Deprecated: Use /api/payments/webhook/{provider} instead.
    
    This endpoint determines the provider from the payload.
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
