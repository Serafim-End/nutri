"""
Client Routes
Handles client intake forms and nutritionist matching.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from app.extensions import db
from app.models import Intake, Profile
from app.schemas.client import IntakeCreateRequest
from app.services.matching import MatchingService


clients_bp = Blueprint("clients", __name__)


@clients_bp.route("/intakes", methods=["POST"])
@jwt_required()
def create_intake():
    """
    Submit client intake questionnaire.

    Request:
        POST /api/clients/intakes
        Authorization: Bearer <token>
        {
            "goals": ["weight_loss"],
            "dietary_restrictions": ["vegetarian"],
            "budget_min": 1000,
            "budget_max": 5000,
            "preferred_schedule": "weekends",
            "health_conditions": ["diabetes"],
            "additional_notes": "..."
        }

    Response:
        201: { "intake": {...}, "message": "Intake submitted" }
        400: Validation error
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

    # Create intake
    intake = Intake(
        client_id=current_user_id,
        answers={
            "goals": schema.goals,
            "dietary_restrictions": schema.dietary_restrictions,
            "budget_min": schema.budget_min,
            "budget_max": schema.budget_max,
            "preferred_schedule": schema.preferred_schedule,
            "health_conditions": schema.health_conditions,
            "additional_notes": schema.additional_notes,
        },
    )

    db.session.add(intake)
    db.session.commit()

    return jsonify({
        "intake": intake.to_dict(),
        "message": "Intake submitted successfully",
    }), 201


@clients_bp.route("/matches", methods=["GET"])
@jwt_required()
def get_matches():
    """
    Get matched nutritionists based on intake.

    Request:
        GET /api/clients/matches?intake_id=<uuid>
        Authorization: Bearer <token>

    Response:
        200: { "matches": [...], "total": 10 }
        400: Missing intake_id
        404: Intake not found
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
    List client's own intakes.

    Request:
        GET /api/clients/intakes
        Authorization: Bearer <token>

    Response:
        200: { "intakes": [...] }
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
    List client's own bookings.

    Request:
        GET /api/clients/bookings
        Authorization: Bearer <token>

    Response:
        200: { "bookings": [...] }
    """
    from app.models import Booking

    current_user_id = get_jwt_identity()

    bookings = Booking.query.filter_by(client_id=current_user_id).order_by(
        Booking.created_at.desc()
    ).all()

    return jsonify({
        "bookings": [b.to_dict(include_relations=True) for b in bookings],
    })


