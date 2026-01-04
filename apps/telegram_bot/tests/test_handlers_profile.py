"""
Unit tests for profile creation/update flow.
Tests FSM state transitions and validation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from handlers.profile import (
    start_profile_flow,
    process_full_name,
    process_bio,
    toggle_specialization,
    submit_profile,
    SPECIALIZATIONS,
)
from states import ProfileStates
from keyboards import CB_CREATE_PROFILE, CB_SPEC_PREFIX, CB_SUBMIT_PROFILE
from tests.conftest import create_message, create_callback_query


pytestmark = pytest.mark.asyncio


class TestProfileFlowStart:
    """Tests for starting profile flow."""
    
    async def test_starts_with_name_prompt(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that profile flow starts with name prompt."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_CREATE_PROFILE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.update_data(nutritionist={})
        
        # Act
        await start_profile_flow(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        # Check step indicator
        assert "Шаг 1" in text
        assert "6" in text  # Step X of 6
        
        # Check prompt for name
        assert "имя" in text.lower()
        
        # Check FSM state
        state = await fsm_context.get_state()
        assert state == ProfileStates.waiting_full_name.state


class TestFullNameValidation:
    """Tests for full name input validation."""
    
    async def test_valid_name_proceeds(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that valid name proceeds to photo step."""
        # Arrange
        message = create_message(test_user, test_chat, text="Иван Петров")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.waiting_full_name)
        await fsm_context.update_data(profile_draft={"full_name": "Old Name"})
        
        # Act
        await process_full_name(message, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ProfileStates.waiting_photo.state
        
        data = await fsm_context.get_data()
        assert data["profile_draft"]["full_name"] == "Иван Петров"
    
    async def test_too_short_name_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that too short name shows error."""
        # Arrange
        message = create_message(test_user, test_chat, text="А")
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.waiting_full_name)
        await fsm_context.update_data(profile_draft={})
        
        # Act
        await process_full_name(message, fsm_context)
        
        # Assert - stays in same state
        state = await fsm_context.get_state()
        assert state == ProfileStates.waiting_full_name.state
        
        # Error message shown
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "коротк" in text.lower()
    
    async def test_too_long_name_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that too long name shows error."""
        # Arrange
        long_name = "А" * 101
        message = create_message(test_user, test_chat, text=long_name)
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.waiting_full_name)
        await fsm_context.update_data(profile_draft={})
        
        # Act
        await process_full_name(message, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ProfileStates.waiting_full_name.state
        
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "длинн" in text.lower()


class TestBioValidation:
    """Tests for bio input validation."""
    
    async def test_valid_bio_proceeds(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that valid bio proceeds to specializations."""
        # Arrange
        bio_text = "Опытный нутрициолог с 5-летним стажем."
        message = create_message(test_user, test_chat, text=bio_text)
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.waiting_bio)
        await fsm_context.update_data(profile_draft={})
        
        # Act
        await process_bio(message, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ProfileStates.selecting_specializations.state
        
        data = await fsm_context.get_data()
        assert data["profile_draft"]["bio"] == bio_text
    
    async def test_bio_over_300_chars_error(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that bio over 300 characters shows error."""
        # Arrange
        long_bio = "А" * 301
        message = create_message(test_user, test_chat, text=long_bio)
        message.answer = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.waiting_bio)
        await fsm_context.update_data(profile_draft={})
        
        # Act
        await process_bio(message, fsm_context)
        
        # Assert - stays in same state
        state = await fsm_context.get_state()
        assert state == ProfileStates.waiting_bio.state
        
        call_args = message.answer.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        assert "длинн" in text.lower() or "300" in text


class TestSpecializationSelection:
    """Tests for specialization multi-select."""
    
    async def test_toggle_adds_specialization(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that toggling adds specialization to list."""
        # Arrange
        spec_id = SPECIALIZATIONS[0]["id"]  # e.g., "weight_management"
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_SPEC_PREFIX}{spec_id}")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.selecting_specializations)
        await fsm_context.update_data(profile_draft={"specializations": []})
        
        # Act
        await toggle_specialization(callback, fsm_context)
        
        # Assert
        data = await fsm_context.get_data()
        assert spec_id in data["profile_draft"]["specializations"]
    
    async def test_toggle_removes_specialization(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that toggling again removes specialization."""
        # Arrange
        spec_id = SPECIALIZATIONS[0]["id"]
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_SPEC_PREFIX}{spec_id}")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.selecting_specializations)
        await fsm_context.update_data(profile_draft={"specializations": [spec_id]})
        
        # Act
        await toggle_specialization(callback, fsm_context)
        
        # Assert
        data = await fsm_context.get_data()
        assert spec_id not in data["profile_draft"]["specializations"]
    
    async def test_updates_counter_in_message(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that selection counter is updated."""
        # Arrange
        spec_id = SPECIALIZATIONS[0]["id"]
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_SPEC_PREFIX}{spec_id}")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.selecting_specializations)
        await fsm_context.update_data(profile_draft={"specializations": []})
        
        # Act
        await toggle_specialization(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        assert "Выбрано: 1" in text


class TestProfileSubmission:
    """Tests for profile submission."""
    
    async def test_successful_submission(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that profile is submitted successfully."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_SUBMIT_PROFILE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.confirming_submission)
        await fsm_context.update_data(
            telegram_user_id=test_user.id,
            profile_draft={
                "full_name": "Тест Нутрициолог",
                "bio": "Описание",
                "specializations": ["weight_management"],
                "tags": [],
            },
        )
        
        with patch("handlers.profile.get_api_client", return_value=mock_api_client):
            # Act
            await submit_profile(callback, fsm_context)
        
        # Assert
        mock_api_client.upsert_nutritionist.assert_called_once()
        call_args = mock_api_client.upsert_nutritionist.call_args
        
        assert call_args.kwargs["submit_for_verification"] == True
        assert call_args.kwargs["full_name"] == "Тест Нутрициолог"
        assert "weight_management" in call_args.kwargs["specializations"]
    
    async def test_submission_clears_state(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that FSM state is cleared after submission."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_SUBMIT_PROFILE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.confirming_submission)
        await fsm_context.update_data(
            telegram_user_id=test_user.id,
            profile_draft={
                "full_name": "Тест",
                "specializations": ["weight_management"],
            },
        )
        
        with patch("handlers.profile.get_api_client", return_value=mock_api_client):
            # Act
            await submit_profile(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state is None
        
        data = await fsm_context.get_data()
        assert data.get("profile_draft") is None
    
    async def test_submission_shows_confirmation(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that success message is shown in Russian."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_SUBMIT_PROFILE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.confirming_submission)
        await fsm_context.update_data(
            telegram_user_id=test_user.id,
            profile_draft={
                "full_name": "Тест",
                "specializations": ["weight_management"],
            },
        )
        
        with patch("handlers.profile.get_api_client", return_value=mock_api_client):
            # Act
            await submit_profile(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        assert "модерац" in text.lower()
        assert "24" in text or "48" in text  # Review time mentioned

