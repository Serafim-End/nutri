"""
Integration tests for availability calculation endpoints.
Tests real user flows: client browsing available slots with working hours,
date exceptions, and Google Calendar busy exclusion.
"""

import pytest
from unittest.mock import patch
from datetime import datetime, date, timedelta, timezone
from flask_jwt_extended import create_access_token

from app.models import (
    Profile,
    NutritionistProfile,
    WorkingHoursTemplate,
    DateException,
    GoogleCalendar,
    Service,
)


def utc_now():
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class TestAvailabilityCalculationEndpoint:
    """Test the /api/public/nutritionists/<id>/slots endpoint."""

    @pytest.fixture
    def nutritionist(self, session):
        """Create a test nutritionist."""
        profile = Profile(
            telegram_user_id=500000001,
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
    def working_hours(self, session, nutritionist):
        """Create working hours template."""
        template = WorkingHoursTemplate(
            nutritionist_id=nutritionist.nutritionist_id,
            weekly_schedule={
                "0": [{"start": "09:00", "end": "12:00"}],  # Monday
                "1": [{"start": "14:00", "end": "18:00"}],  # Tuesday
                "2": [{"start": "10:00", "end": "16:00"}],  # Wednesday
            },
        )
        session.add(template)
        session.commit()
        return template

    def test_list_slots_basic_working_hours(self, client, nutritionist, working_hours):
        """Test listing slots with basic working hours only."""
        response = client.get(
            f"/api/public/nutritionists/{nutritionist.nutritionist_id}/slots"
        )

        assert response.status_code == 200
        data = response.json
        assert "slots" in data
        assert len(data["slots"]) > 0

        # Verify slots are in the future
        for slot in data["slots"]:
            start_at = datetime.fromisoformat(slot["start_at"].replace("Z", "+00:00"))
            assert start_at > utc_now()
            assert slot["status"] == "free"
            assert slot["source"] == "calculated"

    def test_list_slots_with_date_exception_off(self, client, session, nutritionist, working_hours):
        """Test that date exceptions marked as 'off' exclude slots."""
        # Create date exception for tomorrow (Monday)
        tomorrow = date.today() + timedelta(days=1)
        # Find next Monday
        days_until_monday = (0 - tomorrow.weekday()) % 7
        if days_until_monday == 0 and tomorrow.weekday() != 0:
            days_until_monday = 7
        monday_date = tomorrow + timedelta(days=days_until_monday)

        exception = DateException(
            nutritionist_id=nutritionist.nutritionist_id,
            exception_date=monday_date,
            exception_type="off",
        )
        session.add(exception)
        session.commit()

        response = client.get(
            f"/api/public/nutritionists/{nutritionist.nutritionist_id}/slots"
        )

        assert response.status_code == 200
        data = response.json

        # Verify no slots on the exception date
        for slot in data["slots"]:
            start_at = datetime.fromisoformat(slot["start_at"].replace("Z", "+00:00"))
            assert start_at.date() != monday_date

    def test_list_slots_with_date_exception_custom_hours(
        self, client, session, nutritionist, working_hours
    ):
        """Test that custom hours in date exceptions replace regular working hours."""
        # Create date exception with custom hours for tomorrow
        tomorrow = date.today() + timedelta(days=1)
        # Find next Monday
        days_until_monday = (0 - tomorrow.weekday()) % 7
        if days_until_monday == 0 and tomorrow.weekday() != 0:
            days_until_monday = 7
        monday_date = tomorrow + timedelta(days=days_until_monday)

        exception = DateException(
            nutritionist_id=nutritionist.nutritionist_id,
            exception_date=monday_date,
            exception_type="custom",
            custom_hours=[{"start": "15:00", "end": "17:00"}],  # Different hours
        )
        session.add(exception)
        session.commit()

        response = client.get(
            f"/api/public/nutritionists/{nutritionist.nutritionist_id}/slots"
        )

        assert response.status_code == 200
        data = response.json

        # Find slots on the exception date
        exception_slots = [
            slot
            for slot in data["slots"]
            if datetime.fromisoformat(slot["start_at"].replace("Z", "+00:00")).date()
            == monday_date
        ]

        # Should have custom hours (15:00-17:00), not regular hours (09:00-12:00)
        if exception_slots:
            for slot in exception_slots:
                start_at = datetime.fromisoformat(
                    slot["start_at"].replace("Z", "+00:00")
                )
                # Should be in custom hours range
                assert start_at.hour >= 15
                assert start_at.hour < 17

    @patch("app.services.google_calendar.GoogleCalendarService.get_freebusy")
    def test_list_slots_with_google_calendar_busy_exclusion(
        self, mock_get_freebusy, client, session, nutritionist, working_hours
    ):
        """Test that Google Calendar busy intervals are excluded from availability."""
        # Create connected Google Calendar
        calendar = GoogleCalendar(
            nutritionist_id=nutritionist.nutritionist_id,
            is_connected=True,
            access_token="test_token",
            refresh_token="test_refresh",
            selected_calendar_id="test@example.com",
            selected_calendar_summary="Test Calendar",
            connected_at=utc_now(),
        )
        session.add(calendar)
        session.commit()

        # Mock Google Calendar freebusy response
        tomorrow = date.today() + timedelta(days=1)
        # Find next Monday
        days_until_monday = (0 - tomorrow.weekday()) % 7
        if days_until_monday == 0 and tomorrow.weekday() != 0:
            days_until_monday = 7
        monday_date = tomorrow + timedelta(days=days_until_monday)

        # Create busy interval from 10:00-11:00 on Monday
        busy_start = datetime.combine(monday_date, datetime.min.time().replace(hour=10)).replace(
            tzinfo=timezone.utc
        )
        busy_end = datetime.combine(monday_date, datetime.min.time().replace(hour=11)).replace(
            tzinfo=timezone.utc
        )

        mock_get_freebusy.return_value = {
            "calendars": {
                "test@example.com": {
                    "busy": [
                        {
                            "start": busy_start.isoformat(),
                            "end": busy_end.isoformat(),
                        }
                    ]
                }
            }
        }

        response = client.get(
            f"/api/public/nutritionists/{nutritionist.nutritionist_id}/slots"
        )

        assert response.status_code == 200
        data = response.json

        # Verify busy interval is excluded
        for slot in data["slots"]:
            start_at = datetime.fromisoformat(slot["start_at"].replace("Z", "+00:00"))
            end_at = datetime.fromisoformat(slot["end_at"].replace("Z", "+00:00"))

            # Slot should not overlap with busy interval (10:00-11:00)
            if start_at.date() == monday_date:
                # Slot should be either before 10:00 or after 11:00
                assert end_at <= busy_start or start_at >= busy_end

    @patch("app.services.google_calendar.GoogleCalendarService.get_freebusy")
    def test_list_slots_google_calendar_error_handling(
        self, mock_get_freebusy, client, session, nutritionist, working_hours
    ):
        """Test that Google Calendar errors don't break availability calculation."""
        # Create connected Google Calendar
        calendar = GoogleCalendar(
            nutritionist_id=nutritionist.nutritionist_id,
            is_connected=True,
            access_token="test_token",
            refresh_token="test_refresh",
            selected_calendar_id="test@example.com",
            connected_at=utc_now(),
        )
        session.add(calendar)
        session.commit()

        # Mock Google Calendar error
        mock_get_freebusy.side_effect = ValueError("Calendar API error")

        # Should still return slots (without Google Calendar data)
        response = client.get(
            f"/api/public/nutritionists/{nutritionist.nutritionist_id}/slots"
        )

        assert response.status_code == 200
        data = response.json
        assert "slots" in data
        # Should still have slots from working hours
        assert len(data["slots"]) > 0

    def test_list_slots_no_working_hours(self, client, nutritionist):
        """Test listing slots when no working hours are configured."""
        response = client.get(
            f"/api/public/nutritionists/{nutritionist.nutritionist_id}/slots"
        )

        assert response.status_code == 200
        data = response.json
        assert data["slots"] == []

    def test_list_slots_nutritionist_not_found(self, client):
        """Test listing slots for non-existent nutritionist."""
        from uuid import uuid4

        response = client.get(f"/api/public/nutritionists/{uuid4()}/slots")
        assert response.status_code == 404

    def test_list_slots_inactive_nutritionist(self, client, session):
        """Test listing slots for inactive nutritionist."""
        profile = Profile(
            telegram_user_id=500000002,
            full_name="Inactive Nutritionist",
            role="nutritionist",
        )
        session.add(profile)
        session.flush()

        nutritionist = NutritionistProfile(
            nutritionist_id=profile.id,
            verification_status="approved",
            is_active=False,  # Inactive
        )
        session.add(nutritionist)
        session.commit()

        response = client.get(
            f"/api/public/nutritionists/{nutritionist.nutritionist_id}/slots"
        )
        assert response.status_code == 404

    def test_list_slots_with_service_filter(self, client, session, nutritionist, working_hours):
        """Test listing slots filtered by service."""
        # Create service
        service = Service(
            nutritionist_id=nutritionist.nutritionist_id,
            title="Test Service",
            duration_minutes=60,
            price_rub=3000,
            is_active=True,
        )
        session.add(service)
        session.commit()

        response = client.get(
            f"/api/public/nutritionists/{nutritionist.nutritionist_id}/slots",
            query_string={"service_id": str(service.id)},
        )

        assert response.status_code == 200
        data = response.json
        assert "slots" in data

    def test_list_slots_with_invalid_service(self, client, nutritionist, working_hours):
        """Test listing slots with invalid service_id."""
        from uuid import uuid4

        response = client.get(
            f"/api/public/nutritionists/{nutritionist.nutritionist_id}/slots",
            query_string={"service_id": str(uuid4())},
        )
        assert response.status_code == 404

    def test_list_slots_with_days_ahead_parameter(self, client, nutritionist, working_hours):
        """Test listing slots with custom days_ahead parameter."""
        response = client.get(
            f"/api/public/nutritionists/{nutritionist.nutritionist_id}/slots",
            query_string={"days_ahead": 7},
        )

        assert response.status_code == 200
        data = response.json

        # Verify all slots are within 7 days
        max_date = date.today() + timedelta(days=7)
        for slot in data["slots"]:
            start_at = datetime.fromisoformat(slot["start_at"].replace("Z", "+00:00"))
            assert start_at.date() <= max_date

    @patch("app.services.google_calendar.GoogleCalendarService.get_freebusy")
    def test_list_slots_complex_scenario(
        self, mock_get_freebusy, client, session, nutritionist, working_hours
    ):
        """Test complex scenario: working hours + date exception + Google busy."""
        # Create date exception (off day)
        tomorrow = date.today() + timedelta(days=1)
        days_until_monday = (0 - tomorrow.weekday()) % 7
        if days_until_monday == 0 and tomorrow.weekday() != 0:
            days_until_monday = 7
        monday_date = tomorrow + timedelta(days=days_until_monday)

        exception = DateException(
            nutritionist_id=nutritionist.nutritionist_id,
            exception_date=monday_date,
            exception_type="off",
        )
        session.add(exception)
        session.commit()

        # Create connected Google Calendar
        calendar = GoogleCalendar(
            nutritionist_id=nutritionist.nutritionist_id,
            is_connected=True,
            access_token="test_token",
            refresh_token="test_refresh",
            selected_calendar_id="test@example.com",
            connected_at=utc_now(),
        )
        session.add(calendar)
        session.commit()

        # Find next Tuesday (after Monday)
        tuesday_date = monday_date + timedelta(days=1)

        # Mock busy interval on Tuesday 15:00-16:00
        busy_start = datetime.combine(
            tuesday_date, datetime.min.time().replace(hour=15)
        ).replace(tzinfo=timezone.utc)
        busy_end = datetime.combine(
            tuesday_date, datetime.min.time().replace(hour=16)
        ).replace(tzinfo=timezone.utc)

        mock_get_freebusy.return_value = {
            "calendars": {
                "test@example.com": {
                    "busy": [
                        {
                            "start": busy_start.isoformat(),
                            "end": busy_end.isoformat(),
                        }
                    ]
                }
            }
        }

        response = client.get(
            f"/api/public/nutritionists/{nutritionist.nutritionist_id}/slots"
        )

        assert response.status_code == 200
        data = response.json

        # Verify Monday has no slots (exception: off)
        # Verify Tuesday has slots but not 15:00-16:00 (busy)
        for slot in data["slots"]:
            start_at = datetime.fromisoformat(slot["start_at"].replace("Z", "+00:00"))
            end_at = datetime.fromisoformat(slot["end_at"].replace("Z", "+00:00"))

            # No slots on Monday
            assert start_at.date() != monday_date

            # Tuesday slots should not overlap with busy interval
            if start_at.date() == tuesday_date:
                assert end_at <= busy_start or start_at >= busy_end
