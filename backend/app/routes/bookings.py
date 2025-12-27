"""
Booking Routes
Handles booking creation, cancellation, and hold management.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from app.schemas.booking import BookingCreateRequest
from app.services.booking_hold import BookingHoldService
from app.services.payments import PaymentService
from app.models import Booking


bookings_bp = Blueprint("bookings", __name__)


@bookings_bp.route("", methods=["POST"])
@jwt_required()
def create_booking():
    """
    Create a booking and hold the slot for payment.
    Slot is held for 10 minutes by default.

    Request:
        POST /api/bookings
        Authorization: Bearer <token>
        {
            "service_id": "uuid",
            "slot_id": "uuid"
        }

    Response:
        201: {
            "booking": {...},
            "payment": {
                "payment_id": "...",
                "payment_url": "...",
                "expires_at": "..."
            }
        }
        400: Validation error or slot unavailable
    """
    current_user_id = get_jwt_identity()

    try:
        data = request.get_json() or {}
        schema = BookingCreateRequest(**data)
    except ValidationError as e:
        return jsonify({"error": "Validation error", "details": e.errors()}), 400

    # Create booking with slot hold
    booking, error = BookingHoldService.create_booking_with_hold(
        client_id=current_user_id,
        service_id=schema.service_id,
        slot_id=schema.slot_id,
    )

    if error:
        return jsonify({"error": error}), 400

    # Create payment intent
    payment_data = PaymentService.create_payment_intent(booking)

    return jsonify({
        "booking": booking.to_dict(include_relations=True),
        "payment": payment_data,
    }), 201


@bookings_bp.route("/<booking_id>", methods=["GET"])
@jwt_required()
def get_booking(booking_id: str):
    """
    Get booking details.

    Request:
        GET /api/bookings/<id>
        Authorization: Bearer <token>

    Response:
        200: { "booking": {...} }
        404: Not found
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


@bookings_bp.route("/<booking_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_booking(booking_id: str):
    """
    Cancel a booking and release the slot.

    Request:
        POST /api/bookings/<id>/cancel
        Authorization: Bearer <token>
        {
            "reason": "Optional cancellation reason"
        }

    Response:
        200: { "booking": {...}, "message": "Booking cancelled" }
        400: Cannot cancel
        404: Not found
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

    return jsonify({
        "booking": booking.to_dict(include_relations=True),
        "message": "Booking cancelled successfully",
    })


@bookings_bp.route("/release-expired-holds", methods=["POST"])
def release_expired_holds():
    """
    Release expired slot holds.
    Designed to be called by a cron job.

    Request:
        POST /api/bookings/release-expired-holds

    Response:
        200: { "released_count": 5, "message": "..." }
    """
    # In production, this should be protected by a secret key or internal network
    # For now, we allow it for simplicity

    released_count = BookingHoldService.release_expired_holds()

    return jsonify({
        "released_count": released_count,
        "message": f"Released {released_count} expired holds",
    })


