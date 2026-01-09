"""
Unit tests for personal cabinet handlers.
Tests bookings, reviews, statistics, calendar, settings, and support flows.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

from handlers.cabinet import (
    show_reviews,
    reviews_next,
    reviews_prev,
    show_statistics,
    show_calendar,
    show_settings,
    start_support,
    process_support_message,
)
from states import SupportStates
from keyboards import (
    CB_REVIEWS,
    CB_REVIEWS_NEXT,
    CB_REVIEWS_PREV,
    CB_STATISTICS,
    CB_CALENDAR,
    CB_SETTINGS,
    CB_SUPPORT,
    CB_CANCEL_SUPPORT,
)
from tests.conftest import create_message, create_callback_query


pytestmark = pytest.mark.asyncio


class TestBookingsList:
    """Tests for bookings list view."""
    
    async def test_shows_empty_bookings(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that empty bookings list shows appropriate message."""
        # Note: Bookings handler is in schedule.py and tested in test_handlers_schedule.py
        # This test placeholder is kept for reference but actual bookings tests are in schedule tests
        pass
    
    async def test_shows_bookings_with_pagination(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that bookings are shown with pagination."""
        # Note: Bookings handler is in schedule.py and tested there
        # This test is kept for reference but bookings are covered in schedule tests
        pass


class TestReviewsList:
    """Tests for reviews list view."""
    
    async def test_shows_empty_reviews(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that empty reviews list shows appropriate message."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_REVIEWS)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        mock_api_client.get_reviews.return_value = MagicMock(
            success=True,
            data={"reviews": [], "total": 0},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.cabinet.get_api_client", return_value=mock_api_client):
            # Act
            await show_reviews(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        assert "нет отзывов" in text.lower() or "пока нет" in text.lower()
    
    async def test_shows_reviews_with_rating(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that reviews are shown with ratings."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_REVIEWS)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        mock_api_client.get_reviews.return_value = MagicMock(
            success=True,
            data={
                "reviews": [
                    {
                        "id": "1",
                        "rating": 5,
                        "client_name": "Мария Петрова",
                        "comment": "Отличная консультация!",
                        "created_at": "2024-01-15T10:00:00Z",
                    }
                ],
                "total": 1,
            },
            error=None,
            status_code=200,
        )
        
        with patch("handlers.cabinet.get_api_client", return_value=mock_api_client):
            # Act
            await show_reviews(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should show rating stars
        assert "⭐" in text
        # Should show client name
        assert "Мария" in text or "Петрова" in text
        # Should show comment
        assert "консультация" in text.lower()
    
    async def test_reviews_pagination_next(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that reviews pagination next works."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_REVIEWS_NEXT)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"},
            reviews_offset=0,
        )
        
        mock_api_client.get_reviews.return_value = MagicMock(
            success=True,
            data={"reviews": [], "total": 10},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.cabinet.get_api_client", return_value=mock_api_client):
            # Act
            await reviews_next(callback, fsm_context)
        
        # Assert
        data = await fsm_context.get_data()
        assert data.get("reviews_offset") == 5  # Next page offset
        
        # API called with new offset
        mock_api_client.get_reviews.assert_called_once()
        call_args = mock_api_client.get_reviews.call_args
        assert call_args.kwargs["offset"] == 5
    
    async def test_reviews_pagination_prev(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that reviews pagination prev works."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_REVIEWS_PREV)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"},
            reviews_offset=5,
        )
        
        mock_api_client.get_reviews.return_value = MagicMock(
            success=True,
            data={"reviews": [], "total": 10},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.cabinet.get_api_client", return_value=mock_api_client):
            # Act
            await reviews_prev(callback, fsm_context)
        
        # Assert
        data = await fsm_context.get_data()
        assert data.get("reviews_offset") == 0  # Previous page offset


class TestStatisticsView:
    """Tests for statistics view."""
    
    async def test_shows_statistics(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that statistics are displayed."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_STATISTICS)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        mock_api_client.get_statistics.return_value = MagicMock(
            success=True,
            data={
                "income_30d": 50000,
                "consultations_30d": 10,
                "avg_rating": 4.8,
                "total_clients": 25,
            },
            error=None,
            status_code=200,
        )
        
        with patch("handlers.cabinet.get_api_client", return_value=mock_api_client):
            # Act
            await show_statistics(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should show statistics
        assert "50" in text or "50000" in text  # Income
        assert "10" in text  # Consultations
        assert "4.8" in text or "4,8" in text  # Rating
        assert "25" in text  # Clients
    
    async def test_falls_back_to_dashboard_stats(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that falls back to dashboard stats if statistics endpoint fails."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_STATISTICS)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        mock_api_client.get_statistics.return_value = MagicMock(
            success=False,
            data=None,
            error="Not found",
            status_code=404,
        )
        
        mock_api_client.get_nutritionist_dashboard.return_value = MagicMock(
            success=True,
            data={
                "stats": {
                    "total_bookings": 15,
                    "completed_bookings": 12,
                    "total_earnings_rub": 45000,
                }
            },
            error=None,
            status_code=200,
        )
        
        with patch("handlers.cabinet.get_api_client", return_value=mock_api_client):
            # Act
            await show_statistics(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should show dashboard stats
        assert "15" in text or "12" in text  # Bookings
        assert "45" in text or "45000" in text  # Earnings


class TestCalendarSettings:
    """Tests for calendar settings view."""
    
    async def test_shows_connected_calendar(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that connected calendar is shown."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_CALENDAR)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        mock_api_client.get_calendar_status.return_value = MagicMock(
            success=True,
            data={"connected": True, "email": "test@example.com"},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.cabinet.get_api_client", return_value=mock_api_client):
            # Act
            await show_calendar(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should show connection status
        assert "подключён" in text.lower() or "✅" in text
        assert "test@example.com" in text
    
    async def test_shows_disconnected_calendar(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that disconnected calendar shows OAuth button."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_CALENDAR)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        mock_api_client.get_calendar_status.return_value = MagicMock(
            success=True,
            data={"connected": False},
            error=None,
            status_code=200,
        )
        
        mock_api_client.get_google_oauth_url.return_value = MagicMock(
            success=True,
            data={"url": "https://oauth.example.com/auth"},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.cabinet.get_api_client", return_value=mock_api_client):
            # Act
            await show_calendar(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        reply_markup = call_args.kwargs.get("reply_markup")
        
        # Should show not connected
        assert "не подключён" in text.lower() or "❌" in text
        
        # Should have OAuth button
        buttons = []
        for row in reply_markup.inline_keyboard:
            for btn in row:
                buttons.append(btn)
        
        # Check for URL button
        url_buttons = [b for b in buttons if b.url]
        assert len(url_buttons) >= 1


class TestSettingsView:
    """Tests for settings view."""
    
    async def test_shows_cancellation_policy(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that cancellation policy is shown."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_SETTINGS)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        # Act
        await show_settings(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should show policy
        assert "отмен" in text.lower() or "политик" in text.lower()
        assert "24" in text  # 24 hours mentioned
        assert "50%" in text or "50" in text  # 50% refund


class TestSupportFlow:
    """Tests for support message flow."""
    
    async def test_starts_support_flow(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that support flow starts with message prompt."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_SUPPORT)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        # Act
        await start_support(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == SupportStates.waiting_message.state
        
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        assert "поддержк" in text.lower() or "проблем" in text.lower()
    
    async def test_valid_support_message_sent(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that valid support message is sent."""
        # Arrange
        message = create_message(test_user, test_chat, text="У меня проблема с оплатой")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(SupportStates.waiting_message)
        await fsm_context.update_data(telegram_user_id=test_user.id)
        
        mock_api_client.send_support_message.return_value = MagicMock(
            success=True,
            data={},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.cabinet.get_api_client", return_value=mock_api_client):
            # Act
            await process_support_message(message, fsm_context)
        
        # Assert
        mock_api_client.send_support_message.assert_called_once()
        call_args = mock_api_client.send_support_message.call_args
        
        assert call_args.kwargs["telegram_user_id"] == test_user.id
        assert call_args.kwargs["message"] == "У меня проблема с оплатой"
        
        # State cleared
        state = await fsm_context.get_state()
        assert state is None
        
        # Success message shown
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "отправлено" in text.lower() or "✅" in text
    
    async def test_empty_support_message_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that empty support message shows error."""
        # Arrange
        message = create_message(test_user, test_chat, text="")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(SupportStates.waiting_message)
        
        # Act
        await process_support_message(message, fsm_context)
        
        # Assert - stays in same state
        state = await fsm_context.get_state()
        assert state == SupportStates.waiting_message.state
        
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "текстовое" in text.lower() or "сообщени" in text.lower()
    
    async def test_too_long_support_message_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that too long support message shows error."""
        # Arrange
        long_message = "А" * 1001
        message = create_message(test_user, test_chat, text=long_message)
        message.answer = AsyncMock()
        
        await fsm_context.set_state(SupportStates.waiting_message)
        
        # Act
        await process_support_message(message, fsm_context)
        
        # Assert - stays in same state
        state = await fsm_context.get_state()
        assert state == SupportStates.waiting_message.state
        
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "длинн" in text.lower() or "1000" in text
