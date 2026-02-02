"""
Schedule Handlers
Handles availability slot management and bookings view for nutritionists.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from api_client import get_api_client
from states import SlotStates
from bot_texts import MOSCOW_TIME_NOTE
from timezone_utils import MOSCOW_TZ, now_moscow, to_moscow
from keyboards import (
    get_schedule_keyboard,
    get_slot_date_keyboard,
    get_slot_duration_keyboard,
    get_confirm_slot_keyboard,
    get_delete_slot_keyboard,
    get_bookings_keyboard,
    get_back_keyboard,
    get_personal_cabinet_keyboard,
    CB_SCHEDULE,
    CB_ADD_SLOT,
    CB_DELETE_SLOT,
    CB_REFRESH_SCHEDULE,
    CB_SLOT_DATE_PREFIX,
    CB_SLOT_DURATION_PREFIX,
    CB_CONFIRM_SLOT,
    CB_CANCEL_SLOT,
    CB_SELECT_SLOT_DELETE_PREFIX,
    CB_MY_BOOKINGS,
    CB_REFRESH_BOOKINGS,
    CB_BOOKINGS_NEXT,
    CB_BOOKINGS_PREV,
    CB_PERSONAL_CABINET,
    CB_WORKING_HOURS,
    CB_EXCEPTIONS,
)


logger = logging.getLogger(__name__)
router = Router(name="schedule")


# Russian month names (genitive case for dates)
MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}

WEEKDAYS_RU = {
    0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс",
}


def format_date_ru(dt: datetime) -> str:
    """Format date in Russian: '15 января'."""
    return f"{dt.day} {MONTHS_RU[dt.month]}"


def format_date_short_ru(dt: datetime) -> str:
    """Format date in short Russian: '15 янв (Пн)'."""
    month_short = MONTHS_RU[dt.month][:3]
    weekday = WEEKDAYS_RU[dt.weekday()]
    return f"{dt.day} {month_short} ({weekday})"


def format_time_range(start_at: datetime, end_at: datetime) -> str:
    """Format time range: '12:00–13:00'."""
    return f"{start_at.strftime('%H:%M')}–{end_at.strftime('%H:%M')}"


def get_next_14_days() -> list[dict]:
    """Get list of next 14 days for date selection."""
    dates = []
    today = now_moscow().date()
    
    for i in range(14):
        date = today + timedelta(days=i)
        dt = datetime.combine(date, datetime.min.time())
        dates.append({
            "date": date.isoformat(),
            "label": format_date_short_ru(dt),
        })
    
    return dates


def group_slots_by_date(slots: list[dict]) -> dict[str, list[dict]]:
    """Group slots by date for display."""
    grouped = {}
    
    for slot in slots:
        start_at = datetime.fromisoformat(slot["start_at"].replace('Z', '+00:00'))
        end_at = datetime.fromisoformat(slot["end_at"].replace('Z', '+00:00'))
        start_local = to_moscow(start_at)
        end_local = to_moscow(end_at)
        date_key = start_local.date().isoformat()
        
        if date_key not in grouped:
            grouped[date_key] = []
        
        grouped[date_key].append({
            **slot,
            "start_dt": start_local,
            "end_dt": end_local,
        })
    
    # Sort slots within each date
    for date_key in grouped:
        grouped[date_key].sort(key=lambda s: s["start_dt"])
    
    return grouped


def time_to_minutes(time_str: str) -> int:
    """Convert HH:MM to minutes."""
    hours, minutes = time_str.split(":")
    return int(hours) * 60 + int(minutes)


def format_working_hours_summary(weekly_schedule: dict) -> str:
    """Format weekly schedule into a short summary."""
    if not weekly_schedule:
        return ""

    parts = []
    for day_num in range(7):
        ranges = weekly_schedule.get(str(day_num)) or weekly_schedule.get(day_num) or []
        if not ranges:
            continue
        ranges_sorted = sorted(ranges, key=lambda r: time_to_minutes(r["start"]))
        ranges_text = ", ".join([f"{r['start']}–{r['end']}" for r in ranges_sorted])
        parts.append(f"{WEEKDAYS_RU[day_num]} {ranges_text}")

    if not parts:
        return ""

    return f"🕐 Обычные часы: {'; '.join(parts)}"


# ==========================================
# Schedule View
# ==========================================

@router.callback_query(F.data == CB_SCHEDULE)
async def show_schedule(callback: CallbackQuery, state: FSMContext):
    """Show schedule with availability slots."""
    await callback.answer()
    await state.set_state(None)  # Clear any FSM state
    
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    if not nutritionist_id:
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_back_keyboard(CB_PERSONAL_CABINET),
        )
        return
    
    # Fetch slots
    api = get_api_client()
    response = await api.get_slots(nutritionist_id)

    # Fetch working hours summary
    summary_text = ""
    working_hours_response = await api.get_working_hours_template(nutritionist_id)
    if working_hours_response.success:
        template = working_hours_response.data.get("template", {})
        weekly_schedule = template.get("weekly_schedule", {})
        summary_text = format_working_hours_summary(weekly_schedule)
    
    if not response.success:
        text = "🕒 <b>Расписание</b>\n\n"
        if summary_text:
            text += f"{summary_text}\n\n"
        text += (
            "⚠️ Не удалось загрузить расписание.\n"
            "Попробуйте позже."
        )
        await callback.message.edit_text(
            text=text,
            reply_markup=get_schedule_keyboard(has_free_slots=False),
            parse_mode="HTML",
        )
        return
    
    slots = response.data.get("slots", [])
    
    if not slots:
        text = "🕒 <b>Расписание</b>\n\n"
        if summary_text:
            text += f"{summary_text}\n\n"
        text += (
            "У вас пока нет доступных слотов.\n\n"
            "Добавьте слоты, чтобы клиенты могли записаться на консультацию.\n\n"
            "<i>💡 Совет: добавьте несколько слотов на ближайшие дни, "
            "чтобы увеличить шансы на запись.</i>"
        )
        await callback.message.edit_text(
            text=text,
            reply_markup=get_schedule_keyboard(has_free_slots=False),
            parse_mode="HTML",
        )
        return
    
    # Group slots by date
    grouped = group_slots_by_date(slots)
    
    # Build text
    text = "🕒 <b>Расписание</b> (ближайшие 14 дней)\n\n"
    if summary_text:
        text += f"{summary_text}\n\n"
    
    has_free_slots = False
    
    for date_key in sorted(grouped.keys()):
        date_slots = grouped[date_key]
        date_dt = datetime.fromisoformat(date_key)
        
        text += f"📅 <b>{format_date_ru(date_dt)}</b>\n"
        
        for slot in date_slots:
            time_range = format_time_range(slot["start_dt"], slot["end_dt"])
            status = slot.get("status", "free")
            
            if status == "free":
                status_text = "свободно"
                has_free_slots = True
            elif status == "held":
                status_text = "удерживается"
            elif status == "booked":
                status_text = "забронировано"
            else:
                status_text = status
            
            text += f"  • {time_range} ({status_text})\n"
        
        text += "\n"
    
    # Check calendar connection status
    calendar_response = await api.get_calendar_status(nutritionist_id)
    if calendar_response.success and calendar_response.data.get("connected"):
        text += "📅 <i>Google Calendar подключён</i>\n"

    text += MOSCOW_TIME_NOTE
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_schedule_keyboard(has_free_slots=has_free_slots),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_REFRESH_SCHEDULE)
async def refresh_schedule(callback: CallbackQuery, state: FSMContext):
    """Refresh schedule view."""
    await show_schedule(callback, state)


# ==========================================
# Add Slot Flow (FSM)
# ==========================================

@router.callback_query(F.data == CB_ADD_SLOT)
async def start_add_slot(callback: CallbackQuery, state: FSMContext):
    """Start add slot wizard - ask for date."""
    await callback.answer()
    
    dates = get_next_14_days()
    
    await state.set_state(SlotStates.selecting_date)
    await state.update_data(slot_dates=dates)
    
    text = (
        "➕ <b>Добавить слот</b>\n\n"
        "Выберите дату для нового слота:"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_slot_date_keyboard(dates),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith(CB_SLOT_DATE_PREFIX), SlotStates.selecting_date)
async def select_slot_date(callback: CallbackQuery, state: FSMContext):
    """Handle date selection, ask for start time."""
    await callback.answer()
    
    date_str = callback.data.replace(CB_SLOT_DATE_PREFIX, "")
    
    await state.update_data(slot_date=date_str)
    await state.set_state(SlotStates.waiting_start_time)
    
    # Format date for display
    date_dt = datetime.fromisoformat(date_str)
    date_label = format_date_ru(date_dt)
    
    text = (
        f"➕ <b>Добавить слот</b>\n\n"
        f"📅 Дата: {date_label}\n\n"
        f"Введите время начала в формате <b>ЧЧ:ММ</b>\n"
        f"(например: 10:00, 14:30)"
    )
    text += MOSCOW_TIME_NOTE
    
    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
    )


@router.message(SlotStates.waiting_start_time)
async def process_start_time(message: Message, state: FSMContext):
    """Process start time input, ask for duration."""
    time_text = message.text.strip() if message.text else ""
    
    # Validate time format (HH:MM)
    time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')
    match = time_pattern.match(time_text)
    
    if not match:
        await message.answer(
            "⚠️ Неверный формат времени.\n\n"
            "Введите время в формате <b>ЧЧ:ММ</b> (например: 10:00, 14:30)"
            + MOSCOW_TIME_NOTE,
            parse_mode="HTML",
        )
        return
    
    hours, minutes = int(match.group(1)), int(match.group(2))
    
    data = await state.get_data()
    date_str = data.get("slot_date")
    
    # Check if time is in the future
    date_dt = datetime.fromisoformat(date_str)
    slot_start_local = datetime.combine(
        date_dt.date(),
        datetime.strptime(f"{hours:02d}:{minutes:02d}", "%H:%M").time(),
    ).replace(tzinfo=MOSCOW_TZ)
    slot_start = slot_start_local.astimezone(timezone.utc)
    
    now_local = now_moscow()
    if slot_start_local <= now_local:
        await message.answer(
            "⚠️ Время слота должно быть в будущем.\n\n"
            "Введите другое время:"
            + MOSCOW_TIME_NOTE,
            parse_mode="HTML",
        )
        return
    
    await state.update_data(
        slot_start_time=f"{hours:02d}:{minutes:02d}",
        slot_start_dt=slot_start.isoformat(),
    )
    await state.set_state(SlotStates.selecting_duration)
    
    date_label = format_date_ru(date_dt)
    
    text = (
        f"➕ <b>Добавить слот</b>\n\n"
        f"📅 Дата: {date_label}\n"
        f"🕒 Начало: {hours:02d}:{minutes:02d}\n\n"
        f"Выберите продолжительность:"
    )
    text += MOSCOW_TIME_NOTE
    
    await message.answer(
        text=text,
        reply_markup=get_slot_duration_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith(CB_SLOT_DURATION_PREFIX), SlotStates.selecting_duration)
async def select_slot_duration(callback: CallbackQuery, state: FSMContext):
    """Handle duration selection, show confirmation."""
    await callback.answer()
    
    duration_str = callback.data.replace(CB_SLOT_DURATION_PREFIX, "")
    duration_minutes = int(duration_str)
    
    data = await state.get_data()
    slot_start_dt = datetime.fromisoformat(data.get("slot_start_dt"))
    slot_end_dt = slot_start_dt + timedelta(minutes=duration_minutes)
    
    await state.update_data(
        slot_duration=duration_minutes,
        slot_end_dt=slot_end_dt.isoformat(),
    )
    await state.set_state(SlotStates.confirming_slot)
    
    start_local = to_moscow(slot_start_dt)
    end_local = to_moscow(slot_end_dt)
    date_label = format_date_ru(start_local)
    time_range = format_time_range(start_local, end_local)
    
    text = (
        f"➕ <b>Добавить слот</b>\n\n"
        f"Подтвердите создание слота:\n\n"
        f"📅 {date_label}\n"
        f"🕒 {time_range}\n"
        f"⏱ {duration_minutes} минут\n\n"
        f"Всё верно?"
    )
    text += MOSCOW_TIME_NOTE
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_confirm_slot_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_CONFIRM_SLOT, SlotStates.confirming_slot)
async def confirm_slot_creation(callback: CallbackQuery, state: FSMContext):
    """Create slot via API."""
    await callback.answer()
    
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    if not nutritionist_id:
        await state.set_state(None)
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_personal_cabinet_keyboard(),
        )
        return
    
    start_at = data.get("slot_start_dt")
    end_at = data.get("slot_end_dt")
    
    # Create slot via API
    api = get_api_client()
    response = await api.create_slot(nutritionist_id, start_at, end_at)
    
    await state.set_state(None)
    
    if response.success:
        slot_start_dt = datetime.fromisoformat(start_at)
        slot_end_dt = datetime.fromisoformat(end_at)
        start_local = to_moscow(slot_start_dt)
        end_local = to_moscow(slot_end_dt)
        date_label = format_date_ru(start_local)
        time_range = format_time_range(start_local, end_local)
        
        text = (
            f"✅ <b>Слот создан!</b>\n\n"
            f"📅 {date_label}\n"
            f"🕒 {time_range}\n\n"
            f"Клиенты теперь могут записаться на это время."
        )
        text += MOSCOW_TIME_NOTE
        await callback.message.edit_text(
            text=text,
            reply_markup=get_schedule_keyboard(has_free_slots=True),
            parse_mode="HTML",
        )
    else:
        error = response.error or "Неизвестная ошибка"
        
        # Handle specific errors
        if "пересекается" in error.lower() or response.status_code == 409:
            error = "Этот слот пересекается с существующим. Выберите другое время."
        elif "будущем" in error.lower():
            error = "Слот должен быть в будущем."
        
        text = (
            f"❌ <b>Не удалось создать слот</b>\n\n"
            f"{error}\n\n"
            f"Попробуйте ещё раз."
        )
        await callback.message.edit_text(
            text=text,
            reply_markup=get_schedule_keyboard(has_free_slots=False),
            parse_mode="HTML",
        )


@router.callback_query(F.data == CB_CANCEL_SLOT)
async def cancel_slot_creation(callback: CallbackQuery, state: FSMContext):
    """Cancel slot creation and return to schedule."""
    await callback.answer("Отменено")
    await state.set_state(None)
    await show_schedule(callback, state)


# ==========================================
# Delete Slot Flow
# ==========================================

@router.callback_query(F.data == CB_DELETE_SLOT)
async def start_delete_slot(callback: CallbackQuery, state: FSMContext):
    """Show list of free slots to delete."""
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
    
    # Fetch only free slots
    api = get_api_client()
    response = await api.get_slots(nutritionist_id)
    
    if not response.success:
        await callback.message.edit_text(
            text="⚠️ Не удалось загрузить слоты.",
            reply_markup=get_schedule_keyboard(has_free_slots=False),
            parse_mode="HTML",
        )
        return
    
    slots = response.data.get("slots", [])
    free_slots = [s for s in slots if s.get("status") == "free"]
    
    if not free_slots:
        text = (
            "❌ <b>Удаление слота</b>\n\n"
            "Нет свободных слотов для удаления.\n\n"
            "<i>Удалить можно только свободные слоты. "
            "Забронированные слоты удалить нельзя.</i>"
        )
        await callback.message.edit_text(
            text=text,
            reply_markup=get_schedule_keyboard(has_free_slots=False),
            parse_mode="HTML",
        )
        return
    
    # Build slot list for selection
    slot_options = []
    for slot in free_slots:
        start_dt = datetime.fromisoformat(slot["start_at"].replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(slot["end_at"].replace('Z', '+00:00'))
        start_local = to_moscow(start_dt)
        end_local = to_moscow(end_dt)
        
        date_label = format_date_short_ru(start_local)
        time_range = format_time_range(start_local, end_local)
        
        slot_options.append({
            "id": slot["id"],
            "label": f"{date_label}, {time_range}",
        })
    
    await state.set_state(SlotStates.selecting_slot_to_delete)
    
    text = (
        "❌ <b>Удаление слота</b>\n\n"
        "Выберите слот для удаления:"
    )
    text += MOSCOW_TIME_NOTE
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_delete_slot_keyboard(slot_options),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith(CB_SELECT_SLOT_DELETE_PREFIX), SlotStates.selecting_slot_to_delete)
async def confirm_delete_slot(callback: CallbackQuery, state: FSMContext):
    """Delete the selected slot."""
    await callback.answer()
    
    slot_id = callback.data.replace(CB_SELECT_SLOT_DELETE_PREFIX, "")
    
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    if not nutritionist_id:
        await state.set_state(None)
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_personal_cabinet_keyboard(),
        )
        return
    
    # Delete slot via API
    api = get_api_client()
    response = await api.delete_slot(nutritionist_id, slot_id)
    
    await state.set_state(None)
    
    if response.success:
        text = "✅ <b>Слот удалён!</b>"
        await callback.message.edit_text(
            text=text,
            reply_markup=get_schedule_keyboard(has_free_slots=True),
            parse_mode="HTML",
        )
    else:
        error = response.error or "Неизвестная ошибка"
        
        # Handle specific errors
        if "используется" in error.lower() or response.status_code == 400:
            error = "Этот слот уже забронирован и не может быть удалён."
        
        text = (
            f"❌ <b>Не удалось удалить слот</b>\n\n"
            f"{error}"
        )
        await callback.message.edit_text(
            text=text,
            reply_markup=get_schedule_keyboard(has_free_slots=True),
            parse_mode="HTML",
        )


# ==========================================
# Bookings View
# ==========================================

BOOKINGS_LIMIT = 10


@router.callback_query(F.data == CB_MY_BOOKINGS)
async def show_bookings(callback: CallbackQuery, state: FSMContext):
    """Show nutritionist's bookings."""
    await callback.answer()
    await state.set_state(None)
    
    await fetch_and_show_bookings(callback, state, offset=0)


