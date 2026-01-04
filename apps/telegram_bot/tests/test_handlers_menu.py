"""
Unit tests for menu navigation handlers.
Tests nutritionist menu, role selection, and cabinet navigation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from handlers.menu import (
    handle_for_nutritionists,
    handle_i_am_nutritionist,
    handle_personal_cabinet,
)
from keyboards import CB_FOR_NUTRITIONISTS, CB_I_AM_NUTRITIONIST, CB_PERSONAL_CABINET
from tests.conftest import create_message, create_callback_query


pytestmark = pytest.mark.asyncio


class TestForNutritionistsMenu:
    """Tests for 'Для нутрициологов' menu."""
    
    async def test_shows_new_user_options(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that new users see 'Я нутрициолог' button."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_FOR_NUTRITIONISTS)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        # No nutritionist data in state
        await fsm_context.update_data(nutritionist=None)
        
        # Act
        await handle_for_nutritionists(callback, fsm_context)
        
        # Assert
        callback.answer.assert_called_once()
        callback.message.edit_text.assert_called_once()
        
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Check Russian text
        assert "нутрициолог" in text.lower()
        
        # Check buttons
        reply_markup = call_args.kwargs.get("reply_markup")
        buttons = []
        for row in reply_markup.inline_keyboard:
            for btn in row:
                buttons.append(btn)
        
        button_texts = [b.text for b in buttons]
        assert any("Я нутрициолог" in t for t in button_texts)
        assert any("Создать профиль" in t for t in button_texts)
    
    async def test_shows_existing_nutritionist_options(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that existing nutritionists see update and cabinet options."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_FOR_NUTRITIONISTS)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        # Set nutritionist data in state
        await fsm_context.update_data(
            nutritionist={
                "nutritionist_id": "test-id",
                "verification_status": "pending",
            }
        )
        
        # Act
        await handle_for_nutritionists(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        reply_markup = call_args.kwargs.get("reply_markup")
        
        buttons = []
        for row in reply_markup.inline_keyboard:
            for btn in row:
                buttons.append(btn)
        
        button_texts = [b.text for b in buttons]
        assert any("Обновить профиль" in t for t in button_texts)
        assert any("Личный кабинет" in t for t in button_texts)
    
    async def test_shows_verification_status(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that verification status is displayed."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_FOR_NUTRITIONISTS)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={
                "nutritionist_id": "test-id",
                "verification_status": "pending",
            }
        )
        
        # Act
        await handle_for_nutritionists(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should show status
        assert "модерац" in text.lower() or "pending" in text.lower() or "⏳" in text


class TestIAmNutritionist:
    """Tests for 'Я нутрициолог' role selection."""
    
    async def test_creates_nutritionist_profile(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that tapping 'Я нутрициолог' creates profile."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_I_AM_NUTRITIONIST)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(telegram_user_id=test_user.id)
        
        with patch("handlers.menu.get_api_client", return_value=mock_api_client):
            # Act
            await handle_i_am_nutritionist(callback, fsm_context)
        
        # Assert - API called
        mock_api_client.upsert_nutritionist.assert_called_once()
        call_args = mock_api_client.upsert_nutritionist.call_args
        
        assert call_args.kwargs["telegram_user_id"] == test_user.id
        assert call_args.kwargs["submit_for_verification"] == False
    
    async def test_shows_confirmation_message(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that confirmation message is shown in Russian."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_I_AM_NUTRITIONIST)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        with patch("handlers.menu.get_api_client", return_value=mock_api_client):
            # Act
            await handle_i_am_nutritionist(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Check Russian confirmation
        assert "Отлично" in text
        # Check mentions next steps
        assert "профиль" in text.lower()
        assert "услуг" in text.lower()
    
    async def test_updates_role_in_state(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that role is updated in FSM state."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_I_AM_NUTRITIONIST)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(role="client")
        
        with patch("handlers.menu.get_api_client", return_value=mock_api_client):
            # Act
            await handle_i_am_nutritionist(callback, fsm_context)
        
        # Assert
        data = await fsm_context.get_data()
        assert data.get("role") == "nutritionist"
        assert data.get("nutritionist") is not None


class TestPersonalCabinet:
    """Tests for personal cabinet handler."""
    
    async def test_shows_cabinet_with_stats(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that cabinet shows statistics."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_PERSONAL_CABINET)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={
                "nutritionist_id": "test-id",
                "profile": {"full_name": "Тест"},
            }
        )
        
        with patch("handlers.menu.get_api_client", return_value=mock_api_client):
            # Act
            await handle_personal_cabinet(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should show cabinet title
        assert "кабинет" in text.lower()
        # Should show stats
        assert "записей" in text.lower() or "booking" in text.lower() or "₽" in text
    
    async def test_shows_error_without_profile(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that error is shown without nutritionist profile."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_PERSONAL_CABINET)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        # No nutritionist in state
        await fsm_context.update_data(nutritionist=None)
        
        # Act
        await handle_personal_cabinet(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should show error
        assert "не найден" in text.lower() or "создайте" in text.lower()
    
    async def test_cabinet_has_all_menu_options(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that cabinet shows all menu options."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_PERSONAL_CABINET)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        with patch("handlers.menu.get_api_client", return_value=mock_api_client):
            # Act
            await handle_personal_cabinet(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        reply_markup = call_args.kwargs.get("reply_markup")
        
        buttons = []
        for row in reply_markup.inline_keyboard:
            for btn in row:
                buttons.append(btn.text)
        
        # Check for expected menu items
        expected_items = ["услуг", "календарь", "отзыв", "статистик", "настройк", "поддержк"]
        for item in expected_items:
            assert any(item.lower() in btn.lower() for btn in buttons), f"Missing: {item}"

