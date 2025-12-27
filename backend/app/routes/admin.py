"""
Admin Routes
Handles administrative functions like nutritionist verification.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from app.extensions import db
from app.models import NutritionistProfile, NutritionistDocument
from app.services.notifications import NotificationService


admin_bp = Blueprint("admin", __name__)


def require_admin():
    """Check if current user is admin."""
    claims = get_jwt()
    role = claims.get("role", "client")
    if role != "admin":
        return jsonify({"error": "Admin access required"}), 403
    return None


@admin_bp.route("/nutritionists", methods=["GET"])
@jwt_required()
def list_pending_nutritionists():
    """
    List nutritionists pending verification.

    Request:
        GET /api/admin/nutritionists?status=pending
        Authorization: Bearer <admin_token>

    Response:
        200: { "nutritionists": [...] }
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    status = request.args.get("status", "pending")

    nutritionists = NutritionistProfile.query.filter_by(
        verification_status=status
    ).order_by(NutritionistProfile.submitted_at.desc()).all()

    return jsonify({
        "nutritionists": [n.to_dict(include_profile=True) for n in nutritionists],
    })


@admin_bp.route("/nutritionists/<nutritionist_id>", methods=["GET"])
@jwt_required()
def get_nutritionist_admin(nutritionist_id: str):
    """
    Get nutritionist details for admin review.

    Request:
        GET /api/admin/nutritionists/<id>
        Authorization: Bearer <admin_token>

    Response:
        200: { "nutritionist": {...}, "documents": [...] }
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    documents = NutritionistDocument.query.filter_by(
        nutritionist_id=nutritionist_id
    ).all()

    return jsonify({
        "nutritionist": nutritionist.to_dict(include_profile=True),
        "documents": [d.to_dict() for d in documents],
    })


@admin_bp.route("/nutritionists/<nutritionist_id>/approve", methods=["POST"])
@jwt_required()
def approve_nutritionist(nutritionist_id: str):
    """
    Approve nutritionist verification.

    Request:
        POST /api/admin/nutritionists/<id>/approve
        Authorization: Bearer <admin_token>
        {
            "note": "Optional approval note"
        }

    Response:
        200: { "nutritionist": {...}, "message": "Nutritionist approved" }
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    if nutritionist.verification_status not in ("pending", "needs_update"):
        return jsonify({
            "error": f"Cannot approve nutritionist with status: {nutritionist.verification_status}"
        }), 400

    nutritionist.verification_status = "approved"
    nutritionist.verified_at = datetime.utcnow()
    nutritionist.is_active = True

    db.session.commit()

    NotificationService.nutritionist_approved(nutritionist_id)

    return jsonify({
        "nutritionist": nutritionist.to_dict(include_profile=True),
        "message": "Nutritionist approved successfully",
    })


@admin_bp.route("/nutritionists/<nutritionist_id>/reject", methods=["POST"])
@jwt_required()
def reject_nutritionist(nutritionist_id: str):
    """
    Reject nutritionist verification.

    Request:
        POST /api/admin/nutritionists/<id>/reject
        Authorization: Bearer <admin_token>
        {
            "reason": "Required rejection reason"
        }

    Response:
        200: { "nutritionist": {...}, "message": "Nutritionist rejected" }
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    data = request.get_json() or {}
    reason = data.get("reason")

    if not reason:
        return jsonify({"error": "Rejection reason is required"}), 400

    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    if nutritionist.verification_status not in ("pending", "needs_update"):
        return jsonify({
            "error": f"Cannot reject nutritionist with status: {nutritionist.verification_status}"
        }), 400

    nutritionist.verification_status = "rejected"
    nutritionist.is_active = False

    db.session.commit()

    NotificationService.nutritionist_rejected(nutritionist_id, reason)

    return jsonify({
        "nutritionist": nutritionist.to_dict(include_profile=True),
        "message": "Nutritionist rejected",
    })


@admin_bp.route("/nutritionists/<nutritionist_id>/request-update", methods=["POST"])
@jwt_required()
def request_update(nutritionist_id: str):
    """
    Request updates from nutritionist before approval.

    Request:
        POST /api/admin/nutritionists/<id>/request-update
        Authorization: Bearer <admin_token>
        {
            "notes": "Please update your bio and upload diploma"
        }

    Response:
        200: { "nutritionist": {...}, "message": "Update requested" }
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    data = request.get_json() or {}
    notes = data.get("notes")

    if not notes:
        return jsonify({"error": "Notes are required"}), 400

    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    nutritionist.verification_status = "needs_update"

    db.session.commit()

    # In a real app, we would store these notes somewhere
    # For now, just log them
    NotificationService.nutritionist_rejected(nutritionist_id, f"Updates needed: {notes}")

    return jsonify({
        "nutritionist": nutritionist.to_dict(include_profile=True),
        "message": "Update request sent",
    })


@admin_bp.route("/documents/<document_id>/review", methods=["POST"])
@jwt_required()
def review_document(document_id: str):
    """
    Review a nutritionist document.

    Request:
        POST /api/admin/documents/<id>/review
        Authorization: Bearer <admin_token>
        {
            "status": "accepted",  // or "rejected"
            "note": "Optional review note"
        }

    Response:
        200: { "document": {...} }
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    data = request.get_json() or {}
    status = data.get("status")
    note = data.get("note")

    if status not in ("accepted", "rejected"):
        return jsonify({"error": "Status must be 'accepted' or 'rejected'"}), 400

    document = NutritionistDocument.query.get(document_id)
    if not document:
        return jsonify({"error": "Document not found"}), 404

    document.status = status
    document.review_note = note

    db.session.commit()

    NotificationService.document_reviewed(document_id, status, note)

    return jsonify({
        "document": document.to_dict(),
    })


