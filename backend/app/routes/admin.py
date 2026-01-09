"""
Admin Routes
Handles administrative functions like nutritionist verification and booking management.
"""

import os
import logging
from datetime import datetime, date
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt, create_access_token
from sqlalchemy import or_, and_

from app.extensions import db
from app.models import NutritionistProfile, NutritionistDocument, Profile, Booking, AvailabilitySlot, Service, Payment, Review
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
    Вход администратора
    ---
    tags:
      - Admin
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              format: email
              example: admin@nutrimatch.io
            password:
              type: string
              format: password
    responses:
      200:
        description: Успешная авторизация
        schema:
          type: object
          properties:
            access_token:
              type: string
            token_type:
              type: string
              example: bearer
            user:
              type: object
              properties:
                id:
                  type: string
                email:
                  type: string
                name:
                  type: string
                role:
                  type: string
                  example: admin
      400:
        description: Email и password обязательны
      401:
        description: Неверные учётные данные
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
    Список нутрициологов для модерации
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    produces:
      - application/json
    parameters:
      - name: status
        in: query
        type: string
        enum: [draft, pending, approved, rejected, needs_update]
        default: pending
        description: Фильтр по статусу верификации
    responses:
      200:
        description: Список нутрициологов
        schema:
          type: object
          properties:
            nutritionists:
              type: array
              items:
                $ref: '#/definitions/Nutritionist'
      403:
        description: Требуются права администратора
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
    Одобрить нутрициолога
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - in: body
        name: body
        schema:
          type: object
          properties:
            note:
              type: string
              description: Примечание к одобрению
    responses:
      200:
        description: Нутрициолог одобрен
        schema:
          type: object
          properties:
            nutritionist:
              $ref: '#/definitions/Nutritionist'
            message:
              type: string
      400:
        description: Невозможно одобрить с текущим статусом
      403:
        description: Требуются права администратора
      404:
        description: Нутрициолог не найден
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
    Отклонить нутрициолога
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: nutritionist_id
        in: path
        required: true
        type: string
        description: UUID нутрициолога
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/AdminRejectRequest'
    responses:
      200:
        description: Нутрициолог отклонён
        schema:
          type: object
          properties:
            nutritionist:
              $ref: '#/definitions/Nutritionist'
            message:
              type: string
      400:
        description: Причина обязательна или невозможно отклонить с текущим статусом
      403:
        description: Требуются права администратора
      404:
        description: Нутрициолог не найден
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


@admin_bp.route("/nutritionists/<nutritionist_id>/disable", methods=["POST"])
@jwt_required()
def disable_nutritionist(nutritionist_id: str):
    """
    Disable an approved nutritionist.

    Request:
        POST /api/admin/nutritionists/<id>/disable
        Authorization: Bearer <admin_token>

    Response:
        200: { "nutritionist": {...}, "message": "Nutritionist disabled" }
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    nutritionist = NutritionistProfile.query.get(nutritionist_id)
    if not nutritionist:
        return jsonify({"error": "Nutritionist not found"}), 404

    if nutritionist.verification_status != "approved":
        return jsonify({
            "error": f"Cannot disable nutritionist with status: {nutritionist.verification_status}"
        }), 400

    nutritionist.is_active = False

    db.session.commit()

    logger.info(f"Nutritionist {nutritionist_id} disabled by admin")

    return jsonify({
        "nutritionist": nutritionist.to_dict(include_profile=True),
        "message": "Nutritionist disabled successfully",
    })


@admin_bp.route("/documents/<document_id>/url", methods=["GET"])
@jwt_required()
def get_document_url(document_id: str):
    """
    Get a signed URL for downloading a document.

    Request:
        GET /api/admin/documents/<id>/url
        Authorization: Bearer <admin_token>

    Response:
        200: { "url": "..." }
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    document = NutritionistDocument.query.get(document_id)
    if not document:
        return jsonify({"error": "Document not found"}), 404

    # In a real app, generate a signed URL from Supabase or S3
    # For now, return the file_path directly
    file_url = document.file_path

    return jsonify({"url": file_url})


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


