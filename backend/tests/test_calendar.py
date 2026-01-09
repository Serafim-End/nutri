"""
Tests for Google Calendar integration endpoints.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from app.models import Profile, NutritionistProfile, GoogleCalendar


class TestGoogleCalendar:
    """Test Google Calendar integration endpoints."""

    @pytest.fixture
    def nutritionist(self, session):
        """Create a test nutritionist."""
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
            is_active=True,
        )
        session.add(nutritionist)
        session.commit()
        return nutritionist

    @pytest.fixture
    def nutritionist_headers(self, app, session, nutritionist):
        """Create authenticated headers for nutritionist."""
        from flask_jwt_extended import create_access_token

        with app.app_context():
            token = create_access_token(
                identity=str(nutritionist.nutritionist_id),
                additional_claims={
                    "role": "nutritionist",
                    "telegram_user_id": 123456789,
                },
            )
            return {"Authorization": f"Bearer {token}"}

    def test_get_calendar_status_not_connected(self, client, nutritionist_headers, nutritionist):
        """Test getting calendar status when not connected."""
        response = client.get(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/status",
            headers=nutritionist_headers,
        )
        assert response.status_code == 200
        data = response.json
        assert data["calendar"]["is_connected"] is False
        assert data["calendar"]["nutritionist_id"] == str(nutritionist.nutritionist_id)

    def test_get_calendar_status_connected(self, client, session, nutritionist_headers, nutritionist):
        """Test getting calendar status when connected."""
        calendar = GoogleCalendar(
            nutritionist_id=nutritionist.nutritionist_id,
            is_connected=True,
            selected_calendar_id="test@example.com",
            selected_calendar_summary="Test Calendar",
            connected_at=datetime.now(timezone.utc),
        )
        session.add(calendar)
        session.commit()

        response = client.get(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/status",
            headers=nutritionist_headers,
        )
        assert response.status_code == 200
        data = response.json
        assert data["calendar"]["is_connected"] is True
        assert data["calendar"]["selected_calendar_id"] == "test@example.com"

    @patch("app.services.google_calendar.GoogleCalendarService.get_oauth_flow")
    def test_connect_google_calendar(self, mock_flow, client, nutritionist_headers, nutritionist):
        """Test getting OAuth authorization URL."""
        mock_flow_instance = Mock()
        mock_flow_instance.authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth?client_id=test",
            None,
        )
        mock_flow_instance.state = str(nutritionist.nutritionist_id)
        mock_flow.return_value = mock_flow_instance

        with patch.dict("app.config.Config.__dict__", {
            "GOOGLE_CLIENT_ID": "test_client_id",
            "GOOGLE_CLIENT_SECRET": "test_secret",
            "GOOGLE_REDIRECT_URI": "http://localhost:5000/callback",
        }):
            response = client.get(
                f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/connect",
                headers=nutritionist_headers,
            )
            assert response.status_code == 200
            assert "authorization_url" in response.json

    def test_connect_google_calendar_not_configured(self, client, nutritionist_headers, nutritionist):
        """Test connect when Google Calendar is not configured."""
        with patch.dict("app.config.Config.__dict__", {
            "GOOGLE_CLIENT_ID": "",
            "GOOGLE_CLIENT_SECRET": "",
            "GOOGLE_REDIRECT_URI": "",
        }):
            response = client.get(
                f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/connect",
                headers=nutritionist_headers,
            )
            assert response.status_code == 400
            assert "error" in response.json

    @patch("app.services.google_calendar.GoogleCalendarService.get_oauth_flow")
    def test_google_calendar_callback(self, mock_flow, client, session, nutritionist_headers, nutritionist):
        """Test OAuth callback handling."""
        # Mock credentials
        mock_credentials = Mock()
        mock_credentials.token = "access_token_123"
        mock_credentials.refresh_token = "refresh_token_123"
        mock_credentials.expiry = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_flow_instance = Mock()
        mock_flow_instance.fetch_token = Mock()
        mock_flow_instance.credentials = mock_credentials
        mock_flow.return_value = mock_flow_instance

        with patch.dict("app.config.Config.__dict__", {
            "GOOGLE_CLIENT_ID": "test_client_id",
            "GOOGLE_CLIENT_SECRET": "test_secret",
            "GOOGLE_REDIRECT_URI": "http://localhost:5000/callback",
        }):
            response = client.get(
                f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/callback",
                query_string={"code": "auth_code_123", "state": str(nutritionist.nutritionist_id)},
                headers=nutritionist_headers,
            )
            assert response.status_code == 200
            data = response.json
            assert data["calendar"]["is_connected"] is True

            # Verify calendar was saved
            calendar = GoogleCalendar.query.filter_by(
                nutritionist_id=nutritionist.nutritionist_id
            ).first()
            assert calendar is not None
            assert calendar.is_connected is True

    def test_disconnect_google_calendar(self, client, session, nutritionist_headers, nutritionist):
        """Test disconnecting Google Calendar."""
        calendar = GoogleCalendar(
            nutritionist_id=nutritionist.nutritionist_id,
            is_connected=True,
            access_token="token",
            refresh_token="refresh",
            connected_at=datetime.now(timezone.utc),
        )
        session.add(calendar)
        session.commit()

        response = client.post(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/disconnect",
            headers=nutritionist_headers,
        )
        assert response.status_code == 200
        assert response.json["message"] == "Calendar disconnected"

        # Verify calendar was disconnected
        session.refresh(calendar)
        assert calendar.is_connected is False
        assert calendar.access_token is None

    def test_disconnect_google_calendar_not_connected(self, client, nutritionist_headers, nutritionist):
        """Test disconnecting when not connected."""
        response = client.post(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/disconnect",
            headers=nutritionist_headers,
        )
        assert response.status_code == 404

    @patch("app.services.google_calendar.build")
    @patch("app.services.google_calendar.GoogleCalendarService.get_credentials")
    def test_list_calendars(self, mock_get_credentials, mock_build, client, session, nutritionist_headers, nutritionist):
        """Test listing calendars."""
        # Setup calendar connection
        calendar = GoogleCalendar(
            nutritionist_id=nutritionist.nutritionist_id,
            is_connected=True,
            access_token="token",
            refresh_token="refresh",
            connected_at=datetime.now(timezone.utc),
        )
        session.add(calendar)
        session.commit()

        # Mock Google Calendar API
        mock_credentials = Mock(spec=Credentials)
        mock_get_credentials.return_value = mock_credentials

        mock_service = Mock()
        mock_calendar_list = Mock()
        mock_calendar_list.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "primary",
                    "summary": "Primary Calendar",
                    "primary": True,
                    "accessRole": "owner",
                    "backgroundColor": "#9fe1e7",
                    "foregroundColor": "#000000",
                },
                {
                    "id": "test@example.com",
                    "summary": "Test Calendar",
                    "primary": False,
                    "accessRole": "owner",
                },
            ]
        }
        mock_service.calendarList.return_value = mock_calendar_list
        mock_build.return_value = mock_service

        response = client.get(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/calendars",
            headers=nutritionist_headers,
        )
        assert response.status_code == 200
        data = response.json
        assert len(data["calendars"]) == 2
        assert data["calendars"][0]["id"] == "primary"
        assert data["calendars"][0]["summary"] == "Primary Calendar"

    def test_list_calendars_not_connected(self, client, nutritionist_headers, nutritionist):
        """Test listing calendars when not connected."""
        response = client.get(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/calendars",
            headers=nutritionist_headers,
        )
        assert response.status_code == 400
        assert "not connected" in response.json["error"].lower()

    @patch("app.services.google_calendar.build")
    @patch("app.services.google_calendar.GoogleCalendarService.get_credentials")
    def test_select_calendar(self, mock_get_credentials, mock_build, client, session, nutritionist_headers, nutritionist):
        """Test selecting a calendar."""
        # Setup calendar connection
        calendar = GoogleCalendar(
            nutritionist_id=nutritionist.nutritionist_id,
            is_connected=True,
            access_token="token",
            refresh_token="refresh",
            connected_at=datetime.now(timezone.utc),
        )
        session.add(calendar)
        session.commit()

        # Mock Google Calendar API
        mock_credentials = Mock(spec=Credentials)
        mock_get_credentials.return_value = mock_credentials

        mock_service = Mock()
        mock_calendars = Mock()
        mock_calendars.get.return_value.execute.return_value = {
            "id": "test@example.com",
            "summary": "Test Calendar",
        }
        mock_service.calendars.return_value = mock_calendars
        mock_build.return_value = mock_service

        response = client.post(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/select",
            json={"calendar_id": "test@example.com"},
            headers=nutritionist_headers,
        )
        assert response.status_code == 200
        data = response.json
        assert data["calendar"]["selected_calendar_id"] == "test@example.com"
        assert data["calendar"]["selected_calendar_summary"] == "Test Calendar"

    def test_select_calendar_missing_id(self, client, nutritionist_headers, nutritionist):
        """Test selecting calendar without calendar_id."""
        response = client.post(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/select",
            json={},
            headers=nutritionist_headers,
        )
        assert response.status_code == 400

    @patch("app.services.google_calendar.build")
    @patch("app.services.google_calendar.GoogleCalendarService.get_credentials")
    def test_get_freebusy(self, mock_get_credentials, mock_build, client, session, nutritionist_headers, nutritionist):
        """Test getting freebusy information."""
        # Setup calendar connection with selected calendar
        calendar = GoogleCalendar(
            nutritionist_id=nutritionist.nutritionist_id,
            is_connected=True,
            access_token="token",
            refresh_token="refresh",
            selected_calendar_id="test@example.com",
            selected_calendar_summary="Test Calendar",
            connected_at=datetime.now(timezone.utc),
        )
        session.add(calendar)
        session.commit()

        # Mock Google Calendar API
        mock_credentials = Mock(spec=Credentials)
        mock_get_credentials.return_value = mock_credentials

        mock_service = Mock()
        mock_freebusy = Mock()
        mock_freebusy.query.return_value.execute.return_value = {
            "calendars": {
                "test@example.com": {
                    "busy": [
                        {
                            "start": "2024-01-01T10:00:00Z",
                            "end": "2024-01-01T11:00:00Z",
                        },
                        {
                            "start": "2024-01-01T14:00:00Z",
                            "end": "2024-01-01T15:30:00Z",
                        },
                    ]
                }
            },
            "timeMin": "2024-01-01T00:00:00Z",
            "timeMax": "2024-01-01T23:59:59Z",
        }
        mock_service.freebusy.return_value = mock_freebusy
        mock_build.return_value = mock_service

        time_min = datetime.now(timezone.utc)
        time_max = time_min + timedelta(days=1)

        response = client.post(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/freebusy",
            json={
                "time_min": time_min.isoformat(),
                "time_max": time_max.isoformat(),
            },
            headers=nutritionist_headers,
        )
        assert response.status_code == 200
        data = response.json
        assert "calendars" in data
        assert "test@example.com" in data["calendars"]
        assert len(data["calendars"]["test@example.com"]["busy"]) == 2

    def test_get_freebusy_not_connected(self, client, nutritionist_headers, nutritionist):
        """Test getting freebusy when not connected."""
        time_min = datetime.now(timezone.utc)
        time_max = time_min + timedelta(days=1)

        response = client.post(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/freebusy",
            json={
                "time_min": time_min.isoformat(),
                "time_max": time_max.isoformat(),
            },
            headers=nutritionist_headers,
        )
        assert response.status_code == 400
        assert "not connected" in response.json["error"].lower()

    def test_get_freebusy_no_calendar_selected(self, client, session, nutritionist_headers, nutritionist):
        """Test getting freebusy when no calendar is selected."""
        calendar = GoogleCalendar(
            nutritionist_id=nutritionist.nutritionist_id,
            is_connected=True,
            access_token="token",
            refresh_token="refresh",
            connected_at=datetime.now(timezone.utc),
            # No selected_calendar_id
        )
        session.add(calendar)
        session.commit()

        time_min = datetime.now(timezone.utc)
        time_max = time_min + timedelta(days=1)

        response = client.post(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/freebusy",
            json={
                "time_min": time_min.isoformat(),
                "time_max": time_max.isoformat(),
            },
            headers=nutritionist_headers,
        )
        assert response.status_code == 400
        assert "no calendar selected" in response.json["error"].lower()

    def test_get_freebusy_invalid_time_range(self, client, session, nutritionist_headers, nutritionist):
        """Test getting freebusy with invalid time range."""
        calendar = GoogleCalendar(
            nutritionist_id=nutritionist.nutritionist_id,
            is_connected=True,
            access_token="token",
            refresh_token="refresh",
            selected_calendar_id="test@example.com",
            connected_at=datetime.now(timezone.utc),
        )
        session.add(calendar)
        session.commit()

        time_min = datetime.now(timezone.utc)
        time_max = time_min - timedelta(hours=1)  # Invalid: time_max < time_min

        response = client.post(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/freebusy",
            json={
                "time_min": time_min.isoformat(),
                "time_max": time_max.isoformat(),
            },
            headers=nutritionist_headers,
        )
        assert response.status_code == 400
        assert "time_max must be after time_min" in response.json["error"]

    def test_get_freebusy_missing_params(self, client, nutritionist_headers, nutritionist):
        """Test getting freebusy with missing parameters."""
        response = client.post(
            f"/api/nutritionists/{nutritionist.nutritionist_id}/calendar/freebusy",
            json={},
            headers=nutritionist_headers,
        )
        assert response.status_code == 400
        assert "time_min and time_max are required" in response.json["error"]
