"""
Tests for public endpoints.
Covers nutritionist visibility and is_active checks.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot


@pytest.fixture
def test_nutritionist_active(session, app):
    """Create an active approved nutritionist for testing."""
    with app.app_context():
        profile = Profile(
            telegram_user_id=111111111,
            full_name="Active Nutritionist",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()

        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
            bio="Active bio",
            specializations=["weight_management"],
            verification_status="approved",
            is_active=True,
            verified_at=datetime.utcnow(),
        )
        session.add(nutritionist)
        session.commit()
        return nutritionist


@pytest.fixture
def test_nutritionist_disabled(session, app):
    """Create a disabled approved nutritionist for testing."""
    with app.app_context():
        profile = Profile(
            telegram_user_id=222222222,
            full_name="Disabled Nutritionist",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()

        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
            bio="Disabled bio",
            specializations=["diabetes"],
            verification_status="approved",
            is_active=False,  # Disabled
            verified_at=datetime.utcnow(),
        )
        session.add(nutritionist)
        session.commit()
        return nutritionist


@pytest.fixture
def test_service(session, app, test_nutritionist_active):
    """Create a service for the active nutritionist."""
    with app.app_context():
        service = Service(
            nutritionist_id=test_nutritionist_active.nutritionist_id,
            title="Test Service",
            duration_minutes=60,
            price_rub=3000,
            is_active=True,
        )
        session.add(service)
        session.commit()
        return service


@pytest.fixture
def test_slot(session, app, test_nutritionist_active):
    """Create an availability slot for the active nutritionist."""
    with app.app_context():
        start_at = datetime.now(timezone.utc) + timedelta(days=1)
        slot = AvailabilitySlot(
            nutritionist_id=test_nutritionist_active.nutritionist_id,
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
            status="free",
        )
        session.add(slot)
        session.commit()
        return slot


class TestPublicGetNutritionist:
    """Test GET /api/public/nutritionists/<id> endpoint."""

    def test_get_active_nutritionist(self, client, test_nutritionist_active):
        """Test getting an active approved nutritionist."""
        nutri_id = str(test_nutritionist_active.nutritionist_id)
        response = client.get(f"/api/public/nutritionists/{nutri_id}")
        assert response.status_code == 200
        data = response.json
        assert "nutritionist" in data
        assert data["nutritionist"]["nutritionist_id"] == nutri_id
        assert data["nutritionist"]["is_active"] is True

    def test_get_disabled_nutritionist(self, client, test_nutritionist_disabled):
        """Test getting a disabled nutritionist should return 404."""
        nutri_id = str(test_nutritionist_disabled.nutritionist_id)
        response = client.get(f"/api/public/nutritionists/{nutri_id}")
        assert response.status_code == 404
        assert "not found" in response.json.get("error", "").lower()

    def test_get_pending_nutritionist(self, client, session, app):
        """Test getting a pending nutritionist should return 404."""
        with app.app_context():
            profile = Profile(
                telegram_user_id=333333333,
                full_name="Pending Nutritionist",
                role="nutritionist",
            )
            session.add(profile)
            session.flush()

            nutritionist = NutritionistProfile(
                nutritionist_id=profile.id,
                verification_status="pending",
                is_active=True,
            )
            session.add(nutritionist)
            session.commit()
            nutri_id = str(nutritionist.nutritionist_id)

        response = client.get(f"/api/public/nutritionists/{nutri_id}")
        assert response.status_code == 404

    def test_get_nonexistent_nutritionist(self, client):
        """Test getting non-existent nutritionist."""
        fake_id = str(uuid4())
        response = client.get(f"/api/public/nutritionists/{fake_id}")
        assert response.status_code == 404


class TestPublicListServices:
    """Test GET /api/public/nutritionists/<id>/services endpoint."""

    def test_list_services_active_nutritionist(self, client, test_nutritionist_active, test_service):
        """Test listing services for an active nutritionist."""
        nutri_id = str(test_nutritionist_active.nutritionist_id)
        response = client.get(f"/api/public/nutritionists/{nutri_id}/services")
        assert response.status_code == 200
        data = response.json
        assert "services" in data
        assert len(data["services"]) >= 1

    def test_list_services_disabled_nutritionist(self, client, test_nutritionist_disabled):
        """Test listing services for a disabled nutritionist should return 404."""
        nutri_id = str(test_nutritionist_disabled.nutritionist_id)
        response = client.get(f"/api/public/nutritionists/{nutri_id}/services")
        assert response.status_code == 404
        assert "not found" in response.json.get("error", "").lower()

    def test_list_services_pending_nutritionist(self, client, session, app):
        """Test listing services for a pending nutritionist should return 404."""
        with app.app_context():
            profile = Profile(
                telegram_user_id=444444444,
                full_name="Pending Nutritionist",
                role="nutritionist",
            )
            session.add(profile)
            session.flush()

            nutritionist = NutritionistProfile(
                nutritionist_id=profile.id,
                verification_status="pending",
                is_active=True,
            )
            session.add(nutritionist)
            session.commit()
            nutri_id = str(nutritionist.nutritionist_id)

        response = client.get(f"/api/public/nutritionists/{nutri_id}/services")
        assert response.status_code == 404


class TestPublicListSlots:
    """Test GET /api/public/nutritionists/<id>/slots endpoint."""

    def test_list_slots_active_nutritionist(self, client, test_nutritionist_active, test_slot):
        """Test listing slots for an active nutritionist."""
        nutri_id = str(test_nutritionist_active.nutritionist_id)
        response = client.get(f"/api/public/nutritionists/{nutri_id}/slots")
        assert response.status_code == 200
        data = response.json
        assert "slots" in data
        assert len(data["slots"]) >= 1

    def test_list_slots_disabled_nutritionist(self, client, test_nutritionist_disabled):
        """Test listing slots for a disabled nutritionist should return 404."""
        nutri_id = str(test_nutritionist_disabled.nutritionist_id)
        response = client.get(f"/api/public/nutritionists/{nutri_id}/slots")
        assert response.status_code == 404
        assert "not found" in response.json.get("error", "").lower()

    def test_list_slots_pending_nutritionist(self, client, session, app):
        """Test listing slots for a pending nutritionist should return 404."""
        with app.app_context():
            profile = Profile(
                telegram_user_id=555555555,
                full_name="Pending Nutritionist",
                role="nutritionist",
            )
            session.add(profile)
            session.flush()

            nutritionist = NutritionistProfile(
                nutritionist_id=profile.id,
                verification_status="pending",
                is_active=True,
            )
            session.add(nutritionist)
            session.commit()
            nutri_id = str(nutritionist.nutritionist_id)

        response = client.get(f"/api/public/nutritionists/{nutri_id}/slots")
        assert response.status_code == 404