# ============================================================================
# BOOKING MANAGEMENT
# ============================================================================


@admin_bp.route("/bookings", methods=["GET"])
@jwt_required()
def list_bookings():
    """
    List all bookings with optional filters.

    Request:
        GET /api/admin/bookings?status=paid&date_from=2024-01-01&date_to=2024-12-31&page=1&limit=20
        Authorization: Bearer <admin_token>

    Response:
        200: { "bookings": [...], "total": 100, "page": 1, "pages": 5 }
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    # Parse query parameters
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    status = request.args.get("status")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    # Build query
    query = Booking.query

    # Apply filters
    if status:
        query = query.filter(Booking.status == status)

    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from)
            query = query.filter(Booking.created_at >= from_date)
        except ValueError:
            pass

    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to)
            # Add 1 day to include the end date
            to_date = datetime.combine(to_date.date(), datetime.max.time())
            query = query.filter(Booking.created_at <= to_date)
        except ValueError:
            pass

    # Order by most recent first
    query = query.order_by(Booking.created_at.desc())

    # Paginate
    total = query.count()
    pages = (total + limit - 1) // limit
    bookings = query.offset((page - 1) * limit).limit(limit).all()

    # Serialize with expanded relations
    booking_list = []
    for booking in bookings:
        booking_data = booking.to_dict()
        
        # Add client info
        if booking.client:
            booking_data["client"] = {
                "id": str(booking.client.id),
                "full_name": booking.client.full_name,
                "photo_url": booking.client.photo_url,
                "telegram_user_id": booking.client.telegram_user_id,
            }
        
        # Add nutritionist info
        if booking.nutritionist_profile:
            booking_data["nutritionist"] = {
                "id": str(booking.nutritionist_profile.nutritionist_id),
                "full_name": booking.nutritionist_profile.profile.full_name if booking.nutritionist_profile.profile else "Unknown",
            }
        
        # Add slot info
        if booking.slot:
            booking_data["slot"] = booking.slot.to_dict()
        
        # Add service info
        if booking.service:
            booking_data["service"] = {
                "id": str(booking.service.id),
                "title": booking.service.title,
                "duration_minutes": booking.service.duration_minutes,
            }
        
        # Add payment info
        if booking.payment:
            booking_data["payment"] = booking.payment.to_dict()
        
        booking_list.append(booking_data)

    return jsonify({
        "bookings": booking_list,
        "total": total,
        "page": page,
        "pages": pages,
    })


@admin_bp.route("/bookings/<booking_id>", methods=["GET"])
@jwt_required()
def get_booking_admin(booking_id: str):
    """
    Get detailed booking information for admin.

    Request:
        GET /api/admin/bookings/<id>
        Authorization: Bearer <admin_token>

    Response:
        200: { "booking": {...} }
        404: Not found
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    # Build comprehensive response
    booking_data = booking.to_dict()
    
    # Add client info
    if booking.client:
        booking_data["client"] = booking.client.to_dict()
    
    # Add nutritionist info
    if booking.nutritionist_profile:
        booking_data["nutritionist"] = booking.nutritionist_profile.to_dict(include_profile=True)
    
    # Add slot info
    if booking.slot:
        booking_data["slot"] = booking.slot.to_dict()
    
    # Add service info
    if booking.service:
        booking_data["service"] = booking.service.to_dict()
    
    # Add payment info
    if booking.payment:
        booking_data["payment"] = booking.payment.to_dict()

    return jsonify({
        "booking": booking_data,
    })


