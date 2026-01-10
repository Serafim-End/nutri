"""
Start Command Handler
Handles /start command and initial user resolution.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from api_client import get_api_client
from keyboards import get_main_menu_keyboard


logger = logging.getLogger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Handle /start command.
    Resolves user role and shows main menu.
    """
    user = message.from_user
    telegram_user_id = user.id
    
    logger.info(f"User started bot: telegram_id={telegram_user_id}, username={user.username}")
    
    # Clear any existing FSM state
    await state.clear()
    
    # Resolve user via backend
    api = get_api_client()
    response = await api.resolve_telegram_user(
        telegram_user_id,
        full_name=user.full_name,
        telegram_username=user.username,
    )
    
    # Determine greeting based on user data
    user_name = user.first_name or "Пользователь"
    role = "client"
    
    if response.success and response.data:
        profile = response.data.get("profile", {})
        if profile:
            user_name = profile.get("full_name", user_name)
            role = profile.get("role", "client")
    
    # Store user info in FSM data for later use
    await state.update_data(
        telegram_user_id=telegram_user_id,
        role=role,
        profile=response.data.get("profile") if response.success else None,
        nutritionist=response.data.get("nutritionist") if response.success else None,
    )
    
    # Build welcome message
    welcome_text = (
        f"👋 Привет, {user_name}!\n\n"
        "Добро пожаловать в NutriMatch.\n"
        "Это бот‑помощник для клиентов и нутрициологов.\n\n"
    )
    
    if role == "nutritionist":
        welcome_text += (
            "🩺 Вы зарегистрированы как нутрициолог.\n"
            "Если вы здесь впервые, нажмите «Для нутрициологов» и следуйте шагам.\n\n"
        )
    elif role == "admin":
        welcome_text += "👑 Вы администратор.\n\n"
    
    welcome_text += "Выберите действие ниже:"
    
    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu_keyboard(),
    )
