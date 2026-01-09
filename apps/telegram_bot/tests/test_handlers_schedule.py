"""
Unit tests for schedule and slot management handlers.
Tests add slot flow, delete slot flow, and schedule view.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

from handlers.schedule import (
    show_schedule,
    start_add_slot,
    select_slot_date,
    process_start_time,
    select_slot_duration,
    confirm_slot_creation,
    start_delete_slot,
    confirm_delete_slot,
)
from states import SlotStates
from keyboards import (
    CB_SCHEDULE,
    CB_ADD_SLOT,
    CB_DELETE_SLOT,
    CB_SLOT_DATE_PREFIX,
    CB_SLOT_DURATION_PREFIX,
    CB_CONFIRM_SLOT,
    CB_CANCEL_SLOT,
    CB_SELECT_SLOT_DELETE_PREFIX,
)
from tests.conftest import create_message, create_callback_query


pytestmark = pytest.mark.asyncio


class TestScheduleView:
    """Tests for schedule view."""
    
    async def test_shows_empty_schedule(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that empty schedule shows appropriate message."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_SCHEDULE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        mock_api_client.get_slots.return_value = MagicMock(
            success=True,
            data={"slots": []},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.schedule.get_api_client", return_value=mock_api_client):
            # Act
            await show_schedule(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        assert "нет доступных слотов" in text.lower() or "пока нет" in text.lower()
    
    async def test_shows_slots_grouped_by_date(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that slots are grouped by date."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_SCHEDULE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        day_after = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        
        mock_api_client.get_slots.return_value = MagicMock(
            success=True,
            data={
                "slots": [
                    {
                        "id": "1",
                        "start_at": tomorrow,
                        "end_at": (datetime.fromisoformat(tomorrow.replace('Z', '+00:00')) + timedelta(hours=1)).isoformat(),
                        "status": "free",
                    },
                    {
                        "id": "2",
                        "start_at": day_after,
                        "end_at": (datetime.fromisoformat(day_after.replace('Z', '+00:00')) + timedelta(hours=1)).isoformat(),
                        "status": "booked",
                    },
                ]
            },
            error=None,
            status_code=200,
        )
        
        with patch("handlers.schedule.get_api_client", return_value=mock_api_client):
            # Act
            await show_schedule(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Should show dates
        assert "Расписание" in text
        # Should show slot statuses
        assert "свободно" in text.lower() or "забронировано" in text.lower()
    
    async def test_clears_fsm_state(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that schedule view clears FSM state."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_SCHEDULE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(SlotStates.selecting_date)
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        mock_api_client.get_slots.return_value = MagicMock(
            success=True,
            data={"slots": []},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.schedule.get_api_client", return_value=mock_api_client):
            # Act
            await show_schedule(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state is None


class TestAddSlotFlow:
    """Tests for add slot flow (FSM)."""
    
    async def test_starts_with_date_selection(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that add slot flow starts with date selection."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_ADD_SLOT)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        # Act
        await start_add_slot(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == SlotStates.selecting_date.state
        
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        assert "Выберите дату" in text or "дату" in text.lower()
    
    async def test_date_selection_proceeds_to_time(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that date selection proceeds to time input."""
        # Arrange
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_SLOT_DATE_PREFIX}{tomorrow}")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(SlotStates.selecting_date)
        await fsm_context.update_data(slot_dates=[])
        
        # Act
        await select_slot_date(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == SlotStates.waiting_start_time.state
        
        data = await fsm_context.get_data()
        assert data.get("slot_date") == tomorrow
    
    async def test_valid_time_proceeds_to_duration(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that valid time input proceeds to duration selection."""
        # Arrange
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
        message = create_message(test_user, test_chat, text="14:30")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(SlotStates.waiting_start_time)
        await fsm_context.update_data(slot_date=tomorrow)
        
        # Act
        await process_start_time(message, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == SlotStates.selecting_duration.state
        
        data = await fsm_context.get_data()
        assert data.get("slot_start_time") == "14:30"
    
    async def test_invalid_time_format_shows_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that invalid time format shows error."""
        # Arrange
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
        message = create_message(test_user, test_chat, text="25:00")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(SlotStates.waiting_start_time)
        await fsm_context.update_data(slot_date=tomorrow)
        
        # Act
        await process_start_time(message, fsm_context)
        
        # Assert - stays in same state
        state = await fsm_context.get_state()
        assert state == SlotStates.waiting_start_time.state
        
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "формат" in text.lower() or "неверн" in text.lower()
    
    async def test_past_time_shows_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that past time shows error."""
        # Arrange
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
        message = create_message(test_user, test_chat, text="10:00")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(SlotStates.waiting_start_time)
        await fsm_context.update_data(slot_date=yesterday)
        
        # Act
        await process_start_time(message, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == SlotStates.waiting_start_time.state
        
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "будущем" in text.lower() or "прошл" in text.lower()
    
    async def test_duration_selection_proceeds_to_confirmation(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that duration selection proceeds to confirmation."""
        # Arrange
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        tomorrow_iso = tomorrow.isoformat()
        
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_SLOT_DURATION_PREFIX}60")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(SlotStates.selecting_duration)
        await fsm_context.update_data(
            slot_date=tomorrow.date().isoformat(),
            slot_start_time="14:30",
            slot_start_dt=tomorrow_iso,
        )
        
        # Act
        await select_slot_duration(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == SlotStates.confirming_slot.state
        
        data = await fsm_context.get_data()
        assert data.get("slot_duration") == 60
    
    async def test_slot_creation_success(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that slot is created successfully."""
        # Arrange
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        start_dt = tomorrow.replace(hour=14, minute=30, second=0, microsecond=0)
        end_dt = start_dt + timedelta(minutes=60)
        
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_CONFIRM_SLOT)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(SlotStates.confirming_slot)
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"},
            slot_start_dt=start_dt.isoformat(),
            slot_end_dt=end_dt.isoformat(),
        )
        
        mock_api_client.create_slot.return_value = MagicMock(
            success=True,
            data={"slot": {"id": "new-slot-id"}},
            error=None,
            status_code=201,
        )
        
        with patch("handlers.schedule.get_api_client", return_value=mock_api_client):
            # Act
            await confirm_slot_creation(callback, fsm_context)
        
        # Assert
        mock_api_client.create_slot.assert_called_once()
        call_args = mock_api_client.create_slot.call_args
        
        assert call_args.args[0] == "test-id"  # nutritionist_id
        assert call_args.args[1] == start_dt.isoformat()  # start_at
        assert call_args.args[2] == end_dt.isoformat()  # end_at
        
        # State cleared
        state = await fsm_context.get_state()
        assert state is None
        
        # Success message shown
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "создан" in text.lower() or "✅" in text
    
    async def test_slot_creation_clears_state(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that FSM state is cleared after slot creation."""
        # Arrange
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        start_dt = tomorrow.replace(hour=14, minute=30, second=0, microsecond=0)
        end_dt = start_dt + timedelta(minutes=60)
        
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_CONFIRM_SLOT)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(SlotStates.confirming_slot)
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"},
            slot_start_dt=start_dt.isoformat(),
            slot_end_dt=end_dt.isoformat(),
        )
        
        mock_api_client.create_slot.return_value = MagicMock(
            success=True,
            data={"slot": {"id": "new-slot-id"}},
            error=None,
            status_code=201,
        )
        
        with patch("handlers.schedule.get_api_client", return_value=mock_api_client):
            # Act
            await confirm_slot_creation(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state is None


class TestDeleteSlotFlow:
    """Tests for delete slot flow."""
    
    async def test_shows_free_slots_for_deletion(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that delete flow shows only free slots."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_DELETE_SLOT)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        
        mock_api_client.get_slots.return_value = MagicMock(
            success=True,
            data={
                "slots": [
                    {
                        "id": "free-slot-1",
                        "start_at": tomorrow,
                        "end_at": (datetime.fromisoformat(tomorrow.replace('Z', '+00:00')) + timedelta(hours=1)).isoformat(),
                        "status": "free",
                    },
                    {
                        "id": "booked-slot-1",
                        "start_at": tomorrow,
                        "end_at": (datetime.fromisoformat(tomorrow.replace('Z', '+00:00')) + timedelta(hours=1)).isoformat(),
                        "status": "booked",
                    },
                ]
            },
            error=None,
            status_code=200,
        )
        
        with patch("handlers.schedule.get_api_client", return_value=mock_api_client):
            # Act
            await start_delete_slot(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        reply_markup = call_args.kwargs.get("reply_markup")
        
        # Should only show free slot
        buttons = []
        for row in reply_markup.inline_keyboard:
            for btn in row:
                buttons.append(btn.callback_data)
        
        # Should have delete button for free slot
        assert any("free-slot-1" in cb for cb in buttons)
        # Should NOT have delete button for booked slot
        assert not any("booked-slot-1" in cb for cb in buttons)
    
    async def test_no_free_slots_shows_message(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that no free slots shows appropriate message."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_DELETE_SLOT)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        mock_api_client.get_slots.return_value = MagicMock(
            success=True,
            data={"slots": []},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.schedule.get_api_client", return_value=mock_api_client):
            # Act
            await start_delete_slot(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        assert "нет свободных слотов" in text.lower() or "нельзя" in text.lower()
    
    async def test_slot_deletion_success(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that slot is deleted successfully."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_SELECT_SLOT_DELETE_PREFIX}slot-123")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(SlotStates.selecting_slot_to_delete)
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"}
        )
        
        mock_api_client.delete_slot.return_value = MagicMock(
            success=True,
            data={},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.schedule.get_api_client", return_value=mock_api_client):
            # Act
            await confirm_delete_slot(callback, fsm_context)
        
        # Assert
        mock_api_client.delete_slot.assert_called_once()
        call_args = mock_api_client.delete_slot.call_args
        
        assert call_args.args[0] == "test-id"  # nutritionist_id
        assert call_args.args[1] == "slot-123"  # slot_id
        
        # State cleared
        state = await fsm_context.get_state()
        assert state is None
        
        # Success message shown
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "удалён" in text.lower() or "✅" in text
