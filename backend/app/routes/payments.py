"""
Payment Routes
Handles payment webhook processing.
"""

from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from app.schemas.booking import PaymentWebhookRequest
from app.services.payments import PaymentService


payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/webhook", methods=["POST"])
def payment_webhook():
    """
    Handle payment provider webhooks.
    Verifies signature and processes payment status updates.

    Request:
        POST /api/payments/webhook
        {
            "provider": "telegram",
            "payment_id": "provider_payment_123",
            "booking_id": "uuid",
            "amount_rub": 3000,
            "status": "succeeded",
            "signature": "hmac_signature"
        }

    Response:
        200: { "payment": {...}, "message": "Payment processed" }
        400: Validation error
        401: Invalid signature
        404: Booking not found
    """
    try:
        data = request.get_json() or {}
        schema = PaymentWebhookRequest(**data)
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    # Verify webhook signature
    is_valid = PaymentService.verify_webhook_signature(
        provider=schema.provider,
        payload=data,
        signature=schema.signature,
    )

    if not is_valid:
        return jsonify({"error": "Invalid signature"}), 401

    # Process payment
    payment, error = PaymentService.process_webhook(
        provider=schema.provider,
        payment_id=schema.payment_id,
        booking_id=schema.booking_id,
        amount_rub=schema.amount_rub,
        status=schema.status,
        raw_payload=data,
    )

    if error:
        status_code = 404 if "not found" in error.lower() else 400
        return jsonify({"error": error}), status_code

    return jsonify({
        "payment": payment.to_dict(),
        "message": f"Payment {payment.status}",
    })


@payments_bp.route("/test-success/<booking_id>", methods=["POST"])
def test_payment_success(booking_id: str):
    """
    Test endpoint to simulate successful payment.
    Only available in development mode.

    Request:
        POST /api/payments/test-success/<booking_id>

    Response:
        200: { "payment": {...}, "message": "Payment simulated" }
    """
    from flask import current_app

    if not current_app.debug:
        return jsonify({"error": "Only available in development mode"}), 403

    payment, error = PaymentService.process_webhook(
        provider="manual",
        payment_id=f"test_{booking_id}",
        booking_id=booking_id,
        amount_rub=0,  # Will be filled from booking
        status="succeeded",
        raw_payload={"test": True},
    )

    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "payment": payment.to_dict(),
        "message": "Payment simulated successfully",
    })


