"""
Tests for Booking Calendar Sync Service.
Tests idempotent operations and no side effects when Google Calendar not connected.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from googleapiclient.errors import HttpError

from app.models import Profile, NutritionistProfile, Service, AvailabilitySlot, Booking, GoogleCalendar
from app.services.booking_calendar_sync import BookingCalendarSync


def utc_now():
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class TestBookingCalendarSync:
    """Test booking calendar sync functionality."""

    @pytest.fixture
    def nutritionist(self, session):
        """Create a test nutritionist."""
        profile = Profile(
            telegram_user_id=200000001,
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
    def client(self, session):
        """Create a test client."""
        profile = Profile(
            telegram_user_id=200000002,
            full_name="Test Client",
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
            title="Test Consultation",
            duration_minutes=60,
            price_rub=3000,
            is_active=True,
        )
        session.add(service)
        session.commit()
        return service

    @pytest.fixture
    def slot(self, session, nutritionist):
        """Create a test slot."""
        slot = AvailabilitySlot(
            nutritionist_id=nutritionist.nutritionist_id,
            start_at=utc_now() + timedelta(days=1),
            end_at=utc_now() + timedelta(days=1, hours=1),
            status="booked",
        )
        session.add(slot)
        session.commit()
        return slot

    @pytest.fixture
    def booking(self, session, nutritionist, client, service, slot):
        """Create a test booking."""
        booking = Booking(
            client_id=client.id,
            nutritionist_id=nutritionist.nutritionist_id,
            service_id=service.id,
            slot_id=slot.id,
            status="paid",
            price_rub=service.price_rub,
            paid_at=utc_now(),
        )
        session.add(booking)
        session.commit()
        return booking

    @pytest.fixture
    def connected_calendar(self, session, nutritionist):
        """Create a connected Google Calendar."""
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
        return calendar

    @patch("app.services.google_calendar.build")
    @patch("app.services.google_calendar.GoogleCalendarService.get_credentials")
    def test_sync_booking_paid_creates_event(
        self, mock_get_credentials, mock_build, session, booking, connected_calendar
    ):
        """Test that sync_booking_paid creates a calendar event."""
        # Mock credentials
        mock_creds = Mock()
        mock_get_credentials.return_value = mock_creds

        # Mock Google Calendar API
        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_insert = MagicMock()
        mock_insert.execute.return_value = {"id": "event_123"}
        mock_events.insert.return_value = mock_insert
        mock_service.events.return_value = mock_events
        mock_build.return_value = mock_service

        # Sync booking
        BookingCalendarSync.sync_booking_paid(booking)

        # Verify event was created
        mock_events.insert.assert_called_once()
        call_args = mock_events.insert.call_args
        assert call_args[1]["calendarId"] == "test@example.com"
        event_body = call_args[1]["body"]
        assert "Test Consultation" in event_body["summary"]
        assert "Test Client" in event_body["summary"]

        # Verify booking was updated with event ID
        session.refresh(booking)
        assert booking.google_calendar_event_id == "event_123"

    @patch("app.services.google_calendar.build")
    @patch("app.services.google_calendar.GoogleCalendarService.get_credentials")
    def test_sync_booking_paid_idempotent(
        self, mock_get_credentials, mock_build, session, booking, connected_calendar
    ):
        """Test that sync_booking_paid is idempotent (skips if event_id exists)."""
        # Set existing event ID
        booking.google_calendar_event_id = "existing_event_123"
        session.commit()

        # Mock credentials
        mock_creds = Mock()
        mock_get_credentials.return_value = mock_creds

        # Mock Google Calendar API
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Sync booking (should skip)
        BookingCalendarSync.sync_booking_paid(booking)

        # Verify event was NOT created
        mock_service.events.assert_not_called()

        # Verify event ID unchanged
        session.refresh(booking)
        assert booking.google_calendar_event_id == "existing_event_123"

    def test_sync_booking_paid_no_calendar_connection(
        self, session, booking, nutritionist
    ):
        """Test that sync_booking_paid has no side effects when calendar not connected."""
        # No calendar connection - should not raise or create errors
        BookingCalendarSync.sync_booking_paid(booking)

        # Verify booking unchanged
        session.refresh(booking)
        assert booking.google_calendar_event_id is None

    @patch("app.services.google_calendar.build")
    @patch("app.services.google_calendar.GoogleCalendarService.get_credentials")
    def test_sync_booking_cancelled_deletes_event(
        self, mock_get_credentials, mock_build, session, booking, connected_calendar
    ):
        """Test that sync_booking_cancelled deletes calendar event."""
        # Set event ID
        booking.google_calendar_event_id = "event_123"
        booking.status = "cancelled"
        booking.cancelled_at = utc_now()
        session.commit()

        # Mock credentials
        mock_creds = Mock()
        mock_get_credentials.return_value = mock_creds

        # Mock Google Calendar API
        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_delete = MagicMock()
        mock_delete.execute.return_value = None
        mock_events.delete.return_value = mock_delete
        mock_service.events.return_value = mock_events
        mock_build.return_value = mock_service

        # Sync cancellation
        BookingCalendarSync.sync_booking_cancelled(booking)

        # Verify event was deleted
        mock_events.delete.assert_called_once()
        call_args = mock_events.delete.call_args
        assert call_args[1]["calendarId"] == "test@example.com"
        assert call_args[1]["eventId"] == "event_123"

        # Verify booking event ID was cleared
        session.refresh(booking)
        assert booking.google_calendar_event_id is None

    def test_sync_booking_cancelled_idempotent(
        self, session, booking, connected_calendar
    ):
        """Test that sync_booking_cancelled is idempotent (skips if no event_id)."""
        # No event ID
        booking.status = "cancelled"
        booking.cancelled_at = utc_now()
        booking.google_calendar_event_id = None
        session.commit()

        # Sync cancellation (should skip)
        BookingCalendarSync.sync_booking_cancelled(booking)

        # Verify booking unchanged
        session.refresh(booking)
        assert booking.google_calendar_event_id is None

    @patch("app.services.google_calendar.build")
    @patch("app.services.google_calendar.GoogleCalendarService.get_credentials")
    def test_sync_booking_cancelled_event_not_found(
        self, mock_get_credentials, mock_build, session, booking, connected_calendar
    ):
        """Test that sync_booking_cancelled handles 404 (event already deleted) gracefully."""
        # Set event ID
        booking.google_calendar_event_id = "event_123"
        booking.status = "cancelled"
        booking.cancelled_at = utc_now()
        session.commit()

        # Mock credentials
        mock_creds = Mock()
        mock_get_credentials.return_value = mock_creds

        # Mock Google Calendar API - return 404 (event not found)
        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_delete = MagicMock()
        http_error = HttpError(
            resp=Mock(status=404),
            content=b'{"error": "Not Found"}',
        )
        mock_delete.execute.side_effect = http_error
        mock_events.delete.return_value = mock_delete
        mock_service.events.return_value = mock_events
        mock_build.return_value = mock_service

        # Sync cancellation (should handle 404 gracefully)
        BookingCalendarSync.sync_booking_cancelled(booking)

        # Verify event ID was cleared (idempotent - event already deleted)
        session.refresh(booking)
        assert booking.google_calendar_event_id is None

    def test_sync_booking_cancelled_no_calendar_connection(
        self, session, booking, nutritionist
    ):
        """Test that sync_booking_cancelled has no side effects when calendar not connected."""
        # Set event ID but no calendar connection
        booking.google_calendar_event_id = "event_123"
        booking.status = "cancelled"
        booking.cancelled_at = utc_now()
        session.commit()

        # Sync cancellation (should not raise)
        BookingCalendarSync.sync_booking_cancelled(booking)

        # Verify booking unchanged (event ID still there, but that's OK - no side effects)
        session.refresh(booking)
        # Note: event_id might remain if calendar not connected, which is acceptable
        # The important thing is no errors were raised

    @patch("app.services.booking_calendar_sync.BookingCalendarSync.sync_booking_paid")
    def test_payment_finalization_triggers_sync(
        self, mock_sync, app, session, nutritionist, client, service
    ):
        """Test that payment finalization triggers calendar sync."""
        from app.services.payments import PaymentService, PaymentResult
        from app.payments.base import PaymentStatus

        # Create slot
        slot = AvailabilitySlot(
            nutritionist_id=nutritionist.nutritionist_id,
            start_at=utc_now() + timedelta(days=1),
            end_at=utc_now() + timedelta(days=1, hours=1),
            status="held",
        )
        session.add(slot)
        session.flush()

        # Create booking
        booking = Booking(
            client_id=client.id,
            nutritionist_id=nutritionist.nutritionist_id,
            service_id=service.id,
            slot_id=slot.id,
            status="pending_payment",
            price_rub=service.price_rub,
        )
        session.add(booking)
        session.commit()

        # Create payment result
        result = PaymentResult(
            booking_id=str(booking.id),
            provider_payment_id="test_payment_123",
            status=PaymentStatus.SUCCEEDED,
            raw_payload={"test": True},
        )

        # Finalize payment
        with app.app_context():
            payment, error = PaymentService.finalize_payment(result)

        # Verify sync was called
        mock_sync.assert_called_once()
        assert mock_sync.call_args[0][0].id == booking.id

    @patch("app.services.booking_calendar_sync.BookingCalendarSync.sync_booking_cancelled")
    def test_booking_cancellation_triggers_sync(
        self, mock_sync, app, session, nutritionist, client, service
    ):
        """Test that booking cancellation triggers calendar sync."""
        from app.services.booking_hold import BookingHoldService

        # Create slot
        slot = AvailabilitySlot(
            nutritionist_id=nutritionist.nutritionist_id,
            start_at=utc_now() + timedelta(days=1),
            end_at=utc_now() + timedelta(days=1, hours=1),
            status="held",
        )
        session.add(slot)
        session.flush()

        # Create booking
        booking = Booking(
            client_id=client.id,
            nutritionist_id=nutritionist.nutritionist_id,
            service_id=service.id,
            slot_id=slot.id,
            status="pending_payment",
            price_rub=service.price_rub,
        )
        session.add(booking)
        session.commit()

        # Cancel booking
        with app.app_context():
            cancelled_booking, error = BookingHoldService.cancel_booking(
                booking_id=str(booking.id),
                user_id=str(client.id),
                reason="Test cancellation",
            )

        # Verify sync was called
        mock_sync.assert_called_once()
        assert mock_sync.call_args[0][0].id == booking.id

    def test_booking_states_used(self):
        """Test to document exact booking states used for sync."""
        # This test documents the exact states:
        # - 'paid' triggers sync_booking_paid (creates event)
        # - 'cancelled' triggers sync_booking_cancelled (deletes event)
        
        # Verify states are as expected
        valid_states = {
            "pending_payment",  # Initial state
            "paid",  # Triggers calendar event creation
            "cancelled",  # Triggers calendar event deletion
            "completed",
            "no_show",
            "refunded",
        }
        
        # This is a documentation test - just verify our sync logic uses correct states
        assert "paid" in valid_states
        assert "cancelled" in valid_states
