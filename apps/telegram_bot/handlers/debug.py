"""
Debug Command Handler (DEV ONLY)
Enabled only when BOT_DEBUG=true environment variable is set.
Provides debugging utilities for development and QA testing.
"""

import os
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from api_client import get_api_client
from config import get_config
from keyboards import get_back_keyboard, CB_BACK_MAIN
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


logger = logging.getLogger(__name__)
router = Router(name="debug")


# Callback data constants
CB_DEBUG_RESET_STATE = "debug:reset_state"
CB_DEBUG_REFRESH = "debug:refresh"
CB_DEBUG_CHECK_BACKEND = "debug:check_backend"


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled via environment variable."""
    return os.environ.get("BOT_DEBUG", "").lower() == "true"


def get_debug_keyboard() -> InlineKeyboardMarkup:
    """Build debug menu keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🔄 Обновить данные",
            callback_data=CB_DEBUG_REFRESH,
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🗑️ Сбросить FSM состояние",
            callback_data=CB_DEBUG_RESET_STATE,
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🏥 Проверить backend",
            callback_data=CB_DEBUG_CHECK_BACKEND,
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=CB_BACK_MAIN,
        )
    )
    
    return builder.as_markup()


async def get_debug_info(message: Message, state: FSMContext) -> str:
    """Generate debug information string."""
    config = get_config()
    user = message.from_user
    
    # Get FSM state
    current_state = await state.get_state()
    state_data = await state.get_data()
    
    # Extract role from state data
    role = state_data.get("role", "unknown")
    nutritionist = state_data.get("nutritionist")
    nutritionist_id = nutritionist.get("nutritionist_id") if nutritionist else None
    verification_status = nutritionist.get("verification_status") if nutritionist else None
    
    # Resolve role from backend if not in state
    api = get_api_client()
    backend_role = "unknown"
    backend_status = "unknown"
    
    try:
        response = await api.resolve_telegram_user(user.id)
        if response.success and response.data:
            backend_role = response.data.get("role", "unknown")
            backend_status = f"✅ Connected (status={response.status_code})"
        else:
            backend_status = f"❌ Error: {response.error} (status={response.status_code})"
    except Exception as e:
        backend_status = f"❌ Exception: {str(e)}"
    
    # Determine bot mode
    bot_mode = config.mode
    if bot_mode == "webhook":
        bot_mode += f" ({config.webhook_url})"
    
    debug_text = f"""🔧 <b>Debug Info</b>

<b>👤 User:</b>
• Telegram ID: <code>{user.id}</code>
• Username: @{user.username or 'none'}
• Full Name: {user.full_name}

<b>🎭 Role:</b>
• From State: <code>{role}</code>
• From Backend: <code>{backend_role}</code>
• Nutritionist ID: <code>{nutritionist_id or 'N/A'}</code>
• Verification: <code>{verification_status or 'N/A'}</code>

<b>📊 FSM State:</b>
• Current: <code>{current_state or 'None'}</code>
• Data Keys: <code>{list(state_data.keys())}</code>

<b>🌐 Backend:</b>
• URL: <code>{config.backend_url}</code>
• Status: {backend_status}

<b>🤖 Bot Config:</b>
• Mode: <code>{bot_mode}</code>
• Log Level: <code>{config.log_level}</code>
• WebApp URL: <code>{config.webapp_url}</code>

<b>🔑 Environment:</b>
• BOT_DEBUG: <code>true</code>
• DB Connected: <code>✅</code>
"""
    
    return debug_text


@router.message(Command("debug"))
async def cmd_debug(message: Message, state: FSMContext):
    """
    Handle /debug command.
    Only available when BOT_DEBUG=true.
    Shows current role, FSM state, and system info.
    """
    if not is_debug_enabled():
        await message.answer(
            "⚠️ Debug mode отключён.\n"
            "Установите BOT_DEBUG=true для включения."
        )
        return
    
    logger.info(f"Debug command from user {message.from_user.id}")
    
    debug_text = await get_debug_info(message, state)
    
    await message.answer(
        text=debug_text,
        reply_markup=get_debug_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_DEBUG_REFRESH)
async def debug_refresh(callback: CallbackQuery, state: FSMContext):
    """Refresh debug info."""
    if not is_debug_enabled():
        await callback.answer("Debug mode отключён", show_alert=True)
        return
    
    await callback.answer("Обновляем...")
    
    debug_text = await get_debug_info(callback.message, state)
    
    await callback.message.edit_text(
        text=debug_text,
        reply_markup=get_debug_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_DEBUG_RESET_STATE)
async def debug_reset_state(callback: CallbackQuery, state: FSMContext):
    """Reset FSM state completely."""
    if not is_debug_enabled():
        await callback.answer("Debug mode отключён", show_alert=True)
        return
    
    # Store telegram_user_id before clearing
    data = await state.get_data()
    telegram_user_id = data.get("telegram_user_id", callback.from_user.id)
    
    # Clear all state
    await state.clear()
    
    # Restore only telegram_user_id
    await state.update_data(telegram_user_id=telegram_user_id)
    
    logger.info(f"FSM state reset for user {telegram_user_id}")
    
    await callback.answer("✅ FSM состояние сброшено!", show_alert=True)
    
    # Refresh debug info
    debug_text = await get_debug_info(callback.message, state)
    
    await callback.message.edit_text(
        text=debug_text,
        reply_markup=get_debug_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_DEBUG_CHECK_BACKEND)
async def debug_check_backend(callback: CallbackQuery, state: FSMContext):
    """Check backend health and connectivity."""
    if not is_debug_enabled():
        await callback.answer("Debug mode отключён", show_alert=True)
        return
    
    await callback.answer("Проверяем backend...")
    
    api = get_api_client()
    config = get_config()
    
    # Check health endpoint
    health_result = await api.health_check()
    
    # Try resolve user
    user_result = await api.resolve_telegram_user(callback.from_user.id)
    
    text = f"""🏥 <b>Backend Health Check</b>

<b>Backend URL:</b> <code>{config.backend_url}</code>

<b>Health Check (/health/db):</b>
• Status: {'✅ OK' if health_result.success else '❌ FAIL'}
• HTTP Code: <code>{health_result.status_code}</code>
• Response: <code>{health_result.data}</code>

<b>Service Token Auth:</b>
• Endpoint: /api/bot/resolve-telegram-user
• Status: {'✅ OK' if user_result.success else '❌ FAIL'}
• HTTP Code: <code>{user_result.status_code}</code>
• Error: <code>{user_result.error or 'None'}</code>

<b>User Resolution:</b>
• Role: <code>{user_result.data.get('role') if user_result.data else 'N/A'}</code>
• Has Profile: <code>{bool(user_result.data.get('profile')) if user_result.data else 'N/A'}</code>
• Is Nutritionist: <code>{bool(user_result.data.get('nutritionist')) if user_result.data else 'N/A'}</code>
"""
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_debug_keyboard(),
        parse_mode="HTML",
    )

