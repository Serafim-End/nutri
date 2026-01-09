"""
Extended unit tests for services management handlers.
Tests service details, toggle, and delete operations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from handlers.services import (
    show_service_details,
    toggle_service_active,
    confirm_delete_service,
    delete_service,
)
from keyboards import (
    CB_EDIT_SERVICE_PREFIX,
    CB_SERVICE_TOGGLE_PREFIX,
    CB_DELETE_SERVICE_PREFIX,
    CB_CONFIRM_DELETE_PREFIX,
)
from tests.conftest import create_message, create_callback_query


pytestmark = pytest.mark.asyncio


class TestServiceDetails:
    """Tests for service details view."""
    
    async def test_shows_service_details(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that service details are displayed."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_EDIT_SERVICE_PREFIX}service-123")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            services=[
                {
                    "id": "service-123",
                    "title": "Консультация по питанию",
                    "description": "Полная консультация",
                    "duration_minutes": 60,
                    "price_rub": 3000,
                    "is_active": True,
                }
            ]
        )
        
        # Act
        await show_service_details(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should show service info
        assert "Консультация" in text
        assert "60" in text  # Duration
        assert "3000" in text or "3" in text  # Price
        assert "Активна" in text or "✅" in text  # Status
    
    async def test_shows_inactive_service(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that inactive service shows correct status."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_EDIT_SERVICE_PREFIX}service-123")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            services=[
                {
                    "id": "service-123",
                    "title": "Консультация",
                    "duration_minutes": 60,
                    "price_rub": 3000,
                    "is_active": False,
                }
            ]
        )
        
        # Act
        await show_service_details(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should show inactive status
        assert "Неактивна" in text or "⏸️" in text
    
    async def test_service_not_found_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that non-existent service shows error."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_EDIT_SERVICE_PREFIX}nonexistent")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(services=[])
        
        # Act
        await show_service_details(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        assert "не найдена" in text.lower() or "❌" in text


class TestServiceToggle:
    """Tests for service activation/deactivation."""
    
    async def test_toggles_service_to_inactive(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that service can be deactivated."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_SERVICE_TOGGLE_PREFIX}service-123")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"},
            services=[
                {
                    "id": "service-123",
                    "title": "Консультация",
                    "is_active": True,
                }
            ]
        )
        
        mock_api_client.update_service.return_value = MagicMock(
            success=True,
            data={"service": {"id": "service-123", "is_active": False}},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.services.get_api_client", return_value=mock_api_client):
            # Act
            await toggle_service_active(callback, fsm_context)
        
        # Assert
        mock_api_client.update_service.assert_called_once()
        call_args = mock_api_client.update_service.call_args
        
        assert call_args.kwargs["nutritionist_id"] == "test-id"
        assert call_args.kwargs["service_id"] == "service-123"
        assert call_args.kwargs["is_active"] == False
        
        # Local cache updated
        data = await fsm_context.get_data()
        service = next(s for s in data["services"] if s["id"] == "service-123")
        assert service["is_active"] == False
    
    async def test_toggles_service_to_active(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that service can be activated."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_SERVICE_TOGGLE_PREFIX}service-123")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"},
            services=[
                {
                    "id": "service-123",
                    "title": "Консультация",
                    "is_active": False,
                }
            ]
        )
        
        mock_api_client.update_service.return_value = MagicMock(
            success=True,
            data={"service": {"id": "service-123", "is_active": True}},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.services.get_api_client", return_value=mock_api_client):
            # Act
            await toggle_service_active(callback, fsm_context)
        
        # Assert
        call_args = mock_api_client.update_service.call_args
        assert call_args.kwargs["is_active"] == True
        
        # Local cache updated
        data = await fsm_context.get_data()
        service = next(s for s in data["services"] if s["id"] == "service-123")
        assert service["is_active"] == True


class TestServiceDeletion:
    """Tests for service deletion flow."""
    
    async def test_shows_delete_confirmation(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that delete confirmation is shown."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_DELETE_SERVICE_PREFIX}service-123")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        # Act
        await confirm_delete_service(callback)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should show warning
        assert "удалени" in text.lower() or "⚠️" in text
        assert "нельзя отменить" in text.lower() or "нельзя" in text.lower()
    
    async def test_deletes_service_successfully(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that service is deleted successfully."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_CONFIRM_DELETE_PREFIX}service-123")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"},
            services=[
                {
                    "id": "service-123",
                    "title": "Консультация",
                },
                {
                    "id": "service-456",
                    "title": "Другая услуга",
                },
            ]
        )
        
        mock_api_client.delete_service.return_value = MagicMock(
            success=True,
            data={},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.services.get_api_client", return_value=mock_api_client):
            # Act
            await delete_service(callback, fsm_context)
        
        # Assert
        mock_api_client.delete_service.assert_called_once()
        call_args = mock_api_client.delete_service.call_args
        
        assert call_args.args[0] == "test-id"  # nutritionist_id
        assert call_args.args[1] == "service-123"  # service_id
        
        # Service removed from local cache
        data = await fsm_context.get_data()
        services = data.get("services", [])
        assert len(services) == 1
        assert services[0]["id"] == "service-456"
        
        # Success message shown
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "удалена" in text.lower() or "✅" in text
    
    async def test_delete_error_handling(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that delete errors are handled gracefully."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_CONFIRM_DELETE_PREFIX}service-123")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"},
            services=[{"id": "service-123", "title": "Консультация"}],
        )
        
        mock_api_client.delete_service.return_value = MagicMock(
            success=False,
            data=None,
            error="Service has active bookings",
            status_code=400,
        )
        
        with patch("handlers.services.get_api_client", return_value=mock_api_client):
            # Act
            await delete_service(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should show error
        assert "ошибка" in text.lower() or "❌" in text
        
        # Service still in cache (not deleted)
        data = await fsm_context.get_data()
        services = data.get("services", [])
        assert len(services) == 1
