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
    get_calendar_select_keyboard,
    get_back_keyboard,
    get_support_keyboard,
    get_personal_cabinet_keyboard,
    CB_CALENDAR,
    CB_CALENDAR_REFRESH,
    CB_CALENDAR_SELECT,
    CB_CALENDAR_PICK_PREFIX,
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
    
    calendars = []
    can_select_calendar = False
    selected_calendar_summary = None
    selected_calendar_id = None
    is_connected = False

    if status_response.success and status_response.data:
        is_connected = status_response.data.get("connected", False)
        calendar_email = status_response.data.get("email", "")
        selected_calendar_id = status_response.data.get("selected_calendar_id")
        selected_calendar_summary = status_response.data.get("selected_calendar_summary")
        await state.update_data(selected_calendar_id=selected_calendar_id)
        
        if is_connected:
            calendars_response = await api.list_calendars(nutritionist_id)
            if calendars_response.success and calendars_response.data:
                calendars = calendars_response.data.get("calendars", [])
                can_select_calendar = len(calendars) > 1
                await state.update_data(calendar_options=calendars)
            text = (
                "📅 <b>Календарь</b>\n\n"
                "✅ Google Calendar подключён\n"
                f"📧 {calendar_email}\n"
                f"📌 {selected_calendar_summary or 'Календарь не выбран'}\n\n"
                "<b>Что это даёт:</b>\n"
                "• Клиенты не смогут записаться на занятые интервалы\n"
                "• Новые записи можно синхронизировать с календарём\n\n"
                "<b>Дальше:</b>\n"
                "• Нажмите «Выбрать календарь», если у вас их несколько\n"
                "• Нажмите «Проверить подключение», если только что подключили\n\n"
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
                "• Чтобы клиенты не записывались на занятое время\n"
                "• Чтобы ваши записи попадали в календарь автоматически\n\n"
                "<b>Как подключить:</b>\n"
                "1️⃣ Нажмите кнопку «Подключить Google Calendar»\n"
                "2️⃣ Разрешите доступ в Google\n"
                "3️⃣ Вернитесь сюда и нажмите «Проверить подключение»\n\n"
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
        reply_markup=get_calendar_keyboard(
            oauth_url,
            is_connected=is_connected,
            can_select_calendar=can_select_calendar,
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_CALENDAR_REFRESH)
async def refresh_calendar(callback: CallbackQuery, state: FSMContext):
    await show_calendar(callback, state)


@router.callback_query(F.data == CB_CALENDAR_SELECT)
async def select_calendar_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    calendars = data.get("calendar_options", [])
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")

    if not nutritionist_id:
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_back_keyboard(CB_PERSONAL_CABINET),
        )
        return

    if not calendars:
        api = get_api_client()
        calendars_response = await api.list_calendars(nutritionist_id)
        if calendars_response.success and calendars_response.data:
            calendars = calendars_response.data.get("calendars", [])
            await state.update_data(calendar_options=calendars)

    if not calendars:
        await callback.message.edit_text(
            text="❌ Нет доступных календарей для выбора.",
            reply_markup=get_back_keyboard(CB_CALENDAR),
        )
        return

    selected_id = data.get("selected_calendar_id")
    await callback.message.edit_text(
        text="📌 Выберите календарь для синхронизации:",
        reply_markup=get_calendar_select_keyboard(calendars, selected_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith(CB_CALENDAR_PICK_PREFIX))
async def pick_calendar(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    calendars = data.get("calendar_options", [])
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")

    if not nutritionist_id:
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_back_keyboard(CB_PERSONAL_CABINET),
        )
        return

    try:
        index_str = callback.data.split(CB_CALENDAR_PICK_PREFIX, 1)[1]
        idx = int(index_str)
    except (IndexError, ValueError):
        await callback.message.edit_text(
            text="❌ Неверный выбор календаря.",
            reply_markup=get_back_keyboard(CB_CALENDAR),
        )
        return

    if idx < 0 or idx >= len(calendars):
        await callback.message.edit_text(
            text="❌ Неверный выбор календаря.",
            reply_markup=get_back_keyboard(CB_CALENDAR),
        )
        return

    calendar_id = calendars[idx].get("id")
    if not calendar_id:
        await callback.message.edit_text(
            text="❌ Неверный выбор календаря.",
            reply_markup=get_back_keyboard(CB_CALENDAR),
        )
        return

    api = get_api_client()
    select_response = await api.select_calendar(nutritionist_id, calendar_id)
    if select_response.success:
        await state.update_data(selected_calendar_id=calendar_id)
        await callback.message.edit_text(
            text="✅ Календарь выбран. Теперь он используется для синхронизации.",
            reply_markup=get_back_keyboard(CB_CALENDAR),
        )
        return

    await callback.message.edit_text(
        text="❌ Не удалось выбрать календарь. Попробуйте позже.",
        reply_markup=get_back_keyboard(CB_CALENDAR),
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
