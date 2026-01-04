"""
Pytest configuration and fixtures for bot tests.
Uses aiogram test utilities and mocked backend.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.types import User, Chat, Message, CallbackQuery, Update
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage


# =========================================
# Event Loop Configuration
# =========================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =========================================
# Bot and Dispatcher Fixtures
# =========================================

@pytest.fixture
def bot():
    """Create mock bot instance."""
    bot = AsyncMock(spec=Bot)
    bot.id = 123456789
    bot.get_me = AsyncMock(return_value=MagicMock(
        id=123456789,
        username="test_bot",
        first_name="Test Bot",
    ))
    return bot


@pytest.fixture
def storage():
    """Create in-memory FSM storage."""
    return MemoryStorage()


@pytest.fixture
def dp(storage):
    """Create dispatcher with memory storage."""
    return Dispatcher(storage=storage)


# =========================================
# User and Chat Fixtures
# =========================================

@pytest.fixture
def test_user() -> User:
    """Create test Telegram user."""
    return User(
        id=111111111,
        is_bot=False,
        first_name="Тест",
        last_name="Пользователь",
        username="test_user",
        language_code="ru",
    )


@pytest.fixture
def test_nutritionist_user() -> User:
    """Create test nutritionist user."""
    return User(
        id=222222222,
        is_bot=False,
        first_name="Тест",
        last_name="Нутрициолог",
        username="test_nutritionist",
        language_code="ru",
    )


@pytest.fixture
def test_chat(test_user: User) -> Chat:
    """Create test chat."""
    return Chat(
        id=test_user.id,
        type="private",
        first_name=test_user.first_name,
        username=test_user.username,
    )


# =========================================
# Message and CallbackQuery Factories
# =========================================

def create_message(
    user: User,
    chat: Chat,
    text: str = None,
    photo: list = None,
    document: dict = None,
    message_id: int = 1,
) -> Message:
    """Factory to create test messages."""
    return Message(
        message_id=message_id,
        date=0,
        chat=chat,
        from_user=user,
        text=text,
        photo=photo,
        document=document,
    )


def create_callback_query(
    user: User,
    message: Message,
    data: str,
    callback_query_id: str = "test_callback",
) -> CallbackQuery:
    """Factory to create test callback queries."""
    return CallbackQuery(
        id=callback_query_id,
        from_user=user,
        chat_instance="test_instance",
        message=message,
        data=data,
    )


@pytest.fixture
def message_factory(test_user, test_chat):
    """Fixture returning message factory function."""
    def _factory(text: str = None, **kwargs):
        return create_message(test_user, test_chat, text=text, **kwargs)
    return _factory


@pytest.fixture
def callback_factory(test_user, test_chat):
    """Fixture returning callback factory function."""
    def _factory(data: str, message: Message = None):
        if message is None:
            message = create_message(test_user, test_chat, text="Previous message")
        return create_callback_query(test_user, message, data)
    return _factory


# =========================================
# FSM State Fixture
# =========================================

@pytest.fixture
async def fsm_context(storage, test_user, test_chat):
    """Create FSM context for testing."""
    from aiogram.fsm.storage.base import StorageKey
    
    key = StorageKey(
        bot_id=123456789,
        chat_id=test_chat.id,
        user_id=test_user.id,
    )
    
    return FSMContext(storage=storage, key=key)


# =========================================
# Mock API Client
# =========================================

@pytest.fixture
def mock_api_client():
    """Create mocked API client with default responses."""
    client = AsyncMock()
    
    # Default responses
    client.resolve_telegram_user.return_value = MagicMock(
        success=True,
        data={
            "profile": None,
            "nutritionist": None,
            "role": "client",
        },
        error=None,
        status_code=200,
    )
    
    client.upsert_nutritionist.return_value = MagicMock(
        success=True,
        data={
            "nutritionist": {
                "nutritionist_id": "test-nutritionist-id",
                "verification_status": "draft",
                "profile": {
                    "full_name": "Test Nutritionist",
                },
            },
            "is_new": True,
        },
        error=None,
        status_code=200,
    )
    
    client.list_services.return_value = MagicMock(
        success=True,
        data={"services": []},
        error=None,
        status_code=200,
    )
    
    client.create_service.return_value = MagicMock(
        success=True,
        data={
            "service": {
                "id": "test-service-id",
                "title": "Test Service",
                "price_rub": 3000,
                "duration_minutes": 60,
                "is_active": True,
            }
        },
        error=None,
        status_code=201,
    )
    
    client.get_nutritionist_dashboard.return_value = MagicMock(
        success=True,
        data={
            "nutritionist": {
                "nutritionist_id": "test-nutritionist-id",
                "verification_status": "approved",
            },
            "services": [],
            "stats": {
                "total_bookings": 0,
                "completed_bookings": 0,
                "total_earnings_rub": 0,
            },
        },
        error=None,
        status_code=200,
    )
    
    client.health_check.return_value = MagicMock(
        success=True,
        data={"status": "ok"},
        error=None,
        status_code=200,
    )
    
    return client


@pytest.fixture
def patch_api_client(mock_api_client):
    """Patch get_api_client to return mock."""
    with patch("api_client.get_api_client", return_value=mock_api_client):
        yield mock_api_client


# =========================================
# Config Mock
# =========================================

@pytest.fixture
def mock_config():
    """Create mock config."""
    config = MagicMock()
    config.bot_token = "test_token"
    config.backend_url = "http://localhost:5000"
    config.service_token = "test_service_token"
    config.webapp_url = "https://t.me/test_bot/app"
    config.mode = "polling"
    config.log_level = "INFO"
    return config


@pytest.fixture
def patch_config(mock_config):
    """Patch get_config to return mock."""
    with patch("config.get_config", return_value=mock_config):
        yield mock_config

