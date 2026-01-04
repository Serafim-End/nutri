"""
Unit tests for /start command handler.
Tests the initial user routing and greeting.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import InlineKeyboardMarkup

from handlers.start import cmd_start
from tests.conftest import create_message


pytestmark = pytest.mark.asyncio


class TestStartCommand:
    """Tests for /start command handler."""
    
    async def test_start_new_user_shows_russian_greeting(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that new users see Russian greeting."""
        # Arrange
        message = create_message(test_user, test_chat, text="/start")
        message.answer = AsyncMock()
        
        mock_api_client.resolve_telegram_user.return_value = MagicMock(
            success=True,
            data={
                "profile": None,
                "nutritionist": None,
                "role": "client",
            },
            error=None,
            status_code=200,
        )
        
        with patch("handlers.start.get_api_client", return_value=mock_api_client):
            # Act
            await cmd_start(message, fsm_context)
        
        # Assert
        message.answer.assert_called_once()
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Check Russian greeting
        assert "Привет" in text
        assert "NutriMatch" in text
        assert "Добро пожаловать" in text
        
        # Check keyboard is provided
        reply_markup = call_args.kwargs.get("reply_markup")
        assert reply_markup is not None
        assert isinstance(reply_markup, InlineKeyboardMarkup)
    
    async def test_start_shows_webapp_button(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
        mock_config,
    ):
        """Test that main menu has WebApp button."""
        # Arrange
        message = create_message(test_user, test_chat, text="/start")
        message.answer = AsyncMock()
        
        with patch("handlers.start.get_api_client", return_value=mock_api_client), \
             patch("keyboards.get_config", return_value=mock_config):
            # Act
            await cmd_start(message, fsm_context)
        
        # Assert
        call_args = message.answer.call_args
        reply_markup = call_args.kwargs.get("reply_markup")
        
        # Check for WebApp button
        buttons = []
        for row in reply_markup.inline_keyboard:
            for btn in row:
                buttons.append(btn)
        
        # Should have WebApp button
        webapp_buttons = [b for b in buttons if b.web_app is not None]
        assert len(webapp_buttons) >= 1
        
        # Should have "Для нутрициологов" button
        nutritionist_buttons = [b for b in buttons if "нутрициолог" in (b.text or "").lower()]
        assert len(nutritionist_buttons) >= 1
    
    async def test_start_shows_nutritionist_role_message(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that nutritionists see role confirmation."""
        # Arrange
        message = create_message(test_user, test_chat, text="/start")
        message.answer = AsyncMock()
        
        mock_api_client.resolve_telegram_user.return_value = MagicMock(
            success=True,
            data={
                "profile": {
                    "full_name": "Тест Нутрициолог",
                    "role": "nutritionist",
                },
                "nutritionist": {
                    "nutritionist_id": "test-id",
                    "verification_status": "approved",
                },
                "role": "nutritionist",
            },
            error=None,
            status_code=200,
        )
        
        with patch("handlers.start.get_api_client", return_value=mock_api_client):
            # Act
            await cmd_start(message, fsm_context)
        
        # Assert
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should mention nutritionist role
        assert "нутрициолог" in text.lower()
    
    async def test_start_clears_fsm_state(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that /start clears any existing FSM state."""
        # Arrange
        message = create_message(test_user, test_chat, text="/start")
        message.answer = AsyncMock()
        
        # Set some existing state
        await fsm_context.set_state("SomeState:something")
        await fsm_context.update_data(some_key="some_value")
        
        with patch("handlers.start.get_api_client", return_value=mock_api_client):
            # Act
            await cmd_start(message, fsm_context)
        
        # Assert - state should be cleared
        current_state = await fsm_context.get_state()
        assert current_state is None
    
    async def test_start_stores_user_data_in_fsm(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that user info is stored in FSM data."""
        # Arrange
        message = create_message(test_user, test_chat, text="/start")
        message.answer = AsyncMock()
        
        with patch("handlers.start.get_api_client", return_value=mock_api_client):
            # Act
            await cmd_start(message, fsm_context)
        
        # Assert
        data = await fsm_context.get_data()
        assert data.get("telegram_user_id") == test_user.id
        assert data.get("role") == "client"
    
    async def test_start_handles_backend_error_gracefully(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that backend errors don't crash the handler."""
        # Arrange
        message = create_message(test_user, test_chat, text="/start")
        message.answer = AsyncMock()
        
        mock_api_client.resolve_telegram_user.return_value = MagicMock(
            success=False,
            data=None,
            error="Connection error",
            status_code=0,
        )
        
        with patch("handlers.start.get_api_client", return_value=mock_api_client):
            # Act - should not raise
            await cmd_start(message, fsm_context)
        
        # Assert - should still respond
        message.answer.assert_called_once()
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should still show greeting
        assert "Привет" in text

