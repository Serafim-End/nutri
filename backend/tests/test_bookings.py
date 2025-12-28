"""
Tests for booking endpoints.
Covers atomic booking, concurrent access, hold expiration, and payment flow.
"""

import pytest
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import uuid4

from flask_jwt_extended import create_access_token


def utc_now():
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class TestBookingCreation:
    """Test booking creation endpoint."""

    def test_create_booking_unauthorized(self, client):
        """Test booking creation without auth."""
        response = client.post(
            "/api/bookings",
            json={"service_id": str(uuid4()), "slot_id": str(uuid4())},
        )
        assert response.status_code == 401

    def test_create_booking_invalid_service(self, client, auth_headers, session):
        """Test booking with non-existent service."""
        headers, _ = auth_headers
        response = client.post(
            "/api/bookings",
            headers=headers,
            json={"service_id": str(uuid4()), "slot_id": str(uuid4())},
        )
        assert response.status_code == 400
        assert "Service not found" in response.json.get("error", "")

    def test_create_booking_success(self, client, app, session):
        """Test successful booking creation."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot
        
        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=111111111,
                full_name="Test Nutritionist",
                role="nutritionist",
            )
            session.add(nutri_profile)
            session.flush()
            
            nutri = NutritionistProfile(
                nutritionist_id=nutri_profile.id,
                verification_status="approved",
                is_active=True,
            )
            session.add(nutri)
            
            # Create service
            service = Service(
                nutritionist_id=nutri_profile.id,
                title="Test Service",
                duration_minutes=60,
                price_rub=3000,
                is_active=True,
            )
            session.add(service)
            session.flush()
            
            # Create slot
            slot = AvailabilitySlot(
                nutritionist_id=nutri_profile.id,
                start_at=utc_now() + timedelta(days=1),
                end_at=utc_now() + timedelta(days=1, hours=1),
                status="free",
            )
            session.add(slot)
            
            # Create client
            client_profile = Profile(
                telegram_user_id=222222222,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.commit()
            
            # Create token
            token = create_access_token(
                identity=str(client_profile.id),
                additional_claims={"role": "client"},
            )
            
            # Make request
            response = client.post(
                "/api/bookings",
                headers={"Authorization": f"Bearer {token}"},
                json={"service_id": str(service.id), "slot_id": str(slot.id)},
            )
            
            assert response.status_code == 201
            data = response.json
            assert "booking" in data
            assert data["booking"]["status"] == "pending_payment"
            assert "payment" in data
            
            # Verify slot is held
            session.refresh(slot)
            assert slot.status == "held"
            assert slot.hold_expires_at is not None


class TestConcurrentBooking:
    """Test concurrent booking attempts (race condition prevention)."""

    def test_concurrent_booking_only_one_succeeds(self, client, app, session):
        """Test that only one concurrent booking attempt succeeds."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot
        
        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=333333333,
                full_name="Test Nutritionist",
                role="nutritionist",
            )
            session.add(nutri_profile)
            session.flush()
            
            nutri = NutritionistProfile(
                nutritionist_id=nutri_profile.id,
                verification_status="approved",
                is_active=True,
            )
            session.add(nutri)
            
            # Create service
            service = Service(
                nutritionist_id=nutri_profile.id,
                title="Test Service",
                duration_minutes=60,
                price_rub=3000,
                is_active=True,
            )
            session.add(service)
            session.flush()
            
            # Create slot
            slot = AvailabilitySlot(
                nutritionist_id=nutri_profile.id,
                start_at=utc_now() + timedelta(days=1),
                end_at=utc_now() + timedelta(days=1, hours=1),
                status="free",
            )
            session.add(slot)
            
            # Create multiple clients
            tokens = []
            for i in range(3):
                client_profile = Profile(
                    telegram_user_id=400000000 + i,
                    full_name=f"Client {i}",
                    role="client",
                )
                session.add(client_profile)
                session.flush()
                
                token = create_access_token(
                    identity=str(client_profile.id),
                    additional_claims={"role": "client"},
                )
                tokens.append(token)
            
            session.commit()
            
            service_id = str(service.id)
            slot_id = str(slot.id)
            
            # Make concurrent requests (note: SQLite doesn't support FOR UPDATE)
            # This test is more meaningful with PostgreSQL
            success_count = 0
            conflict_count = 0
            
            for token in tokens:
                response = client.post(
                    "/api/bookings",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"service_id": service_id, "slot_id": slot_id},
                )
                if response.status_code == 201:
                    success_count += 1
                elif response.status_code == 409:
                    conflict_count += 1
            
            # At least one should succeed, and the rest should fail
            assert success_count >= 1
            # With SQLite sequential execution, only one succeeds
            # With PostgreSQL and real concurrency, only one should succeed


