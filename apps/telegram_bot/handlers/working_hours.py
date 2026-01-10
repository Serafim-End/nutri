"""
Working Hours Template Handlers
Handles weekly working hours template setup for nutritionists.
"""

import logging
import re
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from api_client import get_api_client
from states import WorkingHoursStates
from keyboards import (
    get_working_hours_keyboard,
    get_day_time_ranges_keyboard,
    get_confirm_time_range_keyboard,
    get_confirm_template_keyboard,
    get_back_keyboard,
    get_working_hours_input_keyboard,
    CB_WORKING_HOURS,
    CB_WORKING_HOURS_DAY_PREFIX,
    CB_ADD_TIME_RANGE,
    CB_DELETE_TIME_RANGE_PREFIX,
    CB_CLEAR_DAY_RANGES,
    CB_BACK_DAY,
    CB_CONFIRM_TIME_RANGE,
    CB_SAVE_TEMPLATE,
    CB_CANCEL_WORKING_HOURS,
    CB_SCHEDULE,
)
from bot_texts import (
    WORKING_HOURS_TITLE,
    WORKING_HOURS_INSTRUCTION,
    WORKING_HOURS_EMPTY,
    WORKING_HOURS_DAY_SELECTED,
    WORKING_HOURS_CURRENT_RANGES,
    WORKING_HOURS_NO_RANGES,
    WORKING_HOURS_ADD_RANGE,
    WORKING_HOURS_START_TIME,
    WORKING_HOURS_END_TIME,
    WORKING_HOURS_INVALID_TIME,
    WORKING_HOURS_END_BEFORE_START,
    WORKING_HOURS_CONFIRM_RANGE,
    WORKING_HOURS_RANGE_ADDED,
    WORKING_HOURS_RANGE_REMOVED,
    WORKING_HOURS_DAY_CLEARED,
    WORKING_HOURS_RANGE_OVERLAP,
    WORKING_HOURS_SAVE_TEMPLATE,
    WORKING_HOURS_TEMPLATE_SAVED,
    WORKING_HOURS_TEMPLATE_ERROR,
    DAY_NAMES,
)


logger = logging.getLogger(__name__)
router = Router(name="working_hours")


def format_time_range(start: str, end: str) -> str:
    """Format time range: '09:00–12:00'."""
    return f"{start}–{end}"


def format_time_ranges_list(ranges: list[dict]) -> str:
    """Format list of time ranges."""
    if not ranges:
        return ""
    return "\n".join([f"  • {format_time_range(r['start'], r['end'])}" for r in ranges])


def time_to_minutes(time_str: str) -> int:
    """Convert HH:MM string to minutes."""
    hours, minutes = time_str.split(":")
    return int(hours) * 60 + int(minutes)


def sort_time_ranges(ranges: list[dict]) -> list[dict]:
    """Sort time ranges by start time."""
    return sorted(ranges, key=lambda r: time_to_minutes(r["start"]))


def build_day_view(day_num: int, schedule: dict, notice: str | None = None) -> tuple[str, list[dict]]:
    """Build day view text and return day ranges."""
    day_name = DAY_NAMES.get(day_num, f"День {day_num}")
    day_key = str(day_num)
    time_ranges = schedule.get(day_key, [])

    text = WORKING_HOURS_TITLE + WORKING_HOURS_DAY_SELECTED.format(day_name=day_name)
    if notice:
        text += f"{notice}\n\n"

    if time_ranges:
        text += WORKING_HOURS_CURRENT_RANGES.format(
            time_ranges=format_time_ranges_list(time_ranges)
        )
    else:
        text += WORKING_HOURS_NO_RANGES

    text += WORKING_HOURS_ADD_RANGE
    return text, time_ranges


@router.callback_query(F.data == CB_WORKING_HOURS)
async def show_working_hours(callback: CallbackQuery, state: FSMContext):
    """Show working hours template setup."""
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
    
    # Fetch current template
    api = get_api_client()
    response = await api.get_working_hours_template(nutritionist_id)
    
    if response.success and response.data:
        template = response.data.get("template", {})
        weekly_schedule = template.get("weekly_schedule", {})
        
        # Ensure keys are strings (API returns string keys)
        schedule_normalized = {
            str(k): sort_time_ranges(v) for k, v in weekly_schedule.items()
        }
        
        # Store in state
        await state.update_data(working_hours_schedule=schedule_normalized)
        
        if schedule_normalized:
            text = WORKING_HOURS_TITLE + WORKING_HOURS_INSTRUCTION
        else:
            text = WORKING_HOURS_TITLE + WORKING_HOURS_EMPTY
    else:
        await state.update_data(working_hours_schedule={})
        text = WORKING_HOURS_TITLE + WORKING_HOURS_EMPTY
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_working_hours_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith(CB_WORKING_HOURS_DAY_PREFIX))
async def select_day(callback: CallbackQuery, state: FSMContext):
    """Handle day selection, show current time ranges."""
    await callback.answer()
    
    day_num = int(callback.data.replace(CB_WORKING_HOURS_DAY_PREFIX, ""))
    data = await state.get_data()
    schedule = data.get("working_hours_schedule", {})
    day_key = str(day_num)
    if schedule.get(day_key):
        schedule[day_key] = sort_time_ranges(schedule[day_key])
        await state.update_data(working_hours_schedule=schedule)

    text, time_ranges = build_day_view(day_num, schedule)
    
    await state.update_data(working_hours_current_day=day_num)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_day_time_ranges_keyboard(time_ranges=time_ranges),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_ADD_TIME_RANGE)
