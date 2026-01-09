"""
Extended unit tests for profile creation flow.
Tests photo skip, tags selection, rules confirmation, and cancel flow.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from handlers.profile import (
    skip_photo,
    process_photo,
    skip_bio,
    tags_done,
    confirm_rules,
    cancel_profile,
    TAGS,
)
from states import ProfileStates
from keyboards import (
    CB_SKIP_PHOTO,
    CB_SKIP_BIO,
    CB_SKIP_TAGS,
    CB_TAG_PREFIX,
    CB_TAG_DONE,
    CB_CONFIRM_RULES,
    CB_CANCEL_PROFILE,
)
from tests.conftest import create_message, create_callback_query


pytestmark = pytest.mark.asyncio


class TestPhotoStep:
    """Tests for photo upload step."""
    
    async def test_skip_photo_proceeds_to_bio(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that skipping photo proceeds to bio step."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_SKIP_PHOTO)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.waiting_photo)
        await fsm_context.update_data(profile_draft={"full_name": "Test"})
        
        # Act
        await skip_photo(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ProfileStates.waiting_bio.state
    
    async def test_photo_upload_proceeds_to_bio(
        self,
        test_user,
        test_chat,
        fsm_context,
        mock_api_client,
    ):
        """Test that photo upload proceeds to bio step."""
        # Arrange
        photo = MagicMock()
        photo.file_id = "photo123"
        photo_list = [photo]
        
        message = create_message(test_user, test_chat, photo=photo_list)
        message.answer = AsyncMock()
        
        bot = AsyncMock()
        bot.get_file = AsyncMock(return_value=MagicMock(file_path="photos/file.jpg"))
        bot.download_file = AsyncMock(return_value=MagicMock(read=lambda: b"fake_image_data"))
        
        await fsm_context.set_state(ProfileStates.waiting_photo)
        await fsm_context.update_data(
            nutritionist={"nutritionist_id": "test-id"},
            profile_draft={"full_name": "Test"},
        )
        
        mock_api_client.upload_photo.return_value = MagicMock(
            success=True,
            data={"photo_url": "https://example.com/photo.jpg"},
            error=None,
            status_code=200,
        )
        
        with patch("handlers.profile.get_api_client", return_value=mock_api_client):
            # Act
            await process_photo(message, fsm_context, bot)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ProfileStates.waiting_bio.state
        
        data = await fsm_context.get_data()
        assert data["profile_draft"].get("photo_url") == "https://example.com/photo.jpg"


class TestTagsStep:
    """Tests for tags selection step."""
    
    async def test_toggle_adds_tag(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that toggling adds tag to list."""
        # Arrange
        tag_id = TAGS[0]["id"]  # e.g., "vegetarian"
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_TAG_PREFIX}{tag_id}")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.selecting_tags)
        await fsm_context.update_data(profile_draft={"tags": []})
        
        # Act
        from handlers.profile import toggle_tag
        await toggle_tag(callback, fsm_context)
        
        # Assert
        data = await fsm_context.get_data()
        assert tag_id in data["profile_draft"]["tags"]
    
    async def test_toggle_removes_tag(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that toggling again removes tag."""
        # Arrange
        tag_id = TAGS[0]["id"]
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, f"{CB_TAG_PREFIX}{tag_id}")
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.selecting_tags)
        await fsm_context.update_data(profile_draft={"tags": [tag_id]})
        
        # Act
        from handlers.profile import toggle_tag
        await toggle_tag(callback, fsm_context)
        
        # Assert
        data = await fsm_context.get_data()
        assert tag_id not in data["profile_draft"]["tags"]
    
    async def test_skip_tags_proceeds_to_rules(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that skipping tags proceeds to rules confirmation."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_SKIP_TAGS)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.selecting_tags)
        await fsm_context.update_data(profile_draft={})
        
        # Act
        await tags_done(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ProfileStates.confirming_rules.state
    
    async def test_tags_done_proceeds_to_rules(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that tags done proceeds to rules confirmation."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_TAG_DONE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.selecting_tags)
        await fsm_context.update_data(profile_draft={"tags": ["vegetarian"]})
        
        # Act
        await tags_done(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ProfileStates.confirming_rules.state


class TestRulesConfirmation:
    """Tests for rules confirmation step."""
    
    async def test_confirm_rules_proceeds_to_submission(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that confirming rules proceeds to final confirmation."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_CONFIRM_RULES)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.confirming_rules)
        await fsm_context.update_data(
            profile_draft={
                "full_name": "Тест Нутрициолог",
                "bio": "Описание",
                "specializations": ["weight_management"],
                "tags": [],
            }
        )
        
        # Act
        await confirm_rules(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state == ProfileStates.confirming_submission.state
        
        # Should show summary
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        assert "Проверка" in text or "Шаг 6" in text
        assert "Тест Нутрициолог" in text
        assert "weight_management" in text.lower() or "Управление весом" in text


class TestCancelProfile:
    """Tests for profile creation cancellation."""
    
    async def test_cancel_clears_state(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that cancel clears FSM state."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_CANCEL_PROFILE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.waiting_bio)
        await fsm_context.update_data(
            profile_draft={"full_name": "Test"},
            nutritionist={"nutritionist_id": "test-id"},
        )
        
        # Act
        await cancel_profile(callback, fsm_context)
        
        # Assert
        state = await fsm_context.get_state()
        assert state is None
        
        data = await fsm_context.get_data()
        assert data.get("profile_draft") is None
        # Nutritionist data should remain
        assert data.get("nutritionist") is not None
    
    async def test_cancel_shows_message(
        self,
        test_user,
        test_chat,
        fsm_context,
    ):
        """Test that cancel shows cancellation message."""
        # Arrange
        message = create_message(test_user, test_chat, text="Previous")
        callback = create_callback_query(test_user, message, CB_CANCEL_PROFILE)
        callback.answer = AsyncMock()
        callback.message.edit_text = AsyncMock()
        
        await fsm_context.set_state(ProfileStates.waiting_bio)
        await fsm_context.update_data(nutritionist={"nutritionist_id": "test-id"})
        
        # Act
        await cancel_profile(callback, fsm_context)
        
        # Assert
        call_args = callback.message.edit_text.call_args
        text = call_args.kwargs.get("text") or call_args.args[0]
        
        assert "отменено" in text.lower() or "❌" in text