@admin_bp.route("/bookings/<booking_id>/cancel", methods=["POST"])
@jwt_required()
def admin_cancel_booking(booking_id: str):
    """
    Admin cancel a booking.

    Request:
        POST /api/admin/bookings/<id>/cancel
        Authorization: Bearer <admin_token>
        {
            "reason": "Optional cancellation reason"
        }

    Response:
        200: { "booking": {...}, "message": "Booking cancelled" }
        400: Cannot cancel
        404: Not found
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    data = request.get_json() or {}
    reason = data.get("reason", "Cancelled by admin")

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if booking.status in ("cancelled", "completed", "refunded"):
        return jsonify({
            "error": f"Cannot cancel booking with status: {booking.status}"
        }), 400

    # Update booking status
    booking.status = "cancelled"
    booking.cancelled_at = datetime.utcnow()

    # Release the slot if it was held/booked
    if booking.slot:
        booking.slot.status = "free"
        booking.slot.hold_expires_at = None

    db.session.commit()

    # Notify parties
    NotificationService.booking_cancelled(booking, reason)

    logger.info(f"Admin cancelled booking: {booking_id}, reason: {reason}")

    return jsonify({
        "booking": booking.to_dict(include_relations=True),
        "message": "Booking cancelled successfully",
    })


@admin_bp.route("/bookings/<booking_id>/complete", methods=["POST"])
@jwt_required()
def admin_complete_booking(booking_id: str):
    """
    Admin mark a booking as completed.

    Request:
        POST /api/admin/bookings/<id>/complete
        Authorization: Bearer <admin_token>
        {
            "notes": "Optional completion notes"
        }

    Response:
        200: { "booking": {...}, "message": "Booking completed" }
        400: Cannot complete
        404: Not found
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    data = request.get_json() or {}
    notes = data.get("notes")

    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    if booking.status != "paid":
        return jsonify({
            "error": f"Cannot complete booking with status: {booking.status}. Only paid bookings can be marked as completed."
        }), 400

    # Update booking status
    booking.status = "completed"

    db.session.commit()

    logger.info(f"Admin marked booking as completed: {booking_id}")

    return jsonify({
        "booking": booking.to_dict(include_relations=True),
        "message": "Booking marked as completed",
    })


@admin_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    """
    Статистика для дашборда
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    produces:
      - application/json
    responses:
      200:
        description: Статистика платформы
        schema:
          type: object
          properties:
            total_users:
              type: integer
              example: 100
            total_nutritionists:
              type: integer
              example: 20
            pending_verifications:
              type: integer
              example: 5
            total_bookings:
              type: integer
              example: 150
            revenue_this_month:
              type: integer
              description: Выручка за текущий месяц (в рублях)
              example: 150000
      403:
        description: Требуются права администратора
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    from sqlalchemy import func

    # Count users (clients)
    total_users = Profile.query.filter(Profile.role == "client").count()

    # Count nutritionists
    total_nutritionists = NutritionistProfile.query.count()

    # Count pending verifications
    pending_verifications = NutritionistProfile.query.filter(
        NutritionistProfile.verification_status == "pending"
    ).count()

    # Count bookings
    total_bookings = Booking.query.count()

    # Calculate revenue this month (from completed/paid bookings)
    first_of_month = date.today().replace(day=1)
    revenue_this_month = db.session.query(
        func.coalesce(func.sum(Booking.price_rub), 0)
    ).filter(
        Booking.status.in_(["paid", "completed"]),
        Booking.paid_at >= first_of_month
    ).scalar() or 0

    return jsonify({
        "total_users": total_users,
        "total_nutritionists": total_nutritionists,
        "pending_verifications": pending_verifications,
        "total_bookings": total_bookings,
        "revenue_this_month": revenue_this_month,
    })


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    """
    Список пользователей с активностью
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    parameters:
      - name: page
        in: query
        type: integer
        description: Page number (default: 1)
      - name: limit
        in: query
        type: integer
        description: Page size (default: 50)
    responses:
      200:
        description: Список пользователей
      403:
        description: Требуются права администратора
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    page = request.args.get("page", type=int, default=1)
    limit = request.args.get("limit", type=int, default=50)
    limit = max(1, min(limit, 200))
    offset = (page - 1) * limit

    total = Profile.query.count()
    profiles = Profile.query.order_by(Profile.created_at.desc()).offset(offset).limit(limit).all()

    def last_seen(profile: Profile):
        events = [
            ("mini_app", profile.last_mini_app_at),
            ("bot_start", profile.last_bot_start_at),
            ("nutritionist_intent", profile.last_nutritionist_intent_at),
        ]
        events = [(name, ts) for name, ts in events if ts]
        if not events:
            return None, None
        name, ts = max(events, key=lambda item: item[1])
        return name, ts

    users = []
    for profile in profiles:
        source, last_seen_at = last_seen(profile)
        data = profile.to_dict()
        data.update({
            "last_seen_at": last_seen_at.isoformat() if last_seen_at else None,
            "last_seen_source": source,
            "has_nutritionist_profile": profile.nutritionist_profile is not None,
        })
        users.append(data)

    stats = {
        "total_users": total,
        "mini_app_users": Profile.query.filter(Profile.last_mini_app_at.isnot(None)).count(),
        "bot_start_users": Profile.query.filter(Profile.last_bot_start_at.isnot(None)).count(),
        "nutritionist_intent_users": Profile.query.filter(Profile.last_nutritionist_intent_at.isnot(None)).count(),
    }

    return jsonify({
        "users": users,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
        "stats": stats,
    })


