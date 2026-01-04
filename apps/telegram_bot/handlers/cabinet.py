"""
Personal Cabinet Handlers
Handles calendar, reviews, statistics, settings, and support.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from api_client import get_api_client
from states import SupportStates
from keyboards import (
    get_reviews_keyboard,
    get_calendar_keyboard,
    get_back_keyboard,
    get_support_keyboard,
    get_personal_cabinet_keyboard,
    CB_CALENDAR,
    CB_REVIEWS,
    CB_STATISTICS,
    CB_SETTINGS,
    CB_SUPPORT,
    CB_REVIEWS_NEXT,
    CB_REVIEWS_PREV,
    CB_PERSONAL_CABINET,
    CB_CANCEL_SUPPORT,
)


logger = logging.getLogger(__name__)
router = Router(name="cabinet")


# ==========================================
# Calendar
# ==========================================

@router.callback_query(F.data == CB_CALENDAR)
async def show_calendar(callback: CallbackQuery, state: FSMContext):
    """Show calendar connection status."""
    await callback.answer()
    
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    if not nutritionist_id:
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_back_keyboard(CB_PERSONAL_CABINET),
        )
        return
    
    # Get calendar status from backend
    api = get_api_client()
    status_response = await api.get_calendar_status(nutritionist_id)
    
    if status_response.success and status_response.data:
        is_connected = status_response.data.get("connected", False)
        calendar_email = status_response.data.get("email", "")
        
        if is_connected:
            text = (
                "📅 <b>Календарь</b>\n\n"
                f"✅ Google Calendar подключён\n"
                f"📧 {calendar_email}\n\n"
                "<b>Как это работает:</b>\n"
                "• Ваши свободные слоты определяются автоматически\n"
                "• Мы смотрим на занятые события в вашем календаре\n"
                "• Свободные промежутки становятся доступны для записи\n\n"
                "Чтобы отключить календарь, напишите в поддержку."
            )
            oauth_url = None
        else:
            # Get OAuth URL
            oauth_response = await api.get_google_oauth_url(nutritionist_id)
            oauth_url = oauth_response.data.get("url") if oauth_response.success else None
            
            text = (
                "📅 <b>Календарь</b>\n\n"
                "❌ Google Calendar не подключён\n\n"
                "<b>Зачем подключать?</b>\n"
                "• Автоматическое определение свободных слотов\n"
                "• Синхронизация записей в ваш календарь\n"
                "• Никаких накладок в расписании\n\n"
                "Нажмите кнопку ниже для подключения."
            )
    else:
        # Backend doesn't have calendar endpoint yet
        text = (
            "📅 <b>Календарь</b>\n\n"
            "⚙️ Функция в разработке\n\n"
            "Скоро здесь появится возможность:\n"
            "• Подключить Google Calendar\n"
            "• Автоматически синхронизировать расписание\n"
            "• Управлять доступными слотами"
        )
        oauth_url = None
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_calendar_keyboard(oauth_url),
        parse_mode="HTML",
    )


# ==========================================
# Reviews
# ==========================================

REVIEWS_LIMIT = 5


@router.callback_query(F.data == CB_REVIEWS)
async def show_reviews(callback: CallbackQuery, state: FSMContext):
    """Show reviews list."""
    await callback.answer()
    await fetch_and_show_reviews(callback, state, offset=0)


@router.callback_query(F.data == CB_REVIEWS_NEXT)
async def reviews_next(callback: CallbackQuery, state: FSMContext):
    """Show next page of reviews."""
    await callback.answer()
    
    data = await state.get_data()
    current_offset = data.get("reviews_offset", 0)
    
    await fetch_and_show_reviews(callback, state, offset=current_offset + REVIEWS_LIMIT)


@router.callback_query(F.data == CB_REVIEWS_PREV)
async def reviews_prev(callback: CallbackQuery, state: FSMContext):
    """Show previous page of reviews."""
    await callback.answer()
    
    data = await state.get_data()
    current_offset = data.get("reviews_offset", 0)
    new_offset = max(0, current_offset - REVIEWS_LIMIT)
    
    await fetch_and_show_reviews(callback, state, offset=new_offset)


async def fetch_and_show_reviews(callback: CallbackQuery, state: FSMContext, offset: int):
    """Fetch and display reviews."""
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    if not nutritionist_id:
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_back_keyboard(CB_PERSONAL_CABINET),
        )
        return
    
    # Fetch reviews from backend
    api = get_api_client()
    response = await api.get_reviews(nutritionist_id, limit=REVIEWS_LIMIT, offset=offset)
    
    if not response.success:
        # Backend might not have reviews endpoint yet
        text = (
            "⭐ <b>Отзывы</b>\n\n"
            "⚙️ Отзывы пока недоступны\n\n"
            "После проведения консультаций клиенты смогут оставлять отзывы.\n"
            "Они появятся здесь."
        )
        await callback.message.edit_text(
            text=text,
            reply_markup=get_back_keyboard(CB_PERSONAL_CABINET),
            parse_mode="HTML",
        )
        return
    
    reviews = response.data.get("reviews", [])
    total = response.data.get("total", 0)
    
    await state.update_data(reviews_offset=offset)
    
    if not reviews and offset == 0:
        text = (
            "⭐ <b>Отзывы</b>\n\n"
            "У вас пока нет отзывов.\n\n"
            "После проведения консультаций клиенты смогут оставлять отзывы.\n"
            "Хорошие отзывы повышают ваш рейтинг и видимость."
        )
    else:
        text = f"⭐ <b>Отзывы</b> ({offset + 1}-{min(offset + len(reviews), total)} из {total})\n\n"
        
        for review in reviews:
            rating = review.get("rating", 5)
            stars = "⭐" * rating
            client_name = review.get("client_name", "Клиент")
            comment = review.get("comment", "")
            date = review.get("created_at", "")[:10]
            
            text += f"{stars} <b>{client_name}</b>\n"
            if comment:
                text += f"<i>{comment[:100]}{'...' if len(comment) > 100 else ''}</i>\n"
            text += f"<code>{date}</code>\n\n"
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_reviews_keyboard(offset, total, REVIEWS_LIMIT),
        parse_mode="HTML",
    )


# ==========================================
# Statistics
# ==========================================

@router.callback_query(F.data == CB_STATISTICS)
async def show_statistics(callback: CallbackQuery, state: FSMContext):
    """Show nutritionist statistics."""
    await callback.answer()
    
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    if not nutritionist_id:
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_back_keyboard(CB_PERSONAL_CABINET),
        )
        return
    
    # Fetch statistics from backend
    api = get_api_client()
    response = await api.get_statistics(nutritionist_id, days=30)
    
    if response.success and response.data:
        stats = response.data
        
        income_30d = stats.get("income_30d", 0)
        consultations_30d = stats.get("consultations_30d", 0)
        avg_rating = stats.get("avg_rating", 0.0)
        total_clients = stats.get("total_clients", 0)
        
        text = (
            "📊 <b>Статистика за 30 дней</b>\n\n"
            f"💰 <b>Доход:</b> {income_30d:,}₽\n"
            f"📅 <b>Консультаций:</b> {consultations_30d}\n"
            f"⭐ <b>Средний рейтинг:</b> {avg_rating:.1f}\n"
            f"👥 <b>Всего клиентов:</b> {total_clients}\n\n"
            "<i>Статистика обновляется ежедневно</i>"
        )
    else:
        # Use dashboard data as fallback
        dashboard_response = await api.get_nutritionist_dashboard(nutritionist_id)
        
        if dashboard_response.success and dashboard_response.data:
            stats = dashboard_response.data.get("stats", {})
            
            text = (
                "📊 <b>Статистика</b>\n\n"
                f"📅 <b>Всего записей:</b> {stats.get('total_bookings', 0)}\n"
                f"✅ <b>Проведено:</b> {stats.get('completed_bookings', 0)}\n"
                f"💰 <b>Заработано:</b> {stats.get('total_earnings_rub', 0):,}₽\n\n"
                "<i>Подробная статистика скоро будет доступна</i>"
            )
        else:
            text = (
                "📊 <b>Статистика</b>\n\n"
                "Данные пока недоступны.\n"
                "Статистика появится после первых консультаций."
            )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_back_keyboard(CB_PERSONAL_CABINET),
        parse_mode="HTML",
    )


# ==========================================
# Settings
# ==========================================

@router.callback_query(F.data == CB_SETTINGS)
async def show_settings(callback: CallbackQuery, state: FSMContext):
    """Show settings (cancellation policy)."""
    await callback.answer()
    
    text = (
        "⚙️ <b>Настройки</b>\n\n"
        "<b>📋 Политика отмены бронирования</b>\n\n"
        "Для всех консультаций действуют единые правила:\n\n"
        "• <b>За 24+ часа до консультации:</b>\n"
        "  Полный возврат средств клиенту\n\n"
        "• <b>Менее чем за 24 часа:</b>\n"
        "  Возврат 50% стоимости\n\n"
        "• <b>Неявка клиента:</b>\n"
        "  Без возврата (вы получаете оплату)\n\n"
        "• <b>Ваша отмена:</b>\n"
        "  Полный возврат клиенту\n"
        "  При частых отменах — снижение рейтинга\n\n"
        "<i>Эти условия установлены платформой и не изменяются.</i>"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_back_keyboard(CB_PERSONAL_CABINET),
        parse_mode="HTML",
    )


# ==========================================
# Support
# ==========================================

@router.callback_query(F.data == CB_SUPPORT)
async def start_support(callback: CallbackQuery, state: FSMContext):
    """Start support message flow."""
    await callback.answer()
    
    await state.set_state(SupportStates.waiting_message)
    
    await callback.message.edit_text(
        text=(
            "💬 <b>Поддержка</b>\n\n"
            "Опишите вашу проблему или вопрос.\n"
            "Мы ответим в течение 24 часов.\n\n"
            "Отправьте сообщение:"
        ),
        reply_markup=get_support_keyboard(),
        parse_mode="HTML",
    )


@router.message(SupportStates.waiting_message)
async def process_support_message(message: Message, state: FSMContext):
    """Process and send support message."""
    text = message.text.strip() if message.text else ""
    
    if not text:
        await message.answer(
            "⚠️ Отправьте текстовое сообщение.",
            reply_markup=get_support_keyboard(),
        )
        return
    
    if len(text) > 1000:
        await message.answer(
            "⚠️ Сообщение слишком длинное. Максимум 1000 символов.",
            reply_markup=get_support_keyboard(),
        )
        return
    
    data = await state.get_data()
    telegram_user_id = data.get("telegram_user_id", message.from_user.id)
    
    # Send to backend
    api = get_api_client()
    response = await api.send_support_message(
        telegram_user_id=telegram_user_id,
        message=text,
    )
    
    await state.set_state(None)
    
    if response.success:
        await message.answer(
            text=(
                "✅ <b>Сообщение отправлено!</b>\n\n"
                "Спасибо за обращение.\n"
                "Мы ответим вам в ближайшее время."
            ),
            reply_markup=get_personal_cabinet_keyboard(),
            parse_mode="HTML",
        )
    else:
        # Log the message even if backend call failed
        logger.warning(
            f"Support message from user {telegram_user_id}: {text}"
        )
        
        await message.answer(
            text=(
                "✅ <b>Сообщение получено!</b>\n\n"
                "Мы свяжемся с вами в ближайшее время."
            ),
            reply_markup=get_personal_cabinet_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data == CB_CANCEL_SUPPORT, SupportStates.waiting_message)
async def cancel_support(callback: CallbackQuery, state: FSMContext):
    """Cancel support message."""
    await callback.answer("Отменено")
    await state.set_state(None)
    
    await callback.message.edit_text(
        text="❌ Обращение в поддержку отменено.",
        reply_markup=get_personal_cabinet_keyboard(),
    )

