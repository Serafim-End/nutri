"""
Menu Navigation Handlers
Handles main menu navigation and nutritionist menu.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from api_client import get_api_client
from keyboards import (
    get_main_menu_keyboard,
    get_nutritionist_menu_keyboard,
    get_personal_cabinet_keyboard,
    CB_FOR_NUTRITIONISTS,
    CB_I_AM_NUTRITIONIST,
    CB_BACK_MAIN,
    CB_BACK_NUTRITIONIST,
    CB_PERSONAL_CABINET,
)


logger = logging.getLogger(__name__)
router = Router(name="menu")


@router.callback_query(F.data == CB_FOR_NUTRITIONISTS)
async def handle_for_nutritionists(callback: CallbackQuery, state: FSMContext):
    """Show nutritionist menu."""
    await callback.answer()
    
    # Get user data to check if they have a profile
    data = await state.get_data()
    nutritionist = data.get("nutritionist")
    has_profile = nutritionist is not None
    
    text = (
        "👩‍⚕️ <b>Раздел для нутрициологов</b>\n\n"
    )
    
    if has_profile:
        status = nutritionist.get("verification_status", "draft")
        status_map = {
            "draft": "📝 Черновик",
            "pending": "⏳ На модерации",
            "approved": "✅ Подтверждён",
            "rejected": "❌ Отклонён",
            "needs_update": "⚠️ Требуются изменения",
        }
        status_text = status_map.get(status, status)
        
        text += (
            f"Ваш профиль: {status_text}\n\n"
            "Выберите действие:"
        )
    else:
        text += (
            "Здесь вы можете создать профиль нутрициолога, "
            "управлять своими услугами и отслеживать статистику.\n\n"
            "Выберите действие:"
        )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_nutritionist_menu_keyboard(has_profile),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_I_AM_NUTRITIONIST)
async def handle_i_am_nutritionist(callback: CallbackQuery, state: FSMContext):
    """
    Handle 'I am nutritionist' button.
    Registers user intent and suggests creating profile.
    """
    await callback.answer()
    
    # Get user data
    data = await state.get_data()
    telegram_user_id = data.get("telegram_user_id", callback.from_user.id)
    
    # Update role intent via backend
    api = get_api_client()
    response = await api.upsert_nutritionist(
        telegram_user_id=telegram_user_id,
        full_name=callback.from_user.full_name,
        submit_for_verification=False,
    )
    
    if response.success and response.data:
        nutritionist = response.data.get("nutritionist")
        await state.update_data(nutritionist=nutritionist, role="nutritionist")
    
    text = (
        "✨ <b>Отлично!</b>\n\n"
        "Вы отметили, что являетесь нутрициологом.\n\n"
        "Чтобы начать принимать клиентов, необходимо:\n"
        "1️⃣ Заполнить профиль\n"
        "2️⃣ Добавить услуги\n"
        "3️⃣ Подключить календарь\n"
        "4️⃣ Пройти модерацию\n\n"
        "Начнём с создания профиля?"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_nutritionist_menu_keyboard(has_profile=True),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_PERSONAL_CABINET)
async def handle_personal_cabinet(callback: CallbackQuery, state: FSMContext):
    """Show personal cabinet."""
    await callback.answer()
    
    # Get fresh data from backend
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id") if nutritionist else None
    
    if not nutritionist_id:
        await callback.message.edit_text(
            text="❌ Профиль нутрициолога не найден.\nСначала создайте профиль.",
            reply_markup=get_nutritionist_menu_keyboard(has_profile=False),
        )
        return
    
    # Get dashboard data
    api = get_api_client()
    response = await api.get_nutritionist_dashboard(nutritionist_id)
    
    if not response.success:
        text = (
            "🏠 <b>Личный кабинет</b>\n\n"
            "Не удалось загрузить данные.\n"
            "Попробуйте позже."
        )
    else:
        dashboard = response.data
        stats = dashboard.get("stats", {})
        profile = nutritionist.get("profile", {})
        
        total_bookings = stats.get("total_bookings", 0)
        completed = stats.get("completed_bookings", 0)
        earnings = stats.get("total_earnings_rub", 0)
        
        text = (
            f"🏠 <b>Личный кабинет</b>\n\n"
            f"👤 {profile.get('full_name', 'Нутрициолог')}\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Всего записей: {total_bookings}\n"
            f"• Проведено: {completed}\n"
            f"• Заработано: {earnings:,}₽\n\n"
            "Выберите раздел:"
        )
        
        # Update state with fresh data
        await state.update_data(
            nutritionist=dashboard.get("nutritionist"),
            services=dashboard.get("services", []),
        )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_personal_cabinet_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_BACK_MAIN)
async def handle_back_main(callback: CallbackQuery, state: FSMContext):
    """Go back to main menu."""
    await callback.answer()
    
    data = await state.get_data()
    role = data.get("role", "client")
    
    welcome_text = (
        "👋 NutriMatch — сервис подбора нутрициологов\n\n"
    )
    
    if role == "nutritionist":
        welcome_text += "🩺 Вы зарегистрированы как нутрициолог.\n\n"
    
    welcome_text += "Выберите действие:"
    
    await callback.message.edit_text(
        text=welcome_text,
        reply_markup=get_main_menu_keyboard(),
    )


@router.callback_query(F.data == CB_BACK_NUTRITIONIST)
async def handle_back_nutritionist(callback: CallbackQuery, state: FSMContext):
    """Go back to nutritionist menu."""
    await callback.answer()
    
    data = await state.get_data()
    nutritionist = data.get("nutritionist")
    has_profile = nutritionist is not None
    
    text = "👩‍⚕️ <b>Раздел для нутрициологов</b>\n\n"
    
    if has_profile:
        status = nutritionist.get("verification_status", "draft")
        status_map = {
            "draft": "📝 Черновик",
            "pending": "⏳ На модерации",
            "approved": "✅ Подтверждён",
            "rejected": "❌ Отклонён",
            "needs_update": "⚠️ Требуются изменения",
        }
        text += f"Статус профиля: {status_map.get(status, status)}\n\n"
    
    text += "Выберите действие:"
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_nutritionist_menu_keyboard(has_profile),
        parse_mode="HTML",
    )

