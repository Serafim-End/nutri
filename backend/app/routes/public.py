"""
Public Routes
Public endpoints for browsing nutritionists (no auth required).
"""

from datetime import datetime
from flask import Blueprint, request, jsonify

from app.models import NutritionistProfile, Service, AvailabilitySlot
from app.services.matching import MatchingService


public_bp = Blueprint("public", __name__)


@public_bp.route("/nutritionists", methods=["GET"])
def list_nutritionists():
    """
    List approved nutritionists with optional filters.

    Request:
        GET /api/public/nutritionists?specialization=diabetes&budget=5000&tags=vegetarian

    Response:
        200: { "nutritionists": [...], "total": 10 }
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
    Get nutritionist details.

    Request:
        GET /api/public/nutritionists/<id>

    Response:
        200: { "nutritionist": {...} }
        404: { "error": "Nutritionist not found" }
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)

    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    # Only show approved nutritionists publicly
    if nutritionist.verification_status != "approved":
        return jsonify({"error": "Nutritionist not found"}), 404

    return jsonify({
        "nutritionist": nutritionist.to_dict(include_profile=True),
    })


@public_bp.route("/nutritionists/<nutritionist_id>/services", methods=["GET"])
def list_services(nutritionist_id: str):
    """
    List nutritionist's active services.

    Request:
        GET /api/public/nutritionists/<id>/services

    Response:
        200: { "services": [...] }
    """
    nutritionist = NutritionistProfile.query.get(nutritionist_id)

    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    if nutritionist.verification_status != "approved":
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
    List nutritionist's available slots for a service.

    Request:
        GET /api/public/nutritionists/<id>/slots?service_id=<uuid>

    Response:
        200: { "slots": [...] }
    """
    service_id = request.args.get("service_id")

    nutritionist = NutritionistProfile.query.get(nutritionist_id)

    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    if nutritionist.verification_status != "approved":
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