@router.callback_query(F.data == CB_REFRESH_BOOKINGS)
async def refresh_bookings(callback: CallbackQuery, state: FSMContext):
    """Refresh bookings view."""
    await callback.answer()
    
    data = await state.get_data()
    offset = data.get("bookings_offset", 0)
    
    await fetch_and_show_bookings(callback, state, offset=offset)


@router.callback_query(F.data == CB_BOOKINGS_NEXT)
async def bookings_next(callback: CallbackQuery, state: FSMContext):
    """Show next page of bookings."""
    await callback.answer()
    
    data = await state.get_data()
    current_offset = data.get("bookings_offset", 0)
    
    await fetch_and_show_bookings(callback, state, offset=current_offset + BOOKINGS_LIMIT)


@router.callback_query(F.data == CB_BOOKINGS_PREV)
async def bookings_prev(callback: CallbackQuery, state: FSMContext):
    """Show previous page of bookings."""
    await callback.answer()
    
    data = await state.get_data()
    current_offset = data.get("bookings_offset", 0)
    new_offset = max(0, current_offset - BOOKINGS_LIMIT)
    
    await fetch_and_show_bookings(callback, state, offset=new_offset)


async def fetch_and_show_bookings(callback: CallbackQuery, state: FSMContext, offset: int):
    """Fetch and display bookings."""
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    if not nutritionist_id:
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_back_keyboard(CB_PERSONAL_CABINET),
        )
        return
    
    # Fetch bookings
    api = get_api_client()
    response = await api.get_nutritionist_bookings(
        nutritionist_id,
        limit=BOOKINGS_LIMIT,
        offset=offset,
    )
    
    if not response.success:
        text = (
            "📋 <b>Мои бронирования</b>\n\n"
            "⚠️ Не удалось загрузить бронирования.\n"
            "Попробуйте позже."
        )
        await callback.message.edit_text(
            text=text,
            reply_markup=get_bookings_keyboard(offset, 0, BOOKINGS_LIMIT),
            parse_mode="HTML",
        )
        return
    
    bookings = response.data.get("bookings", [])
    total = response.data.get("total", 0)
    
    await state.update_data(bookings_offset=offset)
    
    if not bookings and offset == 0:
        text = (
            "📋 <b>Мои бронирования</b>\n\n"
            "Пока нет предстоящих бронирований.\n\n"
            "<i>Когда клиенты запишутся на консультацию, "
            "их записи появятся здесь.</i>"
        )
        await callback.message.edit_text(
            text=text,
            reply_markup=get_bookings_keyboard(offset, total, BOOKINGS_LIMIT),
            parse_mode="HTML",
        )
        return
    
    # Build bookings text
    if total > BOOKINGS_LIMIT:
        text = f"📋 <b>Мои бронирования</b> ({offset + 1}-{min(offset + len(bookings), total)} из {total})\n\n"
    else:
        text = "📋 <b>Мои бронирования</b>\n\n"
    
    for booking in bookings:
        start_at = datetime.fromisoformat(booking["start_at"].replace('Z', '+00:00'))
        end_at = datetime.fromisoformat(booking["end_at"].replace('Z', '+00:00'))
        start_local = to_moscow(start_at)
        end_local = to_moscow(end_at)
        
        date_label = format_date_ru(start_local)
        time_range = format_time_range(start_local, end_local)
        
        client_name = booking.get("client_name", "Клиент")
        service_title = booking.get("service_title", "Консультация")
        status = booking.get("status", "paid")
        
        # Status emoji
        if status == "paid":
            status_text = "✅ Подтверждено"
        elif status == "completed":
            status_text = "☑️ Завершено"
        else:
            status_text = status
        
        text += (
            f"📅 {date_label}, {time_range}\n"
            f"👤 {client_name}\n"
            f"💼 {service_title}\n"
            f"{status_text}\n\n"
        )
    
    await callback.message.edit_text(
        text=text + MOSCOW_TIME_NOTE,
        reply_markup=get_bookings_keyboard(offset, total, BOOKINGS_LIMIT),
        parse_mode="HTML",
    )