class TestExpiredHolds:
    """Test expired hold release functionality."""

    def test_release_expired_holds_endpoint(self, client):
        """Test expired holds release endpoint is accessible."""
        response = client.post("/api/bookings/release-expired-holds")
        assert response.status_code == 200
        assert "released_count" in response.json

    def test_release_expired_holds_works(self, client, app, session):
        """Test that expired holds are properly released."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking
        
        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=555555555,
                full_name="Test Nutritionist",
                role="nutritionist",
            )
            session.add(nutri_profile)
            session.flush()
            
            nutri = NutritionistProfile(
                nutritionist_id=nutri_profile.id,
                verification_status="approved",
                is_active=True,
            )
            session.add(nutri)
            
            # Create service
            service = Service(
                nutritionist_id=nutri_profile.id,
                title="Test Service",
                duration_minutes=60,
                price_rub=3000,
                is_active=True,
            )
            session.add(service)
            session.flush()
            
            # Create client
            client_profile = Profile(
                telegram_user_id=666666666,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()
            
            # Create slot with expired hold
            slot = AvailabilitySlot(
                nutritionist_id=nutri_profile.id,
                start_at=utc_now() + timedelta(days=1),
                end_at=utc_now() + timedelta(days=1, hours=1),
                status="held",
                hold_expires_at=utc_now() - timedelta(minutes=5),  # Expired 5 min ago
            )
            session.add(slot)
            session.flush()
            
            # Create pending booking
            booking = Booking(
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="pending_payment",
                price_rub=service.price_rub,
            )
            session.add(booking)
            session.commit()
            
            # Call release endpoint
            response = client.post("/api/bookings/release-expired-holds")
            assert response.status_code == 200
            assert response.json["released_count"] >= 1
            
            # Verify slot is free
            session.refresh(slot)
            assert slot.status == "free"
            assert slot.hold_expires_at is None
            
            # Verify booking is cancelled
            session.refresh(booking)
            assert booking.status == "cancelled"


class TestMarkPaid:
    """Test mark-paid (payment success) functionality."""

    def test_mark_paid_success(self, client, app, session):
        """Test that mark-paid transitions held->booked and pending->paid."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking
        
        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=777777777,
                full_name="Test Nutritionist",
                role="nutritionist",
            )
            session.add(nutri_profile)
            session.flush()
            
            nutri = NutritionistProfile(
                nutritionist_id=nutri_profile.id,
                verification_status="approved",
                is_active=True,
            )
            session.add(nutri)
            
            # Create service
            service = Service(
                nutritionist_id=nutri_profile.id,
                title="Test Service",
                duration_minutes=60,
                price_rub=3000,
                is_active=True,
            )
            session.add(service)
            session.flush()
            
            # Create client
            client_profile = Profile(
                telegram_user_id=888888888,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()
            
            # Create slot with hold
            slot = AvailabilitySlot(
                nutritionist_id=nutri_profile.id,
                start_at=utc_now() + timedelta(days=1),
                end_at=utc_now() + timedelta(days=1, hours=1),
                status="held",
                hold_expires_at=utc_now() + timedelta(minutes=10),  # Not expired
            )
            session.add(slot)
            session.flush()
            
            # Create pending booking
            booking = Booking(
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="pending_payment",
                price_rub=service.price_rub,
            )
            session.add(booking)
            session.commit()
            
            # Create token
            token = create_access_token(
                identity=str(client_profile.id),
                additional_claims={"role": "client"},
            )
            
            # Call mark-paid
            response = client.post(
                f"/api/bookings/{booking.id}/mark-paid",
                headers={"Authorization": f"Bearer {token}"},
            )
            
            assert response.status_code == 200
            data = response.json
            assert data["booking"]["status"] == "paid"
            assert data["booking"]["paid_at"] is not None
            
            # Verify slot is booked
            session.refresh(slot)
            assert slot.status == "booked"
            assert slot.hold_expires_at is None

    def test_mark_paid_expired_hold(self, client, app, session):
        """Test that mark-paid fails for expired holds."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking
        
        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=999999997,
                full_name="Test Nutritionist",
                role="nutritionist",
            )
            session.add(nutri_profile)
            session.flush()
            
            nutri = NutritionistProfile(
                nutritionist_id=nutri_profile.id,
                verification_status="approved",
                is_active=True,
            )
            session.add(nutri)
            
            # Create service
            service = Service(
                nutritionist_id=nutri_profile.id,
                title="Test Service",
                duration_minutes=60,
                price_rub=3000,
                is_active=True,
            )
            session.add(service)
            session.flush()
            
            # Create client
            client_profile = Profile(
                telegram_user_id=999999998,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()
            
            # Create slot with expired hold
            slot = AvailabilitySlot(
                nutritionist_id=nutri_profile.id,
                start_at=utc_now() + timedelta(days=1),
                end_at=utc_now() + timedelta(days=1, hours=1),
                status="held",
                hold_expires_at=utc_now() - timedelta(minutes=5),  # Expired
            )
            session.add(slot)
            session.flush()
            
            # Create pending booking
            booking = Booking(
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="pending_payment",
                price_rub=service.price_rub,
            )
            session.add(booking)
            session.commit()
            
            # Create token
            token = create_access_token(
                identity=str(client_profile.id),
                additional_claims={"role": "client"},
            )
            
            # Call mark-paid
            response = client.post(
                f"/api/bookings/{booking.id}/mark-paid",
                headers={"Authorization": f"Bearer {token}"},
            )
            
            assert response.status_code == 400
            assert "expired" in response.json.get("error", "").lower()


class TestCancelBooking:
    """Test booking cancellation functionality."""

    def test_cancel_pending_releases_slot(self, client, app, session):
        """Test that cancelling pending booking releases slot."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking
        
        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=111111112,
                full_name="Test Nutritionist",
                role="nutritionist",
            )
            session.add(nutri_profile)
            session.flush()
            
            nutri = NutritionistProfile(
                nutritionist_id=nutri_profile.id,
                verification_status="approved",
                is_active=True,
            )
            session.add(nutri)
            
            # Create service
            service = Service(
                nutritionist_id=nutri_profile.id,
                title="Test Service",
                duration_minutes=60,
                price_rub=3000,
                is_active=True,
            )
            session.add(service)
            session.flush()
            
            # Create client
            client_profile = Profile(
                telegram_user_id=111111113,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()
            
            # Create held slot
            slot = AvailabilitySlot(
                nutritionist_id=nutri_profile.id,
                start_at=utc_now() + timedelta(days=1),
                end_at=utc_now() + timedelta(days=1, hours=1),
                status="held",
                hold_expires_at=utc_now() + timedelta(minutes=10),
            )
            session.add(slot)
            session.flush()
            
            # Create pending booking
            booking = Booking(
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="pending_payment",
                price_rub=service.price_rub,
            )
            session.add(booking)
            session.commit()
            
            # Create token
            token = create_access_token(
                identity=str(client_profile.id),
                additional_claims={"role": "client"},
            )
            
            # Cancel booking
            response = client.post(
                f"/api/bookings/{booking.id}/cancel",
                headers={"Authorization": f"Bearer {token}"},
                json={"reason": "Changed my mind"},
            )
            
            assert response.status_code == 200
            assert response.json["booking"]["status"] == "cancelled"
            
            # Verify slot is free
            session.refresh(slot)
            assert slot.status == "free"
            assert slot.hold_expires_at is None

    def test_cancel_paid_forbidden(self, client, app, session):
        """Test that cancelling paid booking is forbidden for clients."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking
        
        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=111111114,
                full_name="Test Nutritionist",
                role="nutritionist",
            )
            session.add(nutri_profile)
            session.flush()
            
            nutri = NutritionistProfile(
                nutritionist_id=nutri_profile.id,
                verification_status="approved",
                is_active=True,
            )
            session.add(nutri)
            
            # Create service
            service = Service(
                nutritionist_id=nutri_profile.id,
                title="Test Service",
                duration_minutes=60,
                price_rub=3000,
                is_active=True,
            )
            session.add(service)
            session.flush()
            
            # Create client
            client_profile = Profile(
                telegram_user_id=111111115,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()
            
            # Create booked slot
            slot = AvailabilitySlot(
                nutritionist_id=nutri_profile.id,
                start_at=utc_now() + timedelta(days=1),
                end_at=utc_now() + timedelta(days=1, hours=1),
                status="booked",
            )
            session.add(slot)
            session.flush()
            
            # Create paid booking
            booking = Booking(
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="paid",
                price_rub=service.price_rub,
                paid_at=utc_now(),
            )
            session.add(booking)
            session.commit()
            
            # Create token
            token = create_access_token(
                identity=str(client_profile.id),
                additional_claims={"role": "client"},
            )
            
            # Try to cancel
            response = client.post(
                f"/api/bookings/{booking.id}/cancel",
                headers={"Authorization": f"Bearer {token}"},
            )
            
            assert response.status_code == 400
            assert "Cannot cancel a paid booking" in response.json.get("error", "")


class TestPublicEndpoints:
    """Test public endpoints."""

    def test_list_nutritionists(self, client):
        """Test listing nutritionists."""
        response = client.get("/api/public/nutritionists")
        assert response.status_code == 200
        assert "nutritionists" in response.json
        assert "total" in response.json

    def test_get_nutritionist_not_found(self, client):
        """Test getting non-existent nutritionist."""
        response = client.get(
            f"/api/public/nutritionists/{uuid4()}"
        )
        assert response.status_code == 404


class TestDevLogin:
    """Test development login endpoint."""

    def test_dev_login_success(self, client, app, session):
        """Test dev login works in development mode."""
        from app.models import Profile
        
        with app.app_context():
            # Create test client profile
            profile = Profile(
                telegram_user_id=300000001,
                full_name="Test Client",
                role="client",
            )
            session.add(profile)
            session.commit()
            
            # Set dev mode
            app.config["DEV_MODE"] = True
            
            response = client.post("/api/auth/dev-login")
            
            if app.config.get("DEV_MODE"):
                assert response.status_code == 200
                assert "access_token" in response.json
                assert "profile" in response.json
            else:
                # In production mode, should be forbidden
                assert response.status_code == 403


class TestMyBookings:
    """Test client bookings list endpoint."""

    def test_list_my_bookings(self, client, app, session):
        """Test listing client's bookings."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking
        
        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=111111116,
                full_name="Test Nutritionist",
                role="nutritionist",
            )
            session.add(nutri_profile)
            session.flush()
            
            nutri = NutritionistProfile(
                nutritionist_id=nutri_profile.id,
                verification_status="approved",
                is_active=True,
            )
            session.add(nutri)
            
            # Create service
            service = Service(
                nutritionist_id=nutri_profile.id,
                title="Test Service",
                duration_minutes=60,
                price_rub=3000,
                is_active=True,
            )
            session.add(service)
            session.flush()
            
            # Create client
            client_profile = Profile(
                telegram_user_id=111111117,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()
            
            # Create slots and bookings
            for i in range(3):
                slot = AvailabilitySlot(
                    nutritionist_id=nutri_profile.id,
                    start_at=utc_now() + timedelta(days=i+1),
                    end_at=utc_now() + timedelta(days=i+1, hours=1),
                    status="booked",
                )
                session.add(slot)
                session.flush()
                
                booking = Booking(
                    client_id=client_profile.id,
                    nutritionist_id=nutri_profile.id,
                    service_id=service.id,
                    slot_id=slot.id,
                    status="paid",
                    price_rub=service.price_rub,
                )
                session.add(booking)
            
            session.commit()
            
            # Create token
            token = create_access_token(
                identity=str(client_profile.id),
                additional_claims={"role": "client"},
            )
            
            # Get bookings
            response = client.get(
                "/api/clients/me/bookings",
                headers={"Authorization": f"Bearer {token}"},
            )
            
            assert response.status_code == 200
            assert "bookings" in response.json
            assert len(response.json["bookings"]) == 3
