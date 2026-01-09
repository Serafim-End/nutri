"""
Tests for review endpoints.
Covers client creating reviews, nutritionist viewing reviews, and admin managing reviews.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from flask_jwt_extended import create_access_token


def utc_now():
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class TestClientCreateReview:
    """Test client creating reviews for completed bookings."""

    def test_create_review_unauthorized(self, client):
        """Test creating review without auth."""
        response = client.post(
            f"/api/bookings/{uuid4()}/review",
            json={"rating": 5, "comment": "Great service!"},
        )
        assert response.status_code == 401

    def test_create_review_booking_not_found(self, client, app, session):
        """Test creating review for non-existent booking."""
        from app.models import Profile

        with app.app_context():
            client_profile = Profile(
                telegram_user_id=200000001,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.commit()

            token = create_access_token(
                identity=str(client_profile.id),
                additional_claims={"role": "client"},
            )

            response = client.post(
                f"/api/bookings/{uuid4()}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5, "comment": "Great service!"},
            )
            assert response.status_code == 404

    def test_create_review_not_authorized(self, client, app, session):
        """Test creating review for another client's booking."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking

        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=200000002,
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
                status="booked",
            )
            session.add(slot)
            session.flush()

            # Create client 1 (booking owner)
            client1_profile = Profile(
                telegram_user_id=200000003,
                full_name="Client 1",
                role="client",
            )
            session.add(client1_profile)
            session.flush()

            # Create client 2 (trying to review)
            client2_profile = Profile(
                telegram_user_id=200000004,
                full_name="Client 2",
                role="client",
            )
            session.add(client2_profile)
            session.flush()

            # Create completed booking for client 1
            booking = Booking(
                client_id=client1_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="completed",
                price_rub=service.price_rub,
            )
            session.add(booking)
            session.commit()

            # Client 2 tries to review client 1's booking
            token = create_access_token(
                identity=str(client2_profile.id),
                additional_claims={"role": "client"},
            )

            response = client.post(
                f"/api/bookings/{booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5, "comment": "Great service!"},
            )
            assert response.status_code == 403

    def test_create_review_not_completed(self, client, app, session):
        """Test creating review for non-completed booking."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking

        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=200000005,
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
                status="booked",
            )
            session.add(slot)
            session.flush()

            # Create client
            client_profile = Profile(
                telegram_user_id=200000006,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()

            # Create paid (not completed) booking
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

            token = create_access_token(
                identity=str(client_profile.id),
                additional_claims={"role": "client"},
            )

            response = client.post(
                f"/api/bookings/{booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5, "comment": "Great service!"},
            )
            assert response.status_code == 400
            assert "completed" in response.json.get("error", "").lower()

    def test_create_review_success(self, client, app, session):
        """Test successfully creating a review."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking, Review

        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=200000007,
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
                status="booked",
            )
            session.add(slot)
            session.flush()

            # Create client
            client_profile = Profile(
                telegram_user_id=200000008,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()

            # Create completed booking
            booking = Booking(
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="completed",
                price_rub=service.price_rub,
            )
            session.add(booking)
            session.commit()

            token = create_access_token(
                identity=str(client_profile.id),
                additional_claims={"role": "client"},
            )

            response = client.post(
                f"/api/bookings/{booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5, "comment": "Great service! Highly recommend."},
            )

            assert response.status_code == 201
            data = response.json
            assert "review" in data
            assert data["review"]["rating"] == 5
            assert data["review"]["comment"] == "Great service! Highly recommend."
            assert data["review"]["booking_id"] == str(booking.id)
            assert data["review"]["nutritionist_id"] == str(nutri_profile.id)
            assert data["review"]["is_hidden"] is False

            # Verify review was created in database
            review = Review.query.filter_by(booking_id=booking.id).first()
            assert review is not None
            assert review.rating == 5
            assert review.comment == "Great service! Highly recommend."

    def test_create_review_duplicate(self, client, app, session):
        """Test creating duplicate review for same booking."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking, Review

        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=200000009,
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
                status="booked",
            )
            session.add(slot)
            session.flush()

            # Create client
            client_profile = Profile(
                telegram_user_id=200000010,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()

            # Create completed booking
            booking = Booking(
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="completed",
                price_rub=service.price_rub,
            )
            session.add(booking)
            session.flush()

            # Create existing review
            review = Review(
                booking_id=booking.id,
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                rating=4,
                comment="Good service",
            )
            session.add(review)
            session.commit()

            token = create_access_token(
                identity=str(client_profile.id),
                additional_claims={"role": "client"},
            )

            # Try to create another review
            response = client.post(
                f"/api/bookings/{booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 5, "comment": "Great service!"},
            )

            assert response.status_code == 409
            assert "already exists" in response.json.get("error", "").lower()

    def test_create_review_invalid_rating(self, client, app, session):
        """Test creating review with invalid rating."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking

        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=200000011,
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
                status="booked",
            )
            session.add(slot)
            session.flush()

            # Create client
            client_profile = Profile(
                telegram_user_id=200000012,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()

            # Create completed booking
            booking = Booking(
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="completed",
                price_rub=service.price_rub,
            )
            session.add(booking)
            session.commit()

            token = create_access_token(
                identity=str(client_profile.id),
                additional_claims={"role": "client"},
            )

            # Try rating 0 (invalid)
            response = client.post(
                f"/api/bookings/{booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 0, "comment": "Bad"},
            )
            assert response.status_code == 400

            # Try rating 6 (invalid)
            response = client.post(
                f"/api/bookings/{booking.id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={"rating": 6, "comment": "Bad"},
            )
            assert response.status_code == 400


class TestNutritionistViewReviews:
    """Test nutritionist viewing their reviews."""

    def test_list_reviews_unauthorized(self, client):
        """Test listing reviews without auth."""
        response = client.get(f"/api/nutritionists/{uuid4()}/reviews")
        assert response.status_code == 401

    def test_list_reviews_not_authorized(self, client, app, session):
        """Test listing reviews for another nutritionist."""
        from app.models import Profile, NutritionistProfile

        with app.app_context():
            # Create nutritionist 1
            nutri1_profile = Profile(
                telegram_user_id=300000001,
                full_name="Nutritionist 1",
                role="nutritionist",
            )
            session.add(nutri1_profile)
            session.flush()

            nutri1 = NutritionistProfile(
                nutritionist_id=nutri1_profile.id,
                verification_status="approved",
                is_active=True,
            )
            session.add(nutri1)

            # Create nutritionist 2
            nutri2_profile = Profile(
                telegram_user_id=300000002,
                full_name="Nutritionist 2",
                role="nutritionist",
            )
            session.add(nutri2_profile)
            session.flush()

            nutri2 = NutritionistProfile(
                nutritionist_id=nutri2_profile.id,
                verification_status="approved",
                is_active=True,
            )
            session.add(nutri2)
            session.commit()

            # Nutritionist 2 tries to view nutritionist 1's reviews
            token = create_access_token(
                identity=str(nutri2_profile.id),
                additional_claims={"role": "nutritionist"},
            )

            response = client.get(
                f"/api/nutritionists/{nutri1_profile.id}/reviews",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 403

    def test_list_reviews_success(self, client, app, session):
        """Test successfully listing reviews."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking, Review

        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=300000003,
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

            # Create clients and bookings with reviews
            reviews_data = [
                (300000004, "Client 1", 5, "Excellent"),
                (300000005, "Client 2", 4, "Very good"),
                (300000006, "Client 3", 5, None),  # No comment
            ]

            for telegram_id, name, rating, comment in reviews_data:
                client_profile = Profile(
                    telegram_user_id=telegram_id,
                    full_name=name,
                    role="client",
                )
                session.add(client_profile)
                session.flush()

                slot = AvailabilitySlot(
                    nutritionist_id=nutri_profile.id,
                    start_at=utc_now() + timedelta(days=1),
                    end_at=utc_now() + timedelta(days=1, hours=1),
                    status="booked",
                )
                session.add(slot)
                session.flush()

                booking = Booking(
                    client_id=client_profile.id,
                    nutritionist_id=nutri_profile.id,
                    service_id=service.id,
                    slot_id=slot.id,
                    status="completed",
                    price_rub=service.price_rub,
                )
                session.add(booking)
                session.flush()

                review = Review(
                    booking_id=booking.id,
                    client_id=client_profile.id,
                    nutritionist_id=nutri_profile.id,
                    rating=rating,
                    comment=comment,
                    is_hidden=False,
                )
                session.add(review)

            session.commit()

            token = create_access_token(
                identity=str(nutri_profile.id),
                additional_claims={"role": "nutritionist"},
            )

            response = client.get(
                f"/api/nutritionists/{nutri_profile.id}/reviews",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json
            assert "reviews" in data
            assert len(data["reviews"]) == 3
            assert data["total"] == 3
            assert data["page"] == 1
            assert data["rating_count"] == 3
            assert data["average_rating"] == pytest.approx(4.67, abs=0.01)

            # Verify hidden reviews are excluded
            hidden_review = Review(
                booking_id=booking.id,
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                rating=1,
                comment="Hidden review",
                is_hidden=True,
            )
            session.add(hidden_review)
            session.commit()

            response = client.get(
                f"/api/nutritionists/{nutri_profile.id}/reviews",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json
            assert len(data["reviews"]) == 3  # Hidden review not included
            assert data["total"] == 3
            assert data["rating_count"] == 3  # Hidden review not counted

    def test_list_reviews_admin_access(self, client, app, session):
        """Test admin can view any nutritionist's reviews."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking, Review

        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=300000007,
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

            # Create service, client, booking, review
            service = Service(
                nutritionist_id=nutri_profile.id,
                title="Test Service",
                duration_minutes=60,
                price_rub=3000,
                is_active=True,
            )
            session.add(service)
            session.flush()

            client_profile = Profile(
                telegram_user_id=300000008,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()

            slot = AvailabilitySlot(
                nutritionist_id=nutri_profile.id,
                start_at=utc_now() + timedelta(days=1),
                end_at=utc_now() + timedelta(days=1, hours=1),
                status="booked",
            )
            session.add(slot)
            session.flush()

            booking = Booking(
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="completed",
                price_rub=service.price_rub,
            )
            session.add(booking)
            session.flush()

            review = Review(
                booking_id=booking.id,
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                rating=5,
                comment="Great!",
                is_hidden=False,
            )
            session.add(review)
            session.commit()

            # Admin token
            admin_token = create_access_token(
                identity="admin",
                additional_claims={"role": "admin"},
            )

            response = client.get(
                f"/api/nutritionists/{nutri_profile.id}/reviews",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            data = response.json
            assert len(data["reviews"]) == 1
            assert data["reviews"][0]["rating"] == 5


class TestAdminManageReviews:
    """Test admin hiding and deleting reviews."""

    def test_hide_review_not_admin(self, client, app, session):
        """Test hiding review without admin access."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking, Review

        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=400000001,
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

            # Create service, client, booking, review
            service = Service(
                nutritionist_id=nutri_profile.id,
                title="Test Service",
                duration_minutes=60,
                price_rub=3000,
                is_active=True,
            )
            session.add(service)
            session.flush()

            client_profile = Profile(
                telegram_user_id=400000002,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()

            slot = AvailabilitySlot(
                nutritionist_id=nutri_profile.id,
                start_at=utc_now() + timedelta(days=1),
                end_at=utc_now() + timedelta(days=1, hours=1),
                status="booked",
            )
            session.add(slot)
            session.flush()

            booking = Booking(
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="completed",
                price_rub=service.price_rub,
            )
            session.add(booking)
            session.flush()

            review = Review(
                booking_id=booking.id,
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                rating=5,
                comment="Great!",
            )
            session.add(review)
            session.commit()

            # Client tries to hide review
            client_token = create_access_token(
                identity=str(client_profile.id),
                additional_claims={"role": "client"},
            )

            response = client.post(
                f"/api/admin/reviews/{review.id}/hide",
                headers={"Authorization": f"Bearer {client_token}"},
            )
            assert response.status_code == 403

    def test_hide_review_success(self, client, app, session):
        """Test admin successfully hiding a review."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking, Review

        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=400000003,
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

            # Create service, client, booking, review
            service = Service(
                nutritionist_id=nutri_profile.id,
                title="Test Service",
                duration_minutes=60,
                price_rub=3000,
                is_active=True,
            )
            session.add(service)
            session.flush()

            client_profile = Profile(
                telegram_user_id=400000004,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()

            slot = AvailabilitySlot(
                nutritionist_id=nutri_profile.id,
                start_at=utc_now() + timedelta(days=1),
                end_at=utc_now() + timedelta(days=1, hours=1),
                status="booked",
            )
            session.add(slot)
            session.flush()

            booking = Booking(
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="completed",
                price_rub=service.price_rub,
            )
            session.add(booking)
            session.flush()

            review = Review(
                booking_id=booking.id,
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                rating=1,
                comment="Bad review",
                is_hidden=False,
            )
            session.add(review)
            session.commit()

            # Admin hides review
            admin_token = create_access_token(
                identity="admin",
                additional_claims={"role": "admin"},
            )

            response = client.post(
                f"/api/admin/reviews/{review.id}/hide",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            data = response.json
            assert data["review"]["is_hidden"] is True

            # Verify hidden review is excluded from nutritionist's review list
            nutri_token = create_access_token(
                identity=str(nutri_profile.id),
                additional_claims={"role": "nutritionist"},
            )

            response = client.get(
                f"/api/nutritionists/{nutri_profile.id}/reviews",
                headers={"Authorization": f"Bearer {nutri_token}"},
            )

            assert response.status_code == 200
            data = response.json
            assert len(data["reviews"]) == 0  # Hidden review excluded
            assert data["total"] == 0

    def test_unhide_review_success(self, client, app, session):
        """Test admin successfully unhiding a review."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking, Review

        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=400000005,
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

            # Create service, client, booking, hidden review
            service = Service(
                nutritionist_id=nutri_profile.id,
                title="Test Service",
                duration_minutes=60,
                price_rub=3000,
                is_active=True,
            )
            session.add(service)
            session.flush()

            client_profile = Profile(
                telegram_user_id=400000006,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()

            slot = AvailabilitySlot(
                nutritionist_id=nutri_profile.id,
                start_at=utc_now() + timedelta(days=1),
                end_at=utc_now() + timedelta(days=1, hours=1),
                status="booked",
            )
            session.add(slot)
            session.flush()

            booking = Booking(
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="completed",
                price_rub=service.price_rub,
            )
            session.add(booking)
            session.flush()

            review = Review(
                booking_id=booking.id,
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                rating=5,
                comment="Good review",
                is_hidden=True,
            )
            session.add(review)
            session.commit()

            # Admin unhides review
            admin_token = create_access_token(
                identity="admin",
                additional_claims={"role": "admin"},
            )

            response = client.post(
                f"/api/admin/reviews/{review.id}/unhide",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            data = response.json
            assert data["review"]["is_hidden"] is False

            # Verify review is now visible to nutritionist
            nutri_token = create_access_token(
                identity=str(nutri_profile.id),
                additional_claims={"role": "nutritionist"},
            )

            response = client.get(
                f"/api/nutritionists/{nutri_profile.id}/reviews",
                headers={"Authorization": f"Bearer {nutri_token}"},
            )

            assert response.status_code == 200
            data = response.json
            assert len(data["reviews"]) == 1
            assert data["reviews"][0]["id"] == str(review.id)

    def test_delete_review_success(self, client, app, session):
        """Test admin successfully deleting a review."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking, Review

        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=400000007,
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

            # Create service, client, booking, review
            service = Service(
                nutritionist_id=nutri_profile.id,
                title="Test Service",
                duration_minutes=60,
                price_rub=3000,
                is_active=True,
            )
            session.add(service)
            session.flush()

            client_profile = Profile(
                telegram_user_id=400000008,
                full_name="Test Client",
                role="client",
            )
            session.add(client_profile)
            session.flush()

            slot = AvailabilitySlot(
                nutritionist_id=nutri_profile.id,
                start_at=utc_now() + timedelta(days=1),
                end_at=utc_now() + timedelta(days=1, hours=1),
                status="booked",
            )
            session.add(slot)
            session.flush()

            booking = Booking(
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                service_id=service.id,
                slot_id=slot.id,
                status="completed",
                price_rub=service.price_rub,
            )
            session.add(booking)
            session.flush()

            review = Review(
                booking_id=booking.id,
                client_id=client_profile.id,
                nutritionist_id=nutri_profile.id,
                rating=1,
                comment="Spam review",
            )
            session.add(review)
            session.commit()

            review_id = review.id

            # Admin deletes review
            admin_token = create_access_token(
                identity="admin",
                additional_claims={"role": "admin"},
            )

            response = client.delete(
                f"/api/admin/reviews/{review_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            assert "deleted" in response.json.get("message", "").lower()

            # Verify review is deleted
            deleted_review = Review.query.get(review_id)
            assert deleted_review is None

    def test_list_reviews_admin(self, client, app, session):
        """Test admin listing all reviews with filters."""
        from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking, Review

        with app.app_context():
            # Create nutritionist
            nutri_profile = Profile(
                telegram_user_id=400000009,
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

            # Create multiple reviews (some hidden, some visible)
            for i in range(3):
                client_profile = Profile(
                    telegram_user_id=400000010 + i,
                    full_name=f"Client {i}",
                    role="client",
                )
                session.add(client_profile)
                session.flush()

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
                    status="completed",
                    price_rub=service.price_rub,
                )
                session.add(booking)
                session.flush()

                review = Review(
                    booking_id=booking.id,
                    client_id=client_profile.id,
                    nutritionist_id=nutri_profile.id,
                    rating=5 - i,
                    comment=f"Review {i}",
                    is_hidden=(i == 1),  # Middle one is hidden
                )
                session.add(review)

            session.commit()

            # Admin lists all reviews
            admin_token = create_access_token(
                identity="admin",
                additional_claims={"role": "admin"},
            )

            response = client.get(
                "/api/admin/reviews",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            data = response.json
            assert len(data["reviews"]) == 3
            assert data["total"] == 3

            # Filter by hidden
            response = client.get(
                "/api/admin/reviews?is_hidden=true",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            data = response.json
            assert len(data["reviews"]) == 1
            assert data["reviews"][0]["is_hidden"] is True

            # Filter by visible
            response = client.get(
                "/api/admin/reviews?is_hidden=false",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            data = response.json
            assert len(data["reviews"]) == 2
            assert all(r["is_hidden"] is False for r in data["reviews"])
