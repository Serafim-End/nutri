"""
Date Exceptions Handlers
Handles date exceptions (off days / custom hours) for nutritionists.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from api_client import get_api_client
from states import DateExceptionStates
from keyboards import (
    get_exceptions_keyboard,
    get_exception_date_keyboard,
    get_exception_type_keyboard,
    get_confirm_exception_keyboard,
    get_delete_exception_keyboard,
    get_back_keyboard,
    CB_EXCEPTIONS,
    CB_ADD_EXCEPTION,
    CB_DELETE_EXCEPTION,
    CB_EXCEPTION_DATE_PREFIX,
    CB_EXCEPTION_TYPE_OFF,
    CB_EXCEPTION_TYPE_CUSTOM,
    CB_EXCEPTION_DELETE_PREFIX,
    CB_CANCEL_EXCEPTION,
    CB_CONFIRM_EXCEPTION,
    CB_SCHEDULE,
)
from bot_texts import (
    EXCEPTIONS_TITLE,
    EXCEPTIONS_INSTRUCTION,
    EXCEPTIONS_LIST_TITLE,
    EXCEPTIONS_EMPTY,
    EXCEPTIONS_ITEM_OFF,
    EXCEPTIONS_ITEM_CUSTOM,
    EXCEPTIONS_ADD_DATE,
    EXCEPTIONS_SELECT_TYPE,
    EXCEPTIONS_TYPE_OFF,
    EXCEPTIONS_TYPE_CUSTOM,
    EXCEPTIONS_CUSTOM_START_TIME,
    EXCEPTIONS_CUSTOM_END_TIME,
    EXCEPTIONS_CONFIRM_OFF,
    EXCEPTIONS_CONFIRM_CUSTOM,
    EXCEPTIONS_CREATED_OFF,
    EXCEPTIONS_CREATED_CUSTOM,
    EXCEPTIONS_ERROR,
    EXCEPTIONS_ALREADY_EXISTS,
    EXCEPTIONS_DELETE_TITLE,
    EXCEPTIONS_DELETE_SELECT,
    EXCEPTIONS_DELETED,
    MONTHS_RU,
    WEEKDAYS_RU,
)


logger = logging.getLogger(__name__)
router = Router(name="exceptions")


def format_date_short_ru(dt: datetime) -> str:
    """Format date in short Russian: '15 янв (Пн)'."""
    month_short = MONTHS_RU[dt.month][:3]
    weekday = WEEKDAYS_RU[dt.weekday()]
    return f"{dt.day} {month_short} ({weekday})"


def format_date_ru(dt: datetime) -> str:
    """Format date in Russian: '15 января'."""
    return f"{dt.day} {MONTHS_RU[dt.month]}"


def format_time_range(start: str, end: str) -> str:
    """Format time range: '09:00–12:00'."""
    return f"{start}–{end}"


def format_time_ranges_list(ranges: list[dict]) -> str:
    """Format list of time ranges."""
    if not ranges:
        return ""
    return ", ".join([format_time_range(r['start'], r['end']) for r in ranges])


def get_next_30_days() -> list[dict]:
    """Get list of next 30 days for date selection."""
    dates = []
    today = datetime.now(timezone.utc).date()
    
    for i in range(30):
        date = today + timedelta(days=i)
        dt = datetime.combine(date, datetime.min.time())
        dates.append({
            "date": date.isoformat(),
            "label": format_date_short_ru(dt),
        })
    
    return dates


@router.callback_query(F.data == CB_EXCEPTIONS)
async def show_exceptions(callback: CallbackQuery, state: FSMContext):
    """Show date exceptions list."""
    await callback.answer()
    await state.set_state(None)
    
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    if not nutritionist_id:
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_back_keyboard(CB_SCHEDULE),
        )
        return
    
    # Fetch exceptions
    api = get_api_client()
    response = await api.list_date_exceptions(nutritionist_id)
    
    if not response.success:
        text = EXCEPTIONS_TITLE + EXCEPTIONS_INSTRUCTION
        await callback.message.edit_text(
            text=text,
            reply_markup=get_exceptions_keyboard(has_exceptions=False),
            parse_mode="HTML",
        )
        return
    
    exceptions = response.data.get("exceptions", [])
    
    if not exceptions:
        text = EXCEPTIONS_LIST_TITLE + EXCEPTIONS_EMPTY
        await callback.message.edit_text(
            text=text,
            reply_markup=get_exceptions_keyboard(has_exceptions=False),
            parse_mode="HTML",
        )
        return
    
    # Build exceptions list
    text = EXCEPTIONS_LIST_TITLE
    
    for exc in exceptions:
        exc_date = datetime.fromisoformat(exc["exception_date"]).date()
        date_label = format_date_ru(datetime.combine(exc_date, datetime.min.time()))
        exc_type = exc.get("exception_type", "off")
        
        if exc_type == "off":
            text += EXCEPTIONS_ITEM_OFF.format(date=date_label) + "\n"
        else:
            custom_hours = exc.get("custom_hours", [])
            if custom_hours:
                time_ranges = format_time_ranges_list(custom_hours)
                text += EXCEPTIONS_ITEM_CUSTOM.format(
                    date=date_label,
                    time_ranges=time_ranges,
                ) + "\n"
            else:
                text += EXCEPTIONS_ITEM_CUSTOM.format(
                    date=date_label,
                    time_ranges="Особые часы",
                ) + "\n"
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_exceptions_keyboard(has_exceptions=True),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_ADD_EXCEPTION)
async def start_add_exception(callback: CallbackQuery, state: FSMContext):
    """Start adding exception - ask for date."""
    await callback.answer()
    
    dates = get_next_30_days()
    
    await state.set_state(DateExceptionStates.selecting_date)
    await state.update_data(exception_dates=dates)
    
    text = EXCEPTIONS_TITLE + EXCEPTIONS_ADD_DATE
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_exception_date_keyboard(dates),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith(CB_EXCEPTION_DATE_PREFIX), DateExceptionStates.selecting_date)
async def select_exception_date(callback: CallbackQuery, state: FSMContext):
    """Handle date selection, ask for exception type."""
    await callback.answer()
    
    date_str = callback.data.replace(CB_EXCEPTION_DATE_PREFIX, "")
    
    # Format date for display
    date_dt = datetime.fromisoformat(date_str)
    date_label = format_date_ru(date_dt)
    
    await state.update_data(exception_date=date_str)
    await state.set_state(DateExceptionStates.selecting_type)
    
    text = EXCEPTIONS_TITLE + EXCEPTIONS_SELECT_TYPE.format(date=date_label)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_exception_type_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_EXCEPTION_TYPE_OFF, DateExceptionStates.selecting_type)
async def select_type_off(callback: CallbackQuery, state: FSMContext):
    """Handle 'off' type selection, show confirmation."""
    await callback.answer()
    
    data = await state.get_data()
    date_str = data.get("exception_date")
    date_dt = datetime.fromisoformat(date_str)
    date_label = format_date_ru(date_dt)
    
    await state.update_data(exception_type="off")
    await state.set_state(DateExceptionStates.confirming_exception)
    
    text = EXCEPTIONS_TITLE + EXCEPTIONS_CONFIRM_OFF.format(date=date_label)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_confirm_exception_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_EXCEPTION_TYPE_CUSTOM, DateExceptionStates.selecting_type)
async def select_type_custom(callback: CallbackQuery, state: FSMContext):
    """Handle 'custom' type selection, ask for start time."""
    await callback.answer()
    
    data = await state.get_data()
    date_str = data.get("exception_date")
    date_dt = datetime.fromisoformat(date_str)
    date_label = format_date_ru(date_dt)
    
    await state.update_data(exception_type="custom")
    await state.set_state(DateExceptionStates.waiting_custom_start_time)
    
    text = EXCEPTIONS_TITLE + EXCEPTIONS_CUSTOM_START_TIME.format(date=date_label)
    
    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
    )


@router.message(DateExceptionStates.waiting_custom_start_time)
async def process_custom_start_time(message: Message, state: FSMContext):
    """Process custom start time, ask for end time."""
    time_text = message.text.strip() if message.text else ""
    
    # Validate time format
    time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')
    match = time_pattern.match(time_text)
    
    if not match:
        await message.answer(
            "⚠️ Неверный формат времени.\n\n"
            "Введите время в формате <b>ЧЧ:ММ</b> (например: 10:00)",
            parse_mode="HTML",
        )
        return
    
    hours, minutes = int(match.group(1)), int(match.group(2))
    start_time = f"{hours:02d}:{minutes:02d}"
    
    data = await state.get_data()
    date_str = data.get("exception_date")
    date_dt = datetime.fromisoformat(date_str)
    date_label = format_date_ru(date_dt)
    
    await state.update_data(exception_custom_start_time=start_time)
    await state.set_state(DateExceptionStates.waiting_custom_end_time)
    
    text = EXCEPTIONS_TITLE + EXCEPTIONS_CUSTOM_END_TIME.format(
        date=date_label,
        start_time=start_time,
    )
    
    await message.answer(
        text=text,
        parse_mode="HTML",
    )


@router.message(DateExceptionStates.waiting_custom_end_time)
async def process_custom_end_time(message: Message, state: FSMContext):
    """Process custom end time, show confirmation."""
    time_text = message.text.strip() if message.text else ""
    
    # Validate time format
    time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')
    match = time_pattern.match(time_text)
    
    if not match:
        await message.answer(
            "⚠️ Неверный формат времени.\n\n"
            "Введите время в формате <b>ЧЧ:ММ</b> (например: 14:00)",
            parse_mode="HTML",
        )
        return
    
    hours, minutes = int(match.group(1)), int(match.group(2))
    end_time = f"{hours:02d}:{minutes:02d}"
    
    data = await state.get_data()
    start_time = data.get("exception_custom_start_time")
    date_str = data.get("exception_date")
    date_dt = datetime.fromisoformat(date_str)
    date_label = format_date_ru(date_dt)
    
    # Validate end > start
    start_parts = start_time.split(':')
    end_parts = end_time.split(':')
    start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
    end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
    
    if end_minutes <= start_minutes:
        await message.answer(
            "⚠️ Время окончания должно быть позже времени начала.\n\n"
            "Введите другое время:",
            parse_mode="HTML",
        )
        return
    
    await state.update_data(exception_custom_end_time=end_time)
    await state.set_state(DateExceptionStates.confirming_exception)
    
    text = EXCEPTIONS_TITLE + EXCEPTIONS_CONFIRM_CUSTOM.format(
        date=date_label,
        start_time=start_time,
        end_time=end_time,
    )
    
    await message.answer(
        text=text,
        reply_markup=get_confirm_exception_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_CONFIRM_EXCEPTION, DateExceptionStates.confirming_exception)
async def confirm_exception(callback: CallbackQuery, state: FSMContext):
    """Create exception via API."""
    await callback.answer()
    
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    if not nutritionist_id:
        await state.set_state(None)
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_back_keyboard(CB_SCHEDULE),
        )
        return
    
    exception_date = data.get("exception_date")
    exception_type = data.get("exception_type")
    custom_hours = None
    
    if exception_type == "custom":
        start_time = data.get("exception_custom_start_time")
        end_time = data.get("exception_custom_end_time")
        custom_hours = [{"start": start_time, "end": end_time}]
    
    # Create exception via API
    api = get_api_client()
    response = await api.create_date_exception(
        nutritionist_id,
        exception_date,
        exception_type,
        custom_hours,
    )
    
    await state.set_state(None)
    
    if response.success:
        date_dt = datetime.fromisoformat(exception_date)
        date_label = format_date_ru(date_dt)
        
        if exception_type == "off":
            text = EXCEPTIONS_TITLE + EXCEPTIONS_CREATED_OFF.format(date=date_label)
        else:
            start_time = data.get("exception_custom_start_time")
            end_time = data.get("exception_custom_end_time")
            text = EXCEPTIONS_TITLE + EXCEPTIONS_CREATED_CUSTOM.format(
                date=date_label,
                start_time=start_time,
                end_time=end_time,
            )
        
        await callback.message.edit_text(
            text=text,
            reply_markup=get_exceptions_keyboard(has_exceptions=True),
            parse_mode="HTML",
        )
    else:
        error = response.error or "Неизвестная ошибка"
        
        # Handle specific errors
        if response.status_code == 409 or "уже существует" in error.lower():
            error = EXCEPTIONS_ALREADY_EXISTS
        
        text = EXCEPTIONS_TITLE + EXCEPTIONS_ERROR.format(error=error)
        await callback.message.edit_text(
            text=text,
            reply_markup=get_exceptions_keyboard(has_exceptions=True),
            parse_mode="HTML",
        )


@router.callback_query(F.data == CB_DELETE_EXCEPTION)
async def start_delete_exception(callback: CallbackQuery, state: FSMContext):
    """Show list of exceptions to delete."""
    await callback.answer()
    
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    if not nutritionist_id:
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_back_keyboard(CB_SCHEDULE),
        )
        return
    
    # Fetch exceptions
    api = get_api_client()
    response = await api.list_date_exceptions(nutritionist_id)
    
    if not response.success:
        await callback.message.edit_text(
            text="⚠️ Не удалось загрузить исключения.",
            reply_markup=get_exceptions_keyboard(has_exceptions=False),
            parse_mode="HTML",
        )
        return
    
    exceptions = response.data.get("exceptions", [])
    
    if not exceptions:
        text = EXCEPTIONS_DELETE_TITLE + "Нет исключений для удаления."
        await callback.message.edit_text(
            text=text,
            reply_markup=get_exceptions_keyboard(has_exceptions=False),
            parse_mode="HTML",
        )
        return
    
    # Build exception list for selection
    exception_options = []
    for exc in exceptions:
        exc_date = datetime.fromisoformat(exc["exception_date"]).date()
        date_label = format_date_ru(datetime.combine(exc_date, datetime.min.time()))
        exc_type = exc.get("exception_type", "off")
        
        if exc_type == "off":
            label = EXCEPTIONS_ITEM_OFF.format(date=date_label)
        else:
            custom_hours = exc.get("custom_hours", [])
            if custom_hours:
                time_ranges = format_time_ranges_list(custom_hours)
                label = EXCEPTIONS_ITEM_CUSTOM.format(
                    date=date_label,
                    time_ranges=time_ranges,
                )
            else:
                label = EXCEPTIONS_ITEM_CUSTOM.format(
                    date=date_label,
                    time_ranges="Особые часы",
                )
        
        exception_options.append({
            "id": exc["id"],
            "label": label,
        })
    
    await state.set_state(DateExceptionStates.selecting_exception)
    
    text = EXCEPTIONS_DELETE_TITLE + EXCEPTIONS_DELETE_SELECT
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_delete_exception_keyboard(exception_options),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith(CB_EXCEPTION_DELETE_PREFIX), DateExceptionStates.selecting_exception)
async def confirm_delete_exception(callback: CallbackQuery, state: FSMContext):
    """Delete the selected exception."""
    await callback.answer()
    
    exception_id = callback.data.replace(CB_EXCEPTION_DELETE_PREFIX, "")
    
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    if not nutritionist_id:
        await state.set_state(None)
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_back_keyboard(CB_SCHEDULE),
        )
        return
    
    # Delete exception via API
    api = get_api_client()
    response = await api.delete_date_exception(nutritionist_id, exception_id)
    
    await state.set_state(None)
    
    if response.success:
        text = EXCEPTIONS_TITLE + EXCEPTIONS_DELETED
        await callback.message.edit_text(
            text=text,
            reply_markup=get_exceptions_keyboard(has_exceptions=True),
            parse_mode="HTML",
        )
    else:
        error = response.error or "Неизвестная ошибка"
        text = EXCEPTIONS_TITLE + EXCEPTIONS_ERROR.format(error=error)
        await callback.message.edit_text(
            text=text,
            reply_markup=get_exceptions_keyboard(has_exceptions=True),
            parse_mode="HTML",
        )


@router.callback_query(F.data == CB_CANCEL_EXCEPTION)
async def cancel_exception(callback: CallbackQuery, state: FSMContext):
    """Cancel exception flow and return to exceptions list."""
    await callback.answer("Отменено")
    await state.set_state(None)
    await show_exceptions(callback, state)