async def start_add_time_range(callback: CallbackQuery, state: FSMContext):
    """Start adding time range - ask for start time."""
    await callback.answer()
    
    data = await state.get_data()
    day_num = data.get("working_hours_current_day")
    day_name = DAY_NAMES.get(day_num, f"День {day_num}")
    
    await state.set_state(WorkingHoursStates.waiting_start_time)
    
    text = (
        WORKING_HOURS_TITLE +
        WORKING_HOURS_DAY_SELECTED.format(day_name=day_name) +
        WORKING_HOURS_START_TIME
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_working_hours_input_keyboard(),
        parse_mode="HTML",
    )


@router.message(WorkingHoursStates.waiting_start_time)
async def process_start_time(message: Message, state: FSMContext):
    """Process start time input, ask for end time."""
    time_text = message.text.strip() if message.text else ""
    
    # Validate time format (HH:MM)
    time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')
    match = time_pattern.match(time_text)
    
    if not match:
        await message.answer(
            WORKING_HOURS_INVALID_TIME,
            reply_markup=get_working_hours_input_keyboard(),
            parse_mode="HTML",
        )
        return
    
    hours, minutes = int(match.group(1)), int(match.group(2))
    start_time = f"{hours:02d}:{minutes:02d}"
    
    data = await state.get_data()
    day_num = data.get("working_hours_current_day")
    day_name = DAY_NAMES.get(day_num, f"День {day_num}")
    
    await state.update_data(working_hours_start_time=start_time)
    await state.set_state(WorkingHoursStates.waiting_end_time)
    
    text = (
        WORKING_HOURS_TITLE +
        WORKING_HOURS_DAY_SELECTED.format(day_name=day_name) +
        WORKING_HOURS_END_TIME.format(start_time=start_time)
    )
    
    await message.answer(
        text=text,
        reply_markup=get_working_hours_input_keyboard(),
        parse_mode="HTML",
    )


@router.message(WorkingHoursStates.waiting_end_time)
async def process_end_time(message: Message, state: FSMContext):
    """Process end time input, show confirmation."""
    time_text = message.text.strip() if message.text else ""
    
    # Validate time format
    time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')
    match = time_pattern.match(time_text)
    
    if not match:
        await message.answer(
            WORKING_HOURS_INVALID_TIME,
            reply_markup=get_working_hours_input_keyboard(),
            parse_mode="HTML",
        )
        return
    
    hours, minutes = int(match.group(1)), int(match.group(2))
    end_time = f"{hours:02d}:{minutes:02d}"
    
    data = await state.get_data()
    start_time = data.get("working_hours_start_time")
    day_num = data.get("working_hours_current_day")
    day_name = DAY_NAMES.get(day_num, f"День {day_num}")
    
    # Validate end > start
    start_parts = start_time.split(':')
    end_parts = end_time.split(':')
    start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
    end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
    
    if end_minutes <= start_minutes:
        await message.answer(
            WORKING_HOURS_END_BEFORE_START,
            reply_markup=get_working_hours_input_keyboard(),
            parse_mode="HTML",
        )
        return
    
    await state.update_data(working_hours_end_time=end_time)
    await state.set_state(WorkingHoursStates.confirming_time_range)
    
    text = (
        WORKING_HOURS_TITLE +
        WORKING_HOURS_CONFIRM_RANGE.format(
            day_name=day_name,
            start_time=start_time,
            end_time=end_time,
        )
    )
    
    await message.answer(
        text=text,
        reply_markup=get_confirm_time_range_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_CONFIRM_TIME_RANGE, WorkingHoursStates.confirming_time_range)
