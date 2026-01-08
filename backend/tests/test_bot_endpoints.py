"""
Contract tests for bot API endpoints.
Verifies the API contract between Telegram bot and backend.
"""

import pytest
import os
from flask import Flask


# Set test service token
TEST_SERVICE_TOKEN = "test-bot-service-token"


@pytest.fixture(autouse=True)
def set_service_token():
    """Set service token for tests."""
    old_token = os.environ.get("BOT_SERVICE_TOKEN")
    os.environ["BOT_SERVICE_TOKEN"] = TEST_SERVICE_TOKEN
    yield
    if old_token:
        os.environ["BOT_SERVICE_TOKEN"] = old_token
    else:
        os.environ.pop("BOT_SERVICE_TOKEN", None)


def get_service_headers():
    """Get headers with service token."""
    return {
        "X-Service-Token": TEST_SERVICE_TOKEN,
        "Content-Type": "application/json",
    }


class TestResolveTelegramUser:
    """Tests for /api/bot/resolve-telegram-user endpoint."""
    
    def test_resolve_new_user_returns_client(self, client):
        """Test that unknown user is resolved as client."""
        response = client.get(
            "/api/bot/resolve-telegram-user",
            query_string={"telegram_user_id": 999888777},
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["profile"] is None
        assert data["nutritionist"] is None
        assert data["role"] == "client"
    
    def test_resolve_existing_nutritionist(self, client, session):
        """Test that existing nutritionist is resolved correctly."""
        from app.models import Profile, NutritionistProfile
        
        # Create test nutritionist
        profile = Profile(
            telegram_user_id=123456789,
            full_name="Test Nutritionist",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()
        
        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
            verification_status="approved",
            bio="Test bio",
        )
        session.add(nutritionist)
        session.commit()
        
        # Resolve
        response = client.get(
            "/api/bot/resolve-telegram-user",
            query_string={"telegram_user_id": 123456789},
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["role"] == "nutritionist"
        assert data["profile"] is not None
        assert data["profile"]["full_name"] == "Test Nutritionist"
        assert data["nutritionist"] is not None
        assert data["nutritionist"]["verification_status"] == "approved"
    
    def test_resolve_missing_telegram_id_returns_400(self, client):
        """Test that missing telegram_user_id returns 400."""
        response = client.get(
            "/api/bot/resolve-telegram-user",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
    
    def test_resolve_without_token_returns_401(self, client):
        """Test that missing service token returns 401."""
        response = client.get(
            "/api/bot/resolve-telegram-user",
            query_string={"telegram_user_id": 123},
        )
        
        assert response.status_code == 401


class TestNutritionistUpsert:
    """Tests for /api/nutritionists/upsert endpoint."""
    
    def test_create_new_nutritionist(self, client, session):
        """Test creating a new nutritionist profile."""
        response = client.post(
            "/api/nutritionists/upsert",
            json={
                "telegram_user_id": 111222333,
                "full_name": "New Nutritionist",
                "bio": "Test bio",
                "specializations": ["weight_management"],
                "submit_for_verification": False,
            },
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["is_new"] == True
        assert data["nutritionist"] is not None
        assert data["nutritionist"]["verification_status"] == "draft"
    
    def test_update_existing_nutritionist(self, client, session):
        """Test updating an existing nutritionist profile."""
        from app.models import Profile, NutritionistProfile
        
        # Create existing nutritionist
        profile = Profile(
            telegram_user_id=444555666,
            full_name="Old Name",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()
        
        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
            verification_status="draft",
        )
        session.add(nutritionist)
        session.commit()
        
        # Update
        response = client.post(
            "/api/nutritionists/upsert",
            json={
                "telegram_user_id": 444555666,
                "full_name": "New Name",
                "bio": "Updated bio",
                "specializations": ["sports_nutrition"],
                "submit_for_verification": False,
            },
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["is_new"] == False
        assert data["nutritionist"]["bio"] == "Updated bio"
    
    def test_submit_for_verification(self, client, session):
        """Test submitting profile for verification."""
        response = client.post(
            "/api/nutritionists/upsert",
            json={
                "telegram_user_id": 777888999,
                "full_name": "Submit Test",
                "specializations": ["weight_management"],
                "submit_for_verification": True,
            },
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["nutritionist"]["verification_status"] == "pending"


class TestNutritionistServices:
    """Tests for nutritionist services endpoints."""
    
    @pytest.fixture
    def nutritionist(self, session):
        """Create test nutritionist."""
        from app.models import Profile, NutritionistProfile
        
        profile = Profile(
            telegram_user_id=999000111,
            full_name="Services Test",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()
        
        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
            verification_status="approved",
        )
        session.add(nutritionist)
        session.commit()
        
        return nutritionist
    
    def test_list_services_empty(self, client, nutritionist):
        """Test listing services when none exist."""
        response = client.get(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/services",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["services"] == []
    
    def test_create_service(self, client, nutritionist):
        """Test creating a service."""
        response = client.post(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/services",
            json={
                "title": "Test Consultation",
                "description": "Test description",
                "duration_minutes": 60,
                "price_rub": 3000,
                "is_active": True,
            },
            headers=get_service_headers(),
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data["service"]["title"] == "Test Consultation"
        assert data["service"]["price_rub"] == 3000
        assert data["service"]["duration_minutes"] == 60
    
    def test_update_service(self, client, session, nutritionist):
        """Test updating a service."""
        from app.models import Service
        
        # Create service
        service = Service(
            nutritionist_id=nutritionist.nutritionist_id,
            title="Original Title",
            duration_minutes=60,
            price_rub=3000,
            is_active=True,
        )
        session.add(service)
        session.commit()
        
        # Update
        response = client.put(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/services/{service.id}",
            json={
                "title": "Updated Title",
                "price_rub": 4000,
            },
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["service"]["title"] == "Updated Title"
        assert data["service"]["price_rub"] == 4000
    
    def test_toggle_service_active(self, client, session, nutritionist):
        """Test toggling service active status."""
        from app.models import Service
        
        # Create active service
        service = Service(
            nutritionist_id=nutritionist.nutritionist_id,
            title="Toggle Test",
            duration_minutes=60,
            price_rub=3000,
            is_active=True,
        )
        session.add(service)
        session.commit()
        
        # Deactivate
        response = client.put(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/services/{service.id}",
            json={"is_active": False},
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["service"]["is_active"] == False
    
    def test_delete_service(self, client, session, nutritionist):
        """Test deleting a service."""
        from app.models import Service
        
        # Create service
        service = Service(
            nutritionist_id=nutritionist.nutritionist_id,
            title="Delete Test",
            duration_minutes=60,
            price_rub=3000,
        )
        session.add(service)
        session.commit()
        service_id = service.id
        
        # Delete
        response = client.delete(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/services/{service_id}",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        
        # Verify deleted
        assert session.get(Service, service_id) is None
    
    def test_delete_wrong_nutritionist_service_forbidden(self, client, session, nutritionist):
        """Test that deleting another nutritionist's service is forbidden."""
        from app.models import Profile, NutritionistProfile, Service
        
        # Create another nutritionist
        other_profile = Profile(
            telegram_user_id=888777666,
            full_name="Other",
            role="nutritionist",
        )
        session.add(other_profile)
        session.flush()
        
        other_nutritionist = NutritionistProfile(
            nutritionist_id=other_profile.id,
        )
        session.add(other_nutritionist)
        
        # Create service for other nutritionist
        service = Service(
            nutritionist_id=other_profile.id,
            title="Other Service",
            duration_minutes=60,
            price_rub=3000,
        )
        session.add(service)
        session.commit()
        
        # Try to delete from wrong nutritionist
        response = client.delete(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/services/{service.id}",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 403


class TestCalendarEndpoints:
    """Tests for calendar-related endpoints."""
    
    @pytest.fixture
    def nutritionist(self, session):
        """Create test nutritionist."""
        from app.models import Profile, NutritionistProfile
        
        profile = Profile(
            telegram_user_id=123123123,
            full_name="Calendar Test",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()
        
        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
        )
        session.add(nutritionist)
        session.commit()
        
        return nutritionist
    
    def test_calendar_status_not_connected(self, client, nutritionist):
        """Test calendar status when not connected."""
        response = client.get(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/calendar/status",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["connected"] == False
        assert data["email"] is None
    
    def test_get_oauth_url(self, client, nutritionist):
        """Test getting OAuth URL."""
        response = client.get(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/calendar/oauth-url",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # URL may be None in dev (placeholder)
        assert "url" in data or "message" in data


class TestReviewsEndpoint:
    """Tests for reviews endpoint."""
    
    @pytest.fixture
    def nutritionist(self, session):
        """Create test nutritionist."""
        from app.models import Profile, NutritionistProfile
        
        profile = Profile(
            telegram_user_id=456456456,
            full_name="Reviews Test",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()
        
        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
        )
        session.add(nutritionist)
        session.commit()
        
        return nutritionist
    
    def test_reviews_empty(self, client, nutritionist):
        """Test reviews endpoint with no reviews."""
        response = client.get(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/reviews",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["reviews"] == []
        assert data["total"] == 0
    
    def test_reviews_pagination_params(self, client, nutritionist):
        """Test that pagination params are accepted."""
        response = client.get(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/reviews",
            query_string={"limit": 10, "offset": 5},
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200


class TestStatisticsEndpoint:
    """Tests for statistics endpoint."""
    
    @pytest.fixture
    def nutritionist(self, session):
        """Create test nutritionist."""
        from app.models import Profile, NutritionistProfile
        
        profile = Profile(
            telegram_user_id=789789789,
            full_name="Stats Test",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()
        
        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
        )
        session.add(nutritionist)
        session.commit()
        
        return nutritionist
    
    def test_statistics_empty(self, client, nutritionist):
        """Test statistics with no bookings."""
        response = client.get(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/statistics",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["income_30d"] == 0
        assert data["consultations_30d"] == 0
        assert "avg_rating" in data
        assert "total_clients" in data
    
    def test_statistics_with_days_param(self, client, nutritionist):
        """Test statistics with custom days parameter."""
        response = client.get(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/statistics",
            query_string={"days": 7},
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200


class TestSupportEndpoint:
    """Tests for support message endpoint."""
    
    def test_create_support_message(self, client):
        """Test creating a support message."""
        response = client.post(
            "/api/bot/support/messages",
            json={
                "telegram_user_id": 123456789,
                "message": "Test support message",
            },
            headers=get_service_headers(),
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert "message" in data
    
    def test_support_missing_fields(self, client):
        """Test support endpoint with missing fields."""
        response = client.post(
            "/api/bot/support/messages",
            json={"telegram_user_id": 123},
            headers=get_service_headers(),
        )
        
        assert response.status_code == 400


class TestPhotoUpload:
    """Tests for photo upload endpoint."""
    
    @pytest.fixture
    def nutritionist(self, session):
        """Create test nutritionist."""
        from app.models import Profile, NutritionistProfile
        
        profile = Profile(
            telegram_user_id=555666777,
            full_name="Photo Test",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()
        
        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
        )
        session.add(nutritionist)
        session.commit()
        
        return nutritionist
    
    def test_upload_photo(self, client, nutritionist):
        """Test photo upload endpoint."""
        import io
        
        # Create fake image data
        photo_data = io.BytesIO(b"fake image data")
        
        response = client.post(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/upload-photo",
            data={"photo": (photo_data, "test.jpg")},
            headers={"X-Service-Token": TEST_SERVICE_TOKEN},
            content_type="multipart/form-data",
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert "photo_url" in data
    
    def test_upload_no_file(self, client, nutritionist):
        """Test upload endpoint without file."""
        response = client.post(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/upload-photo",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 400


class TestDashboardEndpoint:
    """Tests for nutritionist dashboard endpoint."""
    
    @pytest.fixture
    def nutritionist_with_data(self, session):
        """Create test nutritionist with services and bookings."""
        from app.models import Profile, NutritionistProfile, Service
        
        profile = Profile(
            telegram_user_id=111333555,
            full_name="Dashboard Test",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()
        
        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
            verification_status="approved",
        )
        session.add(nutritionist)
        
        # Add service
        service = Service(
            nutritionist_id=profile.id,
            title="Dashboard Service",
            duration_minutes=60,
            price_rub=3000,
        )
        session.add(service)
        session.commit()
        
        return nutritionist
    
    def test_dashboard_returns_all_data(self, client, nutritionist_with_data):
        """Test that dashboard returns all expected data."""
        response = client.get(
            f"/api/nutritionists/{nutritionist_with_data.nutritionist_id}/dashboard",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Check structure
        assert "nutritionist" in data
        assert "services" in data
        assert "stats" in data
        
        # Check stats fields
        assert "total_bookings" in data["stats"]
        assert "completed_bookings" in data["stats"]
        assert "total_earnings_rub" in data["stats"]
        
        # Check services
        assert len(data["services"]) == 1
        assert data["services"][0]["title"] == "Dashboard Service"


class TestAvailabilitySlots:
    """Tests for availability slot management endpoints."""
    
    @pytest.fixture
    def nutritionist(self, session):
        """Create test nutritionist."""
        from app.models import Profile, NutritionistProfile
        
        profile = Profile(
            telegram_user_id=999111222,
            full_name="Slots Test",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()
        
        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
            verification_status="approved",
        )
        session.add(nutritionist)
        session.commit()
        
        return nutritionist
    
    def test_list_slots_empty(self, client, nutritionist):
        """Test listing slots when none exist."""
        response = client.get(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/slots",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["slots"] == []
        assert data["total"] == 0
    
    def test_create_slot_success(self, client, nutritionist):
        """Test creating a valid slot."""
        from datetime import datetime, timedelta, timezone
        
        # Future slot
        start = datetime.now(timezone.utc) + timedelta(days=1, hours=2)
        end = start + timedelta(hours=1)
        
        response = client.post(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/slots",
            json={
                "start_at": start.isoformat(),
                "end_at": end.isoformat(),
            },
            headers=get_service_headers(),
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert "slot" in data
        assert data["slot"]["status"] == "free"
        assert data["slot"]["source"] == "manual"
    
    def test_create_slot_in_past_fails(self, client, nutritionist):
        """Test that creating a slot in the past fails."""
        from datetime import datetime, timedelta, timezone
        
        # Past slot
        start = datetime.now(timezone.utc) - timedelta(hours=2)
        end = start + timedelta(hours=1)
        
        response = client.post(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/slots",
            json={
                "start_at": start.isoformat(),
                "end_at": end.isoformat(),
            },
            headers=get_service_headers(),
        )
        
        assert response.status_code == 400
    
    def test_create_slot_end_before_start_fails(self, client, nutritionist):
        """Test that end_at must be after start_at."""
        from datetime import datetime, timedelta, timezone
        
        start = datetime.now(timezone.utc) + timedelta(days=1)
        end = start - timedelta(hours=1)  # End before start
        
        response = client.post(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/slots",
            json={
                "start_at": start.isoformat(),
                "end_at": end.isoformat(),
            },
            headers=get_service_headers(),
        )
        
        assert response.status_code == 400
    
    def test_create_overlapping_slot_fails(self, client, session, nutritionist):
        """Test that overlapping slots are rejected."""
        from datetime import datetime, timedelta, timezone
        from app.models import AvailabilitySlot
        
        # Create existing slot
        start = datetime.now(timezone.utc) + timedelta(days=2)
        end = start + timedelta(hours=1)
        
        existing_slot = AvailabilitySlot(
            nutritionist_id=nutritionist.nutritionist_id,
            start_at=start,
            end_at=end,
            status="free",
            source="manual",
        )
        session.add(existing_slot)
        session.commit()
        
        # Try to create overlapping slot
        new_start = start + timedelta(minutes=30)  # Overlaps with existing
        new_end = new_start + timedelta(hours=1)
        
        response = client.post(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/slots",
            json={
                "start_at": new_start.isoformat(),
                "end_at": new_end.isoformat(),
            },
            headers=get_service_headers(),
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert "пересекается" in data["error"].lower()
    
    def test_list_slots_with_date_range(self, client, session, nutritionist):
        """Test listing slots with date range filter."""
        from datetime import datetime, timedelta, timezone
        from app.models import AvailabilitySlot
        
        now = datetime.now(timezone.utc)
        
        # Create slots
        slot1 = AvailabilitySlot(
            nutritionist_id=nutritionist.nutritionist_id,
            start_at=now + timedelta(days=1),
            end_at=now + timedelta(days=1, hours=1),
            status="free",
            source="manual",
        )
        slot2 = AvailabilitySlot(
            nutritionist_id=nutritionist.nutritionist_id,
            start_at=now + timedelta(days=5),
            end_at=now + timedelta(days=5, hours=1),
            status="free",
            source="manual",
        )
        session.add_all([slot1, slot2])
        session.commit()
        
        # List slots within 3 days
        to_date = now + timedelta(days=3)
        response = client.get(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/slots",
            query_string={"to": to_date.isoformat()},
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Only slot1 should be in range
        assert data["total"] == 1
    
    def test_delete_free_slot_success(self, client, session, nutritionist):
        """Test deleting a free slot."""
        from datetime import datetime, timedelta, timezone
        from app.models import AvailabilitySlot
        
        # Create free slot
        start = datetime.now(timezone.utc) + timedelta(days=1)
        slot = AvailabilitySlot(
            nutritionist_id=nutritionist.nutritionist_id,
            start_at=start,
            end_at=start + timedelta(hours=1),
            status="free",
            source="manual",
        )
        session.add(slot)
        session.commit()
        slot_id = slot.id
        
        # Delete
        response = client.delete(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/slots/{slot_id}",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        
        # Verify deleted
        assert session.get(AvailabilitySlot, slot_id) is None
    
    def test_delete_booked_slot_fails(self, client, session, nutritionist):
        """Test that booked slots cannot be deleted."""
        from datetime import datetime, timedelta, timezone
        from app.models import AvailabilitySlot
        
        # Create booked slot
        start = datetime.now(timezone.utc) + timedelta(days=1)
        slot = AvailabilitySlot(
            nutritionist_id=nutritionist.nutritionist_id,
            start_at=start,
            end_at=start + timedelta(hours=1),
            status="booked",  # Not free
            source="manual",
        )
        session.add(slot)
        session.commit()
        
        # Try to delete
        response = client.delete(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/slots/{slot.id}",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert "используется" in data["error"].lower()
    
    def test_delete_held_slot_fails(self, client, session, nutritionist):
        """Test that held slots cannot be deleted."""
        from datetime import datetime, timedelta, timezone
        from app.models import AvailabilitySlot
        
        # Create held slot
        start = datetime.now(timezone.utc) + timedelta(days=1)
        slot = AvailabilitySlot(
            nutritionist_id=nutritionist.nutritionist_id,
            start_at=start,
            end_at=start + timedelta(hours=1),
            status="held",  # Not free
            source="manual",
        )
        session.add(slot)
        session.commit()
        
        # Try to delete
        response = client.delete(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/slots/{slot.id}",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 400
    
    def test_delete_other_nutritionist_slot_forbidden(self, client, session, nutritionist):
        """Test that deleting another nutritionist's slot is forbidden."""
        from datetime import datetime, timedelta, timezone
        from app.models import Profile, NutritionistProfile, AvailabilitySlot
        
        # Create another nutritionist
        other_profile = Profile(
            telegram_user_id=333444555,
            full_name="Other Nutritionist",
            role="nutritionist",
        )
        session.add(other_profile)
        session.flush()
        
        other_nutritionist = NutritionistProfile(
            nutritionist_id=other_profile.id,
        )
        session.add(other_nutritionist)
        
        # Create slot for other nutritionist
        start = datetime.now(timezone.utc) + timedelta(days=1)
        slot = AvailabilitySlot(
            nutritionist_id=other_profile.id,
            start_at=start,
            end_at=start + timedelta(hours=1),
            status="free",
            source="manual",
        )
        session.add(slot)
        session.commit()
        
        # Try to delete from wrong nutritionist
        response = client.delete(
            f"/api/bot/nutritionists/{nutritionist.nutritionist_id}/slots/{slot.id}",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 403


class TestNutritionistBookings:
    """Tests for nutritionist bookings endpoint."""
    
    @pytest.fixture
    def nutritionist_with_booking(self, session):
        """Create nutritionist with a booking."""
        from datetime import datetime, timedelta, timezone
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking
        
        # Create nutritionist
        profile = Profile(
            telegram_user_id=888999000,
            full_name="Bookings Test",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()
        
        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
            verification_status="approved",
        )
        session.add(nutritionist)
        
        # Create client
        client_profile = Profile(
            telegram_user_id=111222333,
            full_name="Test Client",
            role="client",
        )
        session.add(client_profile)
        session.flush()
        
        # Create service
        service = Service(
            nutritionist_id=profile.id,
            title="Test Consultation",
            duration_minutes=60,
            price_rub=3000,
        )
        session.add(service)
        session.flush()
        
        # Create slot
        start = datetime.now(timezone.utc) + timedelta(days=1)
        slot = AvailabilitySlot(
            nutritionist_id=profile.id,
            start_at=start,
            end_at=start + timedelta(hours=1),
            status="booked",
            source="manual",
        )
        session.add(slot)
        session.flush()
        
        # Create booking
        booking = Booking(
            client_id=client_profile.id,
            nutritionist_id=profile.id,
            service_id=service.id,
            slot_id=slot.id,
            status="paid",
            price_rub=3000,
        )
        session.add(booking)
        session.commit()
        
        return nutritionist
    
    def test_get_bookings_success(self, client, nutritionist_with_booking):
        """Test getting nutritionist bookings."""
        response = client.get(
            f"/api/bot/nutritionists/{nutritionist_with_booking.nutritionist_id}/bookings",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert "bookings" in data
        assert "total" in data
        assert data["total"] >= 1
        
        if data["bookings"]:
            booking = data["bookings"][0]
            assert "client_name" in booking
            assert "service_title" in booking
            assert "start_at" in booking
            assert "end_at" in booking
            assert "status" in booking
    
    def test_get_bookings_pagination(self, client, nutritionist_with_booking):
        """Test bookings pagination params."""
        response = client.get(
            f"/api/bot/nutritionists/{nutritionist_with_booking.nutritionist_id}/bookings",
            query_string={"limit": 5, "offset": 0},
            headers=get_service_headers(),
        )
        
        assert response.status_code == 200
    
    def test_get_bookings_not_found(self, client):
        """Test bookings for non-existent nutritionist."""
        import uuid
        fake_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/bot/nutritionists/{fake_id}/bookings",
            headers=get_service_headers(),
        )
        
        assert response.status_code == 404

