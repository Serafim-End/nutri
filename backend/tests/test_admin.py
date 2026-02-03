"""
Tests for admin endpoints.
Covers nutritionist moderation and approval workflows.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from flask_jwt_extended import create_access_token

from app.models import Profile, NutritionistProfile


@pytest.fixture
def admin_token(app):
    """Create admin JWT token for testing."""
    with app.app_context():
        token = create_access_token(
            identity="admin",
            additional_claims={
                "role": "admin",
                "email": "admin@nutrimatch.io",
            },
        )
        return token


@pytest.fixture
def admin_headers(admin_token):
    """Create admin headers for testing."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def test_nutritionist_pending(session, app):
    """Create a pending nutritionist for testing."""
    with app.app_context():
        profile = Profile(
            telegram_user_id=111111111,
            full_name="Test Nutritionist Pending",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()

        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
            bio="Test bio",
            specializations=["weight_management", "sports_nutrition"],
            verification_status="pending",
            submitted_at=datetime.utcnow(),
            is_active=False,
        )
        session.add(nutritionist)
        session.commit()
        return nutritionist


@pytest.fixture
def test_nutritionist_draft(session, app):
    """Create a draft nutritionist for testing."""
    with app.app_context():
        profile = Profile(
            telegram_user_id=222222222,
            full_name="Test Nutritionist Draft",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()

        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
            bio="Draft bio",
            specializations=["diabetes"],
            verification_status="draft",
            is_active=False,
        )
        session.add(nutritionist)
        session.commit()
        return nutritionist


class TestAdminNutritionistsList:
    """Test GET /api/admin/nutritionists endpoint."""

    def test_list_nutritionists_unauthorized(self, client):
        """Test listing nutritionists without auth."""
        response = client.get("/api/admin/nutritionists")
        assert response.status_code == 401

    def test_list_nutritionists_non_admin(self, client, auth_headers):
        """Test listing nutritionists as non-admin."""
        headers, _ = auth_headers
        response = client.get("/api/admin/nutritionists", headers=headers)
        assert response.status_code == 403
        assert "Admin access required" in response.json.get("error", "")

    def test_list_pending_nutritionists(self, client, admin_headers, test_nutritionist_pending):
        """Test listing pending nutritionists."""
        response = client.get("/api/admin/nutritionists?status=pending", headers=admin_headers)
        assert response.status_code == 200
        data = response.json
        assert "nutritionists" in data
        assert len(data["nutritionists"]) >= 1
        
        # Find our test nutritionist
        nutri = next(
            (n for n in data["nutritionists"] if n["nutritionist_id"] == str(test_nutritionist_pending.nutritionist_id)),
            None
        )
        assert nutri is not None
        
        # Check structure - should have id, full_name, created_at at root
        assert "id" in nutri
        assert nutri["id"] == str(test_nutritionist_pending.nutritionist_id)
        assert "nutritionist_id" in nutri
        assert "full_name" in nutri
        assert nutri["full_name"] == "Test Nutritionist Pending"
        assert "created_at" in nutri
        assert "verification_status" in nutri
        assert nutri["verification_status"] == "pending"
        assert "bio" in nutri
        assert "specializations" in nutri


