"""
Admin Routes
Handles administrative functions like nutritionist verification.
"""

import os
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt, create_access_token

from app.extensions import db
from app.models import NutritionistProfile, NutritionistDocument, Profile
from app.services.notifications import NotificationService


logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__)


# Admin credentials (in production, use proper user management)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@nutrimatch.io")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")  # Change in production!


def require_admin():
    """Check if current user is admin."""
    claims = get_jwt()
    role = claims.get("role", "client")
    if role != "admin":
        return jsonify({"error": "Admin access required"}), 403
    return None


@admin_bp.route("/auth/login", methods=["POST"])
def admin_login():
    """
    Admin login endpoint.

    Request:
        POST /api/admin/auth/login
        {
            "email": "admin@nutrimatch.io",
            "password": "secret"
        }

    Response:
        200: { "access_token": "...", "token_type": "bearer", "user": {...} }
        401: { "error": "Invalid credentials" }
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Validate credentials
    if email != ADMIN_EMAIL.lower() or password != ADMIN_PASSWORD:
        logger.warning(f"Failed admin login attempt for email: {email}")
        return jsonify({"error": "Invalid credentials"}), 401

    # Create JWT token with admin role
    access_token = create_access_token(
        identity="admin",
        additional_claims={
            "role": "admin",
            "email": email,
        },
    )

    logger.info(f"Admin login successful: {email}")

    return jsonify({
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": "admin",
            "email": email,
            "name": "Administrator",
            "role": "admin",
        },
    })


@admin_bp.route("/auth/me", methods=["GET"])
@jwt_required()
def admin_me():
    """
    Get current admin user info.

    Request:
        GET /api/admin/auth/me
        Authorization: Bearer <admin_token>

    Response:
        200: { "user": {...} }
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    claims = get_jwt()
    return jsonify({
        "user": {
            "id": "admin",
            "email": claims.get("email", ""),
            "name": "Administrator",
            "role": "admin",
        },
    })


@admin_bp.route("/auth/logout", methods=["POST"])
@jwt_required()
def admin_logout():
    """
    Admin logout endpoint (for token invalidation if needed).

    Request:
        POST /api/admin/auth/logout
        Authorization: Bearer <admin_token>

    Response:
        200: { "message": "Logged out" }
    """
    # In a real app, you might want to blacklist the token
    return jsonify({"message": "Logged out"})


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