# ============================================================================
# REVIEW MANAGEMENT
# ============================================================================


@admin_bp.route("/reviews", methods=["GET"])
@jwt_required()
def list_reviews_admin():
    """
    List all reviews with optional filters (admin only).
    
    Request:
        GET /api/admin/reviews?is_hidden=false&nutritionist_id=...&page=1&limit=20
        Authorization: Bearer <admin_token>
    
    Response:
        200: { "reviews": [...], "total": 100, "page": 1, "pages": 5 }
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    # Parse query parameters
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)
    is_hidden = request.args.get("is_hidden")
    nutritionist_id = request.args.get("nutritionist_id")

    # Build query
    query = Review.query

    # Apply filters
    if is_hidden is not None:
        is_hidden_bool = is_hidden.lower() == "true"
        query = query.filter(Review.is_hidden == is_hidden_bool)

    if nutritionist_id:
        query = query.filter(Review.nutritionist_id == nutritionist_id)

    # Order by most recent first
    query = query.order_by(Review.created_at.desc())

    # Paginate
    total = query.count()
    pages = (total + limit - 1) // limit
    reviews = query.offset((page - 1) * limit).limit(limit).all()

    return jsonify({
        "reviews": [r.to_dict(include_relations=True) for r in reviews],
        "total": total,
        "page": page,
        "pages": pages,
    })


@admin_bp.route("/reviews/<review_id>/hide", methods=["POST"])
@jwt_required()
def hide_review(review_id: str):
    """
    Hide a review (admin only).
    
    Request:
        POST /api/admin/reviews/<id>/hide
        Authorization: Bearer <admin_token>
    
    Response:
        200: { "review": {...}, "message": "Review hidden" }
        404: Not found
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    review.is_hidden = True
    db.session.commit()

    logger.info(f"Admin hid review: {review_id}")

    return jsonify({
        "review": review.to_dict(include_relations=True),
        "message": "Review hidden successfully",
    })


@admin_bp.route("/reviews/<review_id>/unhide", methods=["POST"])
@jwt_required()
def unhide_review(review_id: str):
    """
    Unhide a review (admin only).
    
    Request:
        POST /api/admin/reviews/<id>/unhide
        Authorization: Bearer <admin_token>
    
    Response:
        200: { "review": {...}, "message": "Review unhidden" }
        404: Not found
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    review.is_hidden = False
    db.session.commit()

    logger.info(f"Admin unhid review: {review_id}")

    return jsonify({
        "review": review.to_dict(include_relations=True),
        "message": "Review unhidden successfully",
    })


@admin_bp.route("/reviews/<review_id>", methods=["DELETE"])
@jwt_required()
def delete_review(review_id: str):
    """
    Delete a review (admin only).
    
    Request:
        DELETE /api/admin/reviews/<id>
        Authorization: Bearer <admin_token>
    
    Response:
        200: { "message": "Review deleted" }
        404: Not found
    """
    auth_error = require_admin()
    if auth_error:
        return auth_error

    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    db.session.delete(review)
    db.session.commit()

    logger.info(f"Admin deleted review: {review_id}")

    return jsonify({
        "message": "Review deleted successfully",
    })