class TestAdminNutritionistDetail:
    """Test GET /api/admin/nutritionists/<id> endpoint."""

    def test_get_nutritionist_unauthorized(self, client, test_nutritionist_pending):
        """Test getting nutritionist detail without auth."""
        nutri_id = str(test_nutritionist_pending.nutritionist_id)
        response = client.get(f"/api/admin/nutritionists/{nutri_id}")
        assert response.status_code == 401

    def test_get_nutritionist_not_found(self, client, admin_headers):
        """Test getting non-existent nutritionist."""
        fake_id = str(uuid4())
        response = client.get(f"/api/admin/nutritionists/{fake_id}", headers=admin_headers)
        assert response.status_code == 404
        assert "not found" in response.json.get("error", "").lower()

    def test_get_nutritionist_detail(self, client, admin_headers, test_nutritionist_pending):
        """Test getting nutritionist detail with correct structure."""
        nutri_id = str(test_nutritionist_pending.nutritionist_id)
        response = client.get(f"/api/admin/nutritionists/{nutri_id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json
        
        assert "nutritionist" in data
        nutri = data["nutritionist"]
        
        # Check structure - should have id, full_name, created_at at root
        assert "id" in nutri
        assert nutri["id"] == nutri_id
        assert "nutritionist_id" in nutri
        assert "full_name" in nutri
        assert nutri["full_name"] == "Test Nutritionist Pending"
        assert "created_at" in nutri
        assert "verification_status" in nutri
        assert nutri["verification_status"] == "pending"
        assert "bio" in nutri
        assert nutri["bio"] == "Test bio"
        assert "specializations" in nutri
        assert "documents" in data
        assert isinstance(data["documents"], list)


class TestAdminApproveNutritionist:
    """Test POST /api/admin/nutritionists/<id>/approve endpoint."""

    def test_approve_unauthorized(self, client, test_nutritionist_pending):
        """Test approving nutritionist without auth."""
        nutri_id = str(test_nutritionist_pending.nutritionist_id)
        response = client.post(f"/api/admin/nutritionists/{nutri_id}/approve")
        assert response.status_code == 401

    def test_approve_not_found(self, client, admin_headers):
        """Test approving non-existent nutritionist."""
        fake_id = str(uuid4())
        response = client.post(f"/api/admin/nutritionists/{fake_id}/approve", headers=admin_headers)
        assert response.status_code == 404

    def test_approve_pending_nutritionist(self, client, admin_headers, test_nutritionist_pending, session, app):
        """Test approving a pending nutritionist."""
        nutri_id = str(test_nutritionist_pending.nutritionist_id)
        response = client.post(
            f"/api/admin/nutritionists/{nutri_id}/approve",
            headers=admin_headers,
            json={"note": "Looks good!"}
        )
        assert response.status_code == 200
        data = response.json
        assert "nutritionist" in data
        assert "message" in data
        
        nutri_data = data["nutritionist"]
        assert nutri_data["verification_status"] == "approved"
        assert nutri_data["is_active"] is True
        assert nutri_data["verified_at"] is not None
        
        # Verify in database
        with app.app_context():
            session.refresh(test_nutritionist_pending)
            assert test_nutritionist_pending.verification_status == "approved"
            assert test_nutritionist_pending.is_active is True
            assert test_nutritionist_pending.verified_at is not None

    def test_approve_already_approved(self, client, admin_headers, session, app):
        """Test approving an already approved nutritionist."""
        with app.app_context():
            profile = Profile(
                telegram_user_id=333333333,
                full_name="Already Approved",
                role="nutritionist",
            )
            session.add(profile)
            session.flush()

            nutritionist = NutritionistProfile(
                nutritionist_id=profile.id,
                verification_status="approved",
                is_active=True,
                verified_at=datetime.utcnow(),
            )
            session.add(nutritionist)
            session.commit()
            nutri_id = str(nutritionist.nutritionist_id)

        response = client.post(
            f"/api/admin/nutritionists/{nutri_id}/approve",
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "Cannot approve" in response.json.get("error", "")


class TestAdminRejectNutritionist:
    """Test POST /api/admin/nutritionists/<id>/reject endpoint."""

    def test_reject_unauthorized(self, client, test_nutritionist_pending):
        """Test rejecting nutritionist without auth."""
        nutri_id = str(test_nutritionist_pending.nutritionist_id)
        response = client.post(f"/api/admin/nutritionists/{nutri_id}/reject")
        assert response.status_code == 401

    def test_reject_missing_reason(self, client, admin_headers, test_nutritionist_pending):
        """Test rejecting nutritionist without reason."""
        nutri_id = str(test_nutritionist_pending.nutritionist_id)
        response = client.post(
            f"/api/admin/nutritionists/{nutri_id}/reject",
            headers=admin_headers,
            json={}
        )
        assert response.status_code == 400
        assert "reason is required" in response.json.get("error", "")

    def test_reject_pending_nutritionist(self, client, admin_headers, test_nutritionist_pending, session, app):
        """Test rejecting a pending nutritionist."""
        nutri_id = str(test_nutritionist_pending.nutritionist_id)
        response = client.post(
            f"/api/admin/nutritionists/{nutri_id}/reject",
            headers=admin_headers,
            json={"reason": "Incomplete documentation"}
        )
        assert response.status_code == 200
        data = response.json
        assert "nutritionist" in data
        assert "message" in data
        
        nutri_data = data["nutritionist"]
        assert nutri_data["verification_status"] == "rejected"
        assert nutri_data["is_active"] is False
        
        # Verify in database
        with app.app_context():
            session.refresh(test_nutritionist_pending)
            assert test_nutritionist_pending.verification_status == "rejected"
            assert test_nutritionist_pending.is_active is False


class TestAdminDeleteNutritionist:
    """Test DELETE /api/admin/nutritionists/<id> endpoint."""

    def test_delete_unauthorized(self, client, test_nutritionist_pending):
        """Test deleting nutritionist without auth."""
        nutri_id = str(test_nutritionist_pending.nutritionist_id)
        response = client.delete(f"/api/admin/nutritionists/{nutri_id}")
        assert response.status_code == 401

    def test_delete_not_found(self, client, admin_headers):
        """Test deleting non-existent nutritionist."""
        fake_id = str(uuid4())
        response = client.delete(f"/api/admin/nutritionists/{fake_id}", headers=admin_headers)
        assert response.status_code == 404

    def test_delete_nutritionist(self, client, admin_headers, test_nutritionist_pending, session, app):
        """Test deleting nutritionist and profile."""
        nutri_uuid = test_nutritionist_pending.nutritionist_id
        nutri_id = str(nutri_uuid)
        response = client.delete(f"/api/admin/nutritionists/{nutri_id}", headers=admin_headers)
        assert response.status_code == 200
        assert "deleted" in response.json.get("message", "").lower()

        with app.app_context():
            session.expire_all()
            assert session.query(NutritionistProfile.nutritionist_id).filter_by(
                nutritionist_id=nutri_uuid
            ).first() is None
            assert session.query(Profile.id).filter_by(id=nutri_uuid).first() is None
