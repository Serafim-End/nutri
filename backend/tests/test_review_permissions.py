"""
Comprehensive tests for review permissions.
Tests that only clients can review their own completed bookings,
and verifies all permission edge cases.
"""

import pytest
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import create_access_token

from app.models import (
    Profile,
    NutritionistProfile,
    Service,
    AvailabilitySlot,
    Booking,
    Review,
)


def utc_now():
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class TestReviewPermissions:
    """Test review creation permissions."""

    @pytest.fixture
    def nutritionist(self, session):
        """Create a test nutritionist."""
        profile = Profile(
            telegram_user_id=700000001,
            full_name="Test Nutritionist",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()

        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
            verification_status="approved",
            is_active=True,
        )
        session.add(nutritionist)
        session.commit()
        return nutritionist

    @pytest.fixture
    def test_client_profile(self, session):
        """Create a test client profile."""
        profile = Profile(
            telegram_user_id=700000002,
            full_name="Test Client",
            role="client",
        )
        session.add(profile)
        session.commit()
        return profile

    @pytest.fixture
    def other_client_profile(self, session):
        """Create another test client profile."""
        profile = Profile(
            telegram_user_id=700000003,
            full_name="Other Client",
            role="client",
        )
        session.add(profile)
        session.commit()
        return profile

    @pytest.fixture
    def service(self, session, nutritionist):
        """Create a test service."""
        service = Service(
            nutritionist_id=nutritionist.nutritionist_id,
            title="Test Service",
            duration_minutes=60,
            price_rub=3000,
            is_active=True,
        )
        session.add(service)
        session.commit()
        return service

    @pytest.fixture
    def completed_booking(self, session, nutritionist, test_client_profile, service):
        """Create a completed booking."""
        slot = AvailabilitySlot(
            nutritionist_id=nutritionist.nutritionist_id,
            start_at=utc_now() + timedelta(days=1),
            end_at=utc_now() + timedelta(days=1, hours=1),
            status="booked",
        )
        session.add(slot)
        session.flush()

        booking = Booking(
            client_id=test_client_profile.id,
            nutritionist_id=nutritionist.nutritionist_id,
            service_id=service.id,
            slot_id=slot.id,
            status="completed",
            price_rub=service.price_rub,
            paid_at=utc_now() - timedelta(days=2),
        )
        session.add(booking)
        session.commit()
        return booking

    def test_client_can_review_own_completed_booking(
        self, client, app, session, nutritionist, test_client_profile, completed_booking
    ):
        """Test that client can review their own completed booking."""
        with app.app_context():
            token = create_access_token(
                identity=str(test_client_profile.id),
                additional_claims={"role": "client"},
            )

            response = client.post(
                f"/api/bookings/{completed_booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5, "comment": "Great service!"},
            )

            assert response.status_code == 201
            data = response.json
            assert "review" in data
            assert data["review"]["rating"] == 5
            assert data["review"]["booking_id"] == str(completed_booking.id)
            assert data["review"]["client_id"] == str(test_client_profile.id)

    def test_client_cannot_review_other_client_booking(
        self, client, app, session, nutritionist, other_client_profile, completed_booking
    ):
        """Test that client cannot review another client's booking."""
        with app.app_context():
            token = create_access_token(
                identity=str(other_client_profile.id),
                additional_claims={"role": "client"},
            )

            response = client.post(
                f"/api/bookings/{completed_booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5, "comment": "Great service!"},
            )

            assert response.status_code == 403
            assert "authorized" in response.json.get("error", "").lower()

    def test_nutritionist_cannot_review_own_booking(
        self, client, app, session, nutritionist, completed_booking
    ):
        """Test that nutritionist cannot review bookings (even their own)."""
        with app.app_context():
            token = create_access_token(
                identity=str(nutritionist.nutritionist_id),
                additional_claims={"role": "nutritionist"},
            )

            response = client.post(
                f"/api/bookings/{completed_booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5, "comment": "Great service!"},
            )

            assert response.status_code == 403
            assert "authorized" in response.json.get("error", "").lower()

    def test_client_cannot_review_pending_payment_booking(
        self, client, app, session, nutritionist, test_client_profile, service
    ):
        """Test that client cannot review pending_payment booking."""
        slot = AvailabilitySlot(
            nutritionist_id=nutritionist.nutritionist_id,
            start_at=utc_now() + timedelta(days=1),
            end_at=utc_now() + timedelta(days=1, hours=1),
            status="held",
        )
        session.add(slot)
        session.flush()

        booking = Booking(
            client_id=test_client_profile.id,
            nutritionist_id=nutritionist.nutritionist_id,
            service_id=service.id,
            slot_id=slot.id,
            status="pending_payment",
            price_rub=service.price_rub,
        )
        session.add(booking)
        session.commit()

        with app.app_context():
            token = create_access_token(
                identity=str(test_client_profile.id),
                additional_claims={"role": "client"},
            )

            response = client.post(
                f"/api/bookings/{booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5, "comment": "Great service!"},
            )

            assert response.status_code == 400
            assert "completed" in response.json.get("error", "").lower()

    def test_client_cannot_review_paid_booking(
        self, client, app, session, nutritionist, test_client_profile, service
    ):
        """Test that client cannot review paid (but not completed) booking."""
        slot = AvailabilitySlot(
            nutritionist_id=nutritionist.nutritionist_id,
            start_at=utc_now() + timedelta(days=1),
            end_at=utc_now() + timedelta(days=1, hours=1),
            status="booked",
        )
        session.add(slot)
        session.flush()

        booking = Booking(
            client_id=test_client_profile.id,
            nutritionist_id=nutritionist.nutritionist_id,
            service_id=service.id,
            slot_id=slot.id,
            status="paid",
            price_rub=service.price_rub,
            paid_at=utc_now(),
        )
        session.add(booking)
        session.commit()

        with app.app_context():
            token = create_access_token(
                identity=str(test_client_profile.id),
                additional_claims={"role": "client"},
            )

            response = client.post(
                f"/api/bookings/{booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5, "comment": "Great service!"},
            )

            assert response.status_code == 400
            assert "completed" in response.json.get("error", "").lower()

    def test_client_cannot_review_cancelled_booking(
        self, client, app, session, nutritionist, test_client_profile, service
    ):
        """Test that client cannot review cancelled booking."""
        slot = AvailabilitySlot(
            nutritionist_id=nutritionist.nutritionist_id,
            start_at=utc_now() + timedelta(days=1),
            end_at=utc_now() + timedelta(days=1, hours=1),
            status="free",
        )
        session.add(slot)
        session.flush()

        booking = Booking(
            client_id=test_client_profile.id,
            nutritionist_id=nutritionist.nutritionist_id,
            service_id=service.id,
            slot_id=slot.id,
            status="cancelled",
            price_rub=service.price_rub,
            cancelled_at=utc_now(),
        )
        session.add(booking)
        session.commit()

        with app.app_context():
            token = create_access_token(
                identity=str(test_client_profile.id),
                additional_claims={"role": "client"},
            )

            response = client.post(
                f"/api/bookings/{booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5, "comment": "Great service!"},
            )

            assert response.status_code == 400
            assert "completed" in response.json.get("error", "").lower()

    def test_client_cannot_review_twice(
        self, client, app, session, nutritionist, test_client_profile, completed_booking
    ):
        """Test that client cannot review the same booking twice."""
        # Create existing review
        review = Review(
            booking_id=completed_booking.id,
            client_id=test_client_profile.id,
            nutritionist_id=nutritionist.nutritionist_id,
            rating=4,
            comment="First review",
        )
        session.add(review)
        session.commit()

        with app.app_context():
            token = create_access_token(
                identity=str(test_client_profile.id),
                additional_claims={"role": "client"},
            )

            response = client.post(
                f"/api/bookings/{completed_booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5, "comment": "Second review attempt"},
            )

            assert response.status_code == 409
            assert "already exists" in response.json.get("error", "").lower()

    def test_unauthorized_user_cannot_review(
        self, client, completed_booking
    ):
        """Test that unauthorized user cannot review."""
        response = client.post(
            f"/api/bookings/{completed_booking.id}/review",
            json={"rating": 5, "comment": "Great service!"},
        )

        assert response.status_code == 401

    def test_client_can_review_multiple_different_bookings(
        self, client, app, session, nutritionist, test_client_profile, service
    ):
        """Test that client can review multiple different completed bookings."""
        # Create two completed bookings
        bookings = []
        for i in range(2):
            slot = AvailabilitySlot(
                nutritionist_id=nutritionist.nutritionist_id,
                start_at=utc_now() + timedelta(days=i+1),
                end_at=utc_now() + timedelta(days=i+1, hours=1),
                status="booked",
            )
            session.add(slot)
            session.flush()

            booking = Booking(
                client_id=test_client_profile.id,
                nutritionist_id=nutritionist.nutritionist_id,
                service_id=service.id,
                slot_id=slot.id,
                status="completed",
                price_rub=service.price_rub,
                paid_at=utc_now() - timedelta(days=2),
            )
            session.add(booking)
            bookings.append(booking)

        session.commit()

        with app.app_context():
            token = create_access_token(
                identity=str(test_client_profile.id),
                additional_claims={"role": "client"},
            )

            # Review first booking
            response1 = client.post(
                f"/api/bookings/{bookings[0].id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5, "comment": "First review"},
            )
            assert response1.status_code == 201

            # Review second booking
            response2 = client.post(
                f"/api/bookings/{bookings[1].id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 4, "comment": "Second review"},
            )
            assert response2.status_code == 201

            # Verify both reviews exist
            from app.models import Review
            reviews = Review.query.filter_by(client_id=test_client_profile.id).all()
            assert len(reviews) == 2

    def test_review_rating_validation(
        self, client, app, session, nutritionist, test_client_profile, completed_booking
    ):
        """Test that review rating must be between 1 and 5."""
        with app.app_context():
            token = create_access_token(
                identity=str(test_client_profile.id),
                additional_claims={"role": "client"},
            )

            # Test rating 0 (invalid)
            response = client.post(
                f"/api/bookings/{completed_booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 0, "comment": "Invalid rating"},
            )
            assert response.status_code == 400

            # Test rating 6 (invalid)
            response = client.post(
                f"/api/bookings/{completed_booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 6, "comment": "Invalid rating"},
            )
            assert response.status_code == 400

            # Test rating 1 (valid)
            response = client.post(
                f"/api/bookings/{completed_booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 1, "comment": "Valid rating"},
            )
            assert response.status_code == 201

    def test_review_comment_optional(
        self, client, app, session, nutritionist, test_client_profile, completed_booking
    ):
        """Test that review comment is optional."""
        with app.app_context():
            token = create_access_token(
                identity=str(test_client_profile.id),
                additional_claims={"role": "client"},
            )

            response = client.post(
                f"/api/bookings/{completed_booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5},  # No comment
            )

            assert response.status_code == 201
            data = response.json
            assert data["review"]["rating"] == 5
            assert data["review"]["comment"] is None
