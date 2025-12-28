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
    Create a booking and hold the slot for payment.
    Slot is held for BOOKING_HOLD_MINUTES (default 10) minutes.
    Uses row-level locking to prevent race conditions.

    Request:
        POST /api/bookings
        Authorization: Bearer <token>
        {
            "service_id": "uuid",
            "slot_id": "uuid",
            "client_note": "optional note"
        }

    Response:
        201: {
            "booking": {...},
            "payment": {
                "payment_id": "...",
                "provider": "mock",
                "payment_url": "...",
                "amount_rub": 3000,
                "currency": "RUB",
                "expires_at": "..."
            }
        }
        400: Validation error or slot unavailable
        409: Slot already taken (race condition)
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


@bookings_bp.route("/<booking_id>/mark-paid", methods=["POST"])
@jwt_required()
def mark_booking_paid(booking_id: str):
    """
    Mark a booking as paid (DEV shortcut).
    
    This endpoint is preserved for backward compatibility and development.
    Internally, it routes through the payment abstraction layer.
    
    IMPORTANT: In production with real payment providers, this endpoint
    should be disabled. Payments should go through proper webhook flow.
    
    Atomic operation with row locks:
    - Locks booking, ensures pending_payment
    - Locks slot, ensures held and not expired
    - booking -> paid, set paid_at
    - slot -> booked, clear hold_expires_at
    - payment -> succeeded

    Request:
        POST /api/bookings/<id>/mark-paid
        Authorization: Bearer <token>

    Response:
        200: { "booking": {...}, "message": "Payment confirmed" }
        400: Cannot mark as paid (wrong status or expired)
        403: Not available in production (when real provider is configured)
        404: Not found
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
    Cancel a booking and release the slot.
    Only pending_payment bookings can be cancelled by clients.
    Paid bookings cannot be cancelled (must contact support for refunds).

    Request:
        POST /api/bookings/<id>/cancel
        Authorization: Bearer <token>
        {
            "reason": "Optional cancellation reason"
        }

    Response:
        200: { "booking": {...}, "message": "Booking cancelled" }
        400: Cannot cancel (paid booking or other error)
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

    logger.info(f"Booking cancelled: id={booking.id}, client={current_user_id}")

    return jsonify({
        "booking": booking.to_dict(include_relations=True),
        "message": "Booking cancelled successfully",
    })


@bookings_bp.route("/release-expired-holds", methods=["POST"])
def release_expired_holds():
    """
    Release expired slot holds.
    Designed to be called by a cron job.
    Idempotent and safe for concurrent execution.

    Request:
        POST /api/bookings/release-expired-holds

    Response:
        200: { "released_count": 5, "message": "..." }
    """
    # In production, this should be protected by a secret key or internal network
    # For now, we allow it for simplicity

    released_count = BookingHoldService.release_expired_holds()

    logger.info(f"Released {released_count} expired holds via cron endpoint")

    return jsonify({
        "released_count": released_count,
        "message": f"Released {released_count} expired holds",
    })
