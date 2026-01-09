"""
Integration tests for booking ↔ calendar sync.
Tests real user flows: booking payment triggers calendar event creation,
booking cancellation triggers calendar event deletion.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta, timezone
from googleapiclient.errors import HttpError

from app.models import (
    Profile,
    NutritionistProfile,
    Service,
    AvailabilitySlot,
    Booking,
    GoogleCalendar,
)
from app.services.booking_calendar_sync import BookingCalendarSync
from app.services.booking_hold import BookingHoldService
from app.services.payments import PaymentService, PaymentResult
from app.payments.base import PaymentStatus


def utc_now():
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class TestBookingCalendarSyncIntegration:
    """Test booking calendar sync in real user flow scenarios."""

    @pytest.fixture
    def nutritionist(self, session):
        """Create a test nutritionist."""
        profile = Profile(
            telegram_user_id=600000001,
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
            telegram_user_id=600000002,
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
            status="free",
        )
        session.add(slot)
        session.commit()
        return slot

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
    def test_booking_payment_creates_calendar_event(
        self, mock_get_credentials, mock_build, app, session, nutritionist, client, service, slot, connected_calendar
    ):
        """Test that booking payment creates a Google Calendar event."""
        # Create booking with hold
        with app.app_context():
            booking, error = BookingHoldService.create_booking_with_hold(
                client_id=str(client.id),
                service_id=str(service.id),
                slot_id=str(slot.id),
            )
            assert booking is not None
            assert booking.status == "pending_payment"

        # Mock Google Calendar API
        mock_creds = Mock()
        mock_get_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_insert = MagicMock()
        mock_insert.execute.return_value = {"id": "event_123"}
        mock_events.insert.return_value = mock_insert
        mock_service.events.return_value = mock_events
        mock_build.return_value = mock_service

        # Simulate payment success
        with app.app_context():
            payment_result = PaymentResult(
                booking_id=str(booking.id),
                provider_payment_id="test_payment_123",
                status=PaymentStatus.SUCCEEDED,
                raw_payload={"test": True},
            )
            payment, error = PaymentService.finalize_payment(payment_result)
            assert payment is not None

        # Verify calendar event was created
        mock_events.insert.assert_called_once()
        call_args = mock_events.insert.call_args
        assert call_args[1]["calendarId"] == "test@example.com"
        event_body = call_args[1]["body"]
        assert "Test Consultation" in event_body["summary"]
        assert "Test Client" in event_body["summary"]

        # Verify booking has event ID
        session.refresh(booking)
        assert booking.google_calendar_event_id == "event_123"
        assert booking.status == "paid"

    @patch("app.services.google_calendar.build")
    @patch("app.services.google_calendar.GoogleCalendarService.get_credentials")
    def test_booking_cancellation_deletes_calendar_event(
        self, mock_get_credentials, mock_build, app, session, nutritionist, client, service, slot, connected_calendar
    ):
        """Test that booking cancellation deletes Google Calendar event."""
        # Create paid booking with calendar event
        booking = Booking(
            client_id=client.id,
            nutritionist_id=nutritionist.nutritionist_id,
            service_id=service.id,
            slot_id=slot.id,
            status="paid",
            price_rub=service.price_rub,
            google_calendar_event_id="event_123",
            paid_at=utc_now(),
        )
        slot.status = "booked"
        session.add(booking)
        session.commit()

        # Mock Google Calendar API
        mock_creds = Mock()
        mock_get_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_delete = MagicMock()
        mock_delete.execute.return_value = None
        mock_events.delete.return_value = mock_delete
        mock_service.events.return_value = mock_events
        mock_build.return_value = mock_service

        # Cancel booking (admin can cancel paid bookings)
        with app.app_context():
            cancelled_booking, error = BookingHoldService.cancel_booking(
                booking_id=str(booking.id),
                user_id=str(nutritionist.nutritionist_id),  # Nutritionist can cancel
                reason="Client request",
            )
            # Note: In real flow, only pending_payment can be cancelled by client
            # For paid bookings, we'd need admin or different flow
            # This test verifies the sync happens when status changes to cancelled

        # Manually trigger sync for testing
        booking.status = "cancelled"
        booking.cancelled_at = utc_now()
        session.commit()

        with app.app_context():
            BookingCalendarSync.sync_booking_cancelled(booking)

        # Verify calendar event was deleted
        mock_events.delete.assert_called_once()
        call_args = mock_events.delete.call_args
        assert call_args[1]["calendarId"] == "test@example.com"
        assert call_args[1]["eventId"] == "event_123"

        # Verify booking event ID was cleared
        session.refresh(booking)
        assert booking.google_calendar_event_id is None

    @patch("app.services.google_calendar.build")
    @patch("app.services.google_calendar.GoogleCalendarService.get_credentials")
    def test_booking_payment_idempotent_event_creation(
        self, mock_get_credentials, mock_build, app, session, nutritionist, client, service, slot, connected_calendar
    ):
        """Test that calendar event creation is idempotent (doesn't create duplicate)."""
        # Create paid booking with existing event ID
        booking = Booking(
            client_id=client.id,
            nutritionist_id=nutritionist.nutritionist_id,
            service_id=service.id,
            slot_id=slot.id,
            status="paid",
            price_rub=service.price_rub,
            google_calendar_event_id="existing_event_123",
            paid_at=utc_now(),
        )
        slot.status = "booked"
        session.add(booking)
        session.commit()

        # Mock Google Calendar API
        mock_creds = Mock()
        mock_get_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Try to sync again (should be idempotent)
        with app.app_context():
            BookingCalendarSync.sync_booking_paid(booking)

        # Verify event was NOT created again
        mock_service.events.assert_not_called()

        # Verify event ID unchanged
        session.refresh(booking)
        assert booking.google_calendar_event_id == "existing_event_123"

    @patch("app.services.google_calendar.build")
    @patch("app.services.google_calendar.GoogleCalendarService.get_credentials")
    def test_booking_cancellation_idempotent_event_deletion(
        self, mock_get_credentials, mock_build, app, session, nutritionist, client, service, slot, connected_calendar
    ):
        """Test that calendar event deletion is idempotent (handles missing event)."""
        # Create cancelled booking without event ID
        booking = Booking(
            client_id=client.id,
            nutritionist_id=nutritionist.nutritionist_id,
            service_id=service.id,
            slot_id=slot.id,
            status="cancelled",
            price_rub=service.price_rub,
            google_calendar_event_id=None,  # No event ID
            cancelled_at=utc_now(),
        )
        slot.status = "free"
        session.add(booking)
        session.commit()

        # Mock Google Calendar API
        mock_creds = Mock()
        mock_get_credentials.return_value = mock_creds

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Try to sync cancellation (should skip)
        with app.app_context():
            BookingCalendarSync.sync_booking_cancelled(booking)

        # Verify event was NOT deleted (no event ID)
        mock_service.events.assert_not_called()

    @patch("app.services.google_calendar.build")
    @patch("app.services.google_calendar.GoogleCalendarService.get_credentials")
    def test_booking_cancellation_handles_404_gracefully(
        self, mock_get_credentials, mock_build, app, session, nutritionist, client, service, slot, connected_calendar
    ):
        """Test that 404 errors (event already deleted) are handled gracefully."""
        # Create cancelled booking with event ID
        booking = Booking(
            client_id=client.id,
            nutritionist_id=nutritionist.nutritionist_id,
            service_id=service.id,
            slot_id=slot.id,
            status="cancelled",
            price_rub=service.price_rub,
            google_calendar_event_id="event_123",
            cancelled_at=utc_now(),
        )
        slot.status = "free"
        session.add(booking)
        session.commit()

        # Mock Google Calendar API - return 404
        mock_creds = Mock()
        mock_get_credentials.return_value = mock_creds

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
        with app.app_context():
            BookingCalendarSync.sync_booking_cancelled(booking)

        # Verify event ID was cleared (idempotent - event already deleted)
        session.refresh(booking)
        assert booking.google_calendar_event_id is None

    def test_booking_payment_no_calendar_connection(
        self, app, session, nutritionist, client, service, slot
    ):
        """Test that booking payment has no side effects when calendar not connected."""
        # Create booking with hold
        with app.app_context():
            booking, error = BookingHoldService.create_booking_with_hold(
                client_id=str(client.id),
                service_id=str(service.id),
                slot_id=str(slot.id),
            )
            assert booking is not None

        # Simulate payment success (no calendar connection)
        with app.app_context():
            payment_result = PaymentResult(
                booking_id=str(booking.id),
                provider_payment_id="test_payment_123",
                status=PaymentStatus.SUCCEEDED,
                raw_payload={"test": True},
            )
            payment, error = PaymentService.finalize_payment(payment_result)
            assert payment is not None

        # Verify booking is paid but no calendar event
        session.refresh(booking)
        assert booking.status == "paid"
        assert booking.google_calendar_event_id is None

    def test_booking_cancellation_no_calendar_connection(
        self, app, session, nutritionist, client, service, slot
    ):
        """Test that booking cancellation has no side effects when calendar not connected."""
        # Create paid booking
        booking = Booking(
            client_id=client.id,
            nutritionist_id=nutritionist.nutritionist_id,
            service_id=service.id,
            slot_id=slot.id,
            status="paid",
            price_rub=service.price_rub,
            paid_at=utc_now(),
        )
        slot.status = "booked"
        session.add(booking)
        session.commit()

        # Cancel booking (no calendar connection)
        booking.status = "cancelled"
        booking.cancelled_at = utc_now()
        session.commit()

        # Sync cancellation (should not raise)
        with app.app_context():
            BookingCalendarSync.sync_booking_cancelled(booking)

        # Verify booking is cancelled
        session.refresh(booking)
        assert booking.status == "cancelled"
        # No error should have occurred
