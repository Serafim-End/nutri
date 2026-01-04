"""
Unit tests for services management handlers.
Tests service CRUD operations and validation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from handlers.services import (
    show_services,
    start_add_service,
    process_service_title,
    process_service_duration,
    process_service_price,
    confirm_create_service,
)
from states import ServiceStates
from keyboards import CB_MY_SERVICES, CB_ADD_SERVICE, CB_CONFIRM_SERVICE
from tests.conftest import create_message, create_callback_query


pytestmark = pytest.mark.asyncio


class TestServicesListView:
    """Tests for services list view."""
    
    async def test_shows_empty_state(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that empty services list shows appropriate message."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_MY_SERVICES)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        mock_api_client.list_services.return_value = MagicMock(
            success=True,
            data={"services": []},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.services.get_api_client", return_value=mock_api_client):
            # Act
            await show_services(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        assert "нет услуг" in text.lower() or "пока нет" in text.lower()
    
    async def test_shows_services_list(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that services are listed."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_MY_SERVICES)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        mock_api_client.list_services.return_value = MagicMock(
            success=True,
            data={
                "services": [
                    {"id": "1", "title": "Консультация", "price_rub": 3000, "is_active": True},
                    {"id": "2", "title": "Разбор анализов", "price_rub": 2000, "is_active": False},
                ]
            },
            error=None,
            status_code=200,
        )
        
        with patch("handlers.services.get_api_client", return_value=mock_api_client):
            # Act
            await show_services(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        reply_markup = call_args.kwargs.get("reply_markup")
        
        # Check count
        assert "2" in text
        
        # Check buttons include services
        buttons = []
        for row in reply_markup.inline_keyboard:
            for btn in row:
                buttons.append(btn.text)
        
        service_buttons = [b for b in buttons if "₽" in b]
        assert len(service_buttons) == 2


class TestServiceCreation:
    """Tests for service creation flow."""
    
    async def test_starts_with_title_prompt(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that service creation starts with title prompt."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_ADD_SERVICE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        # Act
        await start_add_service(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ServiceStates.waiting_title.state
        
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        assert "Шаг 1" in text
        assert "названи" in text.lower()


class TestServiceTitleValidation:
    """Tests for service title validation."""
    
    async def test_valid_title_proceeds(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that valid title proceeds to description."""
        # Arrange
        message = create_message(test_user, test_chat, text="Консультация по питанию")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ServiceStates.waiting_title)
        await fsm_context.update_data(service_draft={})
        
        # Act
        await process_service_title(message, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ServiceStates.waiting_description.state
        
        data = await fsm_context.get_data()
        assert data["service_draft"]["title"] == "Консультация по питанию"
    
    async def test_too_short_title_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that too short title shows error."""
        # Arrange
        message = create_message(test_user, test_chat, text="АБ")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ServiceStates.waiting_title)
        await fsm_context.update_data(service_draft={})
        
        # Act
        await process_service_title(message, fsm_context)
        
        # Assert - stays in same state
        state = await fsm_context.get_state()
        assert state == ServiceStates.waiting_title.state
        
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "коротк" in text.lower()


class TestServiceDurationValidation:
    """Tests for service duration validation."""
    
    async def test_valid_duration_proceeds(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that valid duration proceeds to price."""
        # Arrange
        message = create_message(test_user, test_chat, text="60")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ServiceStates.waiting_duration)
        await fsm_context.update_data(service_draft={"title": "Test"})
        
        # Act
        await process_service_duration(message, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ServiceStates.waiting_price.state
        
        data = await fsm_context.get_data()
        assert data["service_draft"]["duration_minutes"] == 60
    
    async def test_non_numeric_duration_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that non-numeric duration shows error."""
        # Arrange
        message = create_message(test_user, test_chat, text="abc")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ServiceStates.waiting_duration)
        await fsm_context.update_data(service_draft={})
        
        # Act
        await process_service_duration(message, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ServiceStates.waiting_duration.state
        
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "числ" in text.lower()
    
    async def test_too_short_duration_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that duration under 15 min shows error."""
        # Arrange
        message = create_message(test_user, test_chat, text="10")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ServiceStates.waiting_duration)
        await fsm_context.update_data(service_draft={})
        
        # Act
        await process_service_duration(message, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ServiceStates.waiting_duration.state
        
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "15" in text
    
    async def test_too_long_duration_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that duration over 240 min shows error."""
        # Arrange
        message = create_message(test_user, test_chat, text="300")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ServiceStates.waiting_duration)
        await fsm_context.update_data(service_draft={})
        
        # Act
        await process_service_duration(message, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ServiceStates.waiting_duration.state
        
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "240" in text


class TestServicePriceValidation:
    """Tests for service price validation."""
    
    async def test_valid_price_proceeds(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that valid price shows confirmation."""
        # Arrange
        message = create_message(test_user, test_chat, text="3000")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ServiceStates.waiting_price)
        await fsm_context.update_data(service_draft={
            "title": "Test Service",
            "duration_minutes": 60,
        })
        
        # Act
        await process_service_price(message, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ServiceStates.confirming_service.state
        
        data = await fsm_context.get_data()
        assert data["service_draft"]["price_rub"] == 3000
    
    async def test_price_too_low_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that price under 100 shows error."""
        # Arrange
        message = create_message(test_user, test_chat, text="50")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ServiceStates.waiting_price)
        await fsm_context.update_data(service_draft={})
        
        # Act
        await process_service_price(message, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ServiceStates.waiting_price.state
        
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "100" in text
    
    async def test_price_too_high_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that price over 100000 shows error."""
        # Arrange
        message = create_message(test_user, test_chat, text="150000")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ServiceStates.waiting_price)
        await fsm_context.update_data(service_draft={})
        
        # Act
        await process_service_price(message, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ServiceStates.waiting_price.state
        
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "100" in text  # "100 000"


class TestServiceConfirmation:
    """Tests for service creation confirmation."""
    
    async def test_successful_creation(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that service is created via API."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_CONFIRM_SERVICE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ServiceStates.confirming_service)
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"},
            service_draft={
                "title": "Консультация",
                "duration_minutes": 60,
                "price_rub": 3000,
            },
        )
        
        with patch("handlers.services.get_api_client", return_value=mock_api_client):
            # Act
            await confirm_create_service(callback, fsm_context)
        
        # Assert
        mock_api_client.create_service.assert_called_once()
        call_args = mock_api_client.create_service.call_args
        
        assert call_args.kwargs["title"] == "Консультация"
        assert call_args.kwargs["duration_minutes"] == 60
        assert call_args.kwargs["price_rub"] == 3000
    
    async def test_creation_clears_state(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that FSM state is cleared after creation."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_CONFIRM_SERVICE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ServiceStates.confirming_service)
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"},
            service_draft={
                "title": "Test",
                "duration_minutes": 60,
                "price_rub": 3000,
            },
        )
        
        with patch("handlers.services.get_api_client", return_value=mock_api_client):
            # Act
            await confirm_create_service(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state is None
        
        data = await fsm_context.get_data()
        assert data.get("service_draft") is None
    
    async def test_creation_shows_success_message(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that success message is shown in Russian."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_CONFIRM_SERVICE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ServiceStates.confirming_service)
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"},
            service_draft={
                "title": "Test",
                "duration_minutes": 60,
                "price_rub": 3000,
            },
        )
        
        with patch("handlers.services.get_api_client", return_value=mock_api_client):
            # Act
            await confirm_create_service(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        assert "создан" in text.lower()