async def confirm_time_range(callback: CallbackQuery, state: FSMContext):
    """Confirm and add time range to schedule."""
    await callback.answer()
    
    data = await state.get_data()
    day_num = data.get("working_hours_current_day")
    start_time = data.get("working_hours_start_time")
    end_time = data.get("working_hours_end_time")
    
    schedule = data.get("working_hours_schedule", {})
    day_key = str(day_num)
    
    # Add time range to schedule
    if day_key not in schedule:
        schedule[day_key] = []

    new_start = time_to_minutes(start_time)
    new_end = time_to_minutes(end_time)
    for existing in schedule[day_key]:
        existing_start = time_to_minutes(existing["start"])
        existing_end = time_to_minutes(existing["end"])
        if new_start < existing_end and new_end > existing_start:
            text, time_ranges = build_day_view(
                day_num,
                schedule,
                notice=WORKING_HOURS_RANGE_OVERLAP,
            )
            await state.set_state(None)
            await callback.message.edit_text(
                text=text,
                reply_markup=get_day_time_ranges_keyboard(time_ranges=time_ranges),
                parse_mode="HTML",
            )
            return

    schedule[day_key].append({
        "start": start_time,
        "end": end_time,
    })
    schedule[day_key] = sort_time_ranges(schedule[day_key])
    
    await state.update_data(working_hours_schedule=schedule)
    await state.set_state(None)
    
    text, time_ranges = build_day_view(
        day_num,
        schedule,
        notice=WORKING_HOURS_RANGE_ADDED,
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=get_day_time_ranges_keyboard(time_ranges=time_ranges),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith(CB_DELETE_TIME_RANGE_PREFIX))
async def delete_time_range(callback: CallbackQuery, state: FSMContext):
    """Remove a time range from the current day."""
    await callback.answer()

    data = await state.get_data()
    day_num = data.get("working_hours_current_day")
    schedule = data.get("working_hours_schedule", {})

    if day_num is None:
        await callback.message.edit_text(
            text=WORKING_HOURS_TITLE + WORKING_HOURS_EMPTY,
            reply_markup=get_working_hours_keyboard(),
            parse_mode="HTML",
        )
        return

    day_key = str(day_num)
    time_ranges = schedule.get(day_key, [])

    try:
        index = int(callback.data.replace(CB_DELETE_TIME_RANGE_PREFIX, ""))
    except ValueError:
        index = -1

    if 0 <= index < len(time_ranges):
        time_ranges.pop(index)
        if time_ranges:
            schedule[day_key] = sort_time_ranges(time_ranges)
        else:
            schedule.pop(day_key, None)

    await state.update_data(working_hours_schedule=schedule)

    text, ranges = build_day_view(
        day_num,
        schedule,
        notice=WORKING_HOURS_RANGE_REMOVED,
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=get_day_time_ranges_keyboard(time_ranges=ranges),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_CLEAR_DAY_RANGES)
async def clear_day_ranges(callback: CallbackQuery, state: FSMContext):
    """Clear all ranges for the current day."""
    await callback.answer()

    data = await state.get_data()
    day_num = data.get("working_hours_current_day")
    schedule = data.get("working_hours_schedule", {})

    if day_num is None:
        await callback.message.edit_text(
            text=WORKING_HOURS_TITLE + WORKING_HOURS_EMPTY,
            reply_markup=get_working_hours_keyboard(),
            parse_mode="HTML",
        )
        return

    schedule.pop(str(day_num), None)
    await state.update_data(working_hours_schedule=schedule)

    text, ranges = build_day_view(
        day_num,
        schedule,
        notice=WORKING_HOURS_DAY_CLEARED,
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=get_day_time_ranges_keyboard(time_ranges=ranges),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_BACK_DAY)
async def back_to_day(callback: CallbackQuery, state: FSMContext):
    """Return to current day view."""
    await callback.answer()
    await state.set_state(None)

    data = await state.get_data()
    day_num = data.get("working_hours_current_day")
    schedule = data.get("working_hours_schedule", {})

    if day_num is None:
        await callback.message.edit_text(
            text=WORKING_HOURS_TITLE + WORKING_HOURS_EMPTY,
            reply_markup=get_working_hours_keyboard(),
            parse_mode="HTML",
        )
        return

    text, time_ranges = build_day_view(day_num, schedule)
    await callback.message.edit_text(
        text=text,
        reply_markup=get_day_time_ranges_keyboard(time_ranges=time_ranges),
        parse_mode="HTML",
    )

@router.callback_query(F.data == CB_SAVE_TEMPLATE)
async def save_template(callback: CallbackQuery, state: FSMContext):
    """Save working hours template to backend."""
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
    
    schedule = data.get("working_hours_schedule", {})
    
    # Convert string keys to int for API
    schedule_int = {
        int(day): ranges for day, ranges in schedule.items()
    }
    
    # Save to backend
    api = get_api_client()
    response = await api.update_working_hours_template(nutritionist_id, schedule_int)
    
    await state.set_state(None)
    
    if response.success:
        text = WORKING_HOURS_TITLE + WORKING_HOURS_TEMPLATE_SAVED
        await callback.message.edit_text(
            text=text,
            reply_markup=get_back_keyboard(CB_SCHEDULE),
            parse_mode="HTML",
        )
    else:
        error = response.error or "Неизвестная ошибка"
        text = WORKING_HOURS_TITLE + WORKING_HOURS_TEMPLATE_ERROR.format(error=error)
        await callback.message.edit_text(
            text=text,
            reply_markup=get_working_hours_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data == CB_CANCEL_WORKING_HOURS)
async def cancel_working_hours(callback: CallbackQuery, state: FSMContext):
    """Cancel working hours setup and return to schedule."""
    await callback.answer("Отменено")
    await state.set_state(None)
    
    # Redirect to schedule by showing a message with schedule button
    # User can click "Назад" to go to schedule
    from keyboards import get_schedule_keyboard
    await callback.message.edit_text(
        text=(
            "🕒 <b>Расписание</b>\n\n"
            "Настройка рабочих часов отменена.\n\n"
            "Нажмите «Назад» для возврата к расписанию."
        ),
        reply_markup=get_back_keyboard(CB_SCHEDULE),
        parse_mode="HTML",
    )
