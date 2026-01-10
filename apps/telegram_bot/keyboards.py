"""
Keyboard Builders
Creates inline keyboards for bot navigation.
"""

from typing import Optional
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import get_config


# ==========================================
# Callback Data Constants
# ==========================================

# Main menu
CB_OPEN_WEBAPP = "open_webapp"
CB_FOR_NUTRITIONISTS = "for_nutritionists"

# Nutritionist menu
CB_I_AM_NUTRITIONIST = "i_am_nutritionist"
CB_CREATE_PROFILE = "create_profile"
CB_UPDATE_PROFILE = "update_profile"
CB_PERSONAL_CABINET = "personal_cabinet"
CB_BACK_MAIN = "back_main"

# Personal cabinet
CB_MY_SERVICES = "my_services"
CB_CALENDAR = "calendar"
CB_CALENDAR_REFRESH = "calendar_refresh"
CB_CALENDAR_SELECT = "calendar_select"
CB_CALENDAR_PICK_PREFIX = "calendar_pick:"
CB_REVIEWS = "reviews"
CB_STATISTICS = "statistics"
CB_SETTINGS = "settings"
CB_SUPPORT = "support"
CB_BACK_NUTRITIONIST = "back_nutritionist"

# Services
CB_ADD_SERVICE = "add_service"
CB_EDIT_SERVICE_PREFIX = "edit_service:"
CB_DELETE_SERVICE_PREFIX = "delete_service:"
CB_CONFIRM_DELETE_PREFIX = "confirm_delete:"
CB_SERVICE_TOGGLE_PREFIX = "toggle_service:"
CB_BACK_SERVICES = "back_services"

# Profile flow
CB_SKIP_PHOTO = "skip_photo"
CB_SKIP_BIO = "skip_bio"
CB_SKIP_TAGS = "skip_tags"
CB_SPEC_PREFIX = "spec:"
CB_SPEC_DONE = "spec_done"
CB_TAG_PREFIX = "tag:"
CB_TAG_DONE = "tag_done"
CB_CONFIRM_RULES = "confirm_rules"
CB_SUBMIT_PROFILE = "submit_profile"
CB_CANCEL_PROFILE = "cancel_profile"

# Service flow
CB_SKIP_DESCRIPTION = "skip_description"
CB_CONFIRM_SERVICE = "confirm_service"
CB_CANCEL_SERVICE = "cancel_service"

# Reviews pagination
CB_REVIEWS_NEXT = "reviews_next"
CB_REVIEWS_PREV = "reviews_prev"

# Support
CB_CANCEL_SUPPORT = "cancel_support"

# Schedule (Slots)
CB_SCHEDULE = "schedule"
CB_ADD_SLOT = "add_slot"
CB_DELETE_SLOT = "delete_slot"
CB_REFRESH_SCHEDULE = "refresh_schedule"
CB_SLOT_DATE_PREFIX = "slot_date:"
CB_SLOT_DURATION_PREFIX = "slot_dur:"
CB_CONFIRM_SLOT = "confirm_slot"
CB_CANCEL_SLOT = "cancel_slot"
CB_SELECT_SLOT_DELETE_PREFIX = "del_slot:"

# Bookings
CB_MY_BOOKINGS = "my_bookings"
CB_REFRESH_BOOKINGS = "refresh_bookings"
CB_BOOKINGS_NEXT = "bookings_next"
CB_BOOKINGS_PREV = "bookings_prev"

# Working Hours Template
CB_WORKING_HOURS = "working_hours"
CB_WORKING_HOURS_DAY_PREFIX = "wh_day:"
CB_ADD_TIME_RANGE = "add_time_range"
CB_DELETE_TIME_RANGE_PREFIX = "del_time_range:"
CB_CLEAR_DAY_RANGES = "clear_day_ranges"
CB_BACK_DAY = "wh_back_day"
CB_CONFIRM_TIME_RANGE = "confirm_time_range"
CB_SAVE_TEMPLATE = "save_template"
CB_CANCEL_WORKING_HOURS = "cancel_working_hours"

# Date Exceptions
CB_EXCEPTIONS = "exceptions"
CB_ADD_EXCEPTION = "add_exception"
CB_DELETE_EXCEPTION = "delete_exception"
CB_EXCEPTION_DATE_PREFIX = "exc_date:"
CB_EXCEPTION_TYPE_OFF = "exc_type_off"
CB_EXCEPTION_TYPE_CUSTOM = "exc_type_custom"
CB_EXCEPTION_DELETE_PREFIX = "exc_del:"
CB_CANCEL_EXCEPTION = "cancel_exception"
CB_CONFIRM_EXCEPTION = "confirm_exception"


# ==========================================
# Keyboard Builders
# ==========================================

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu with WebApp button and nutritionist entry."""
    config = get_config()
    
    builder = InlineKeyboardBuilder()
    
    # WebApp button (opens Mini App)
    # Only show if URL is valid (starts with https://)
    webapp_url = config.webapp_url
    if webapp_url and webapp_url.startswith("https://") and webapp_url != "https://t.me/your_bot/app":
        builder.row(
            InlineKeyboardButton(
                text="🍎 Открыть мини-приложение",
                web_app=WebAppInfo(url=webapp_url),
            )
        )
    
    # For nutritionists button
    builder.row(
        InlineKeyboardButton(
            text="👩‍⚕️ Для нутрициологов",
            callback_data=CB_FOR_NUTRITIONISTS,
        )
    )
    
    return builder.as_markup()


def get_nutritionist_menu_keyboard(has_profile: bool = False) -> InlineKeyboardMarkup:
    """Nutritionist menu - options based on whether they have a profile."""
    builder = InlineKeyboardBuilder()
    
    if not has_profile:
        builder.row(
            InlineKeyboardButton(
                text="✨ Я нутрициолог",
                callback_data=CB_I_AM_NUTRITIONIST,
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📝 Создать профиль",
                callback_data=CB_CREATE_PROFILE,
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="✏️ Обновить профиль",
                callback_data=CB_UPDATE_PROFILE,
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🏠 Личный кабинет",
                callback_data=CB_PERSONAL_CABINET,
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=CB_BACK_MAIN,
        )
    )
    
    return builder.as_markup()


def get_personal_cabinet_keyboard() -> InlineKeyboardMarkup:
    """Personal cabinet menu."""
    builder = InlineKeyboardBuilder()
    
    # Primary actions: Schedule and Bookings
    builder.row(
        InlineKeyboardButton(
            text="🕒 Расписание",
            callback_data=CB_SCHEDULE,
        ),
        InlineKeyboardButton(
            text="📋 Мои бронирования",
            callback_data=CB_MY_BOOKINGS,
        ),
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📋 Мои услуги",
            callback_data=CB_MY_SERVICES,
        ),
        InlineKeyboardButton(
            text="📅 Календарь",
            callback_data=CB_CALENDAR,
        ),
    )
    
    builder.row(
        InlineKeyboardButton(
            text="⭐ Отзывы",
            callback_data=CB_REVIEWS,
        ),
        InlineKeyboardButton(
            text="📊 Статистика",
            callback_data=CB_STATISTICS,
        ),
    )
    
    builder.row(
        InlineKeyboardButton(
            text="⚙️ Настройки",
            callback_data=CB_SETTINGS,
        ),
        InlineKeyboardButton(
            text="💬 Поддержка",
            callback_data=CB_SUPPORT,
        ),
    )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=CB_BACK_NUTRITIONIST,
        )
    )
    
    return builder.as_markup()


def get_services_keyboard(services: list[dict]) -> InlineKeyboardMarkup:
    """Services list with add/edit/delete options."""
    builder = InlineKeyboardBuilder()
    
    # Add new service button
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить услугу",
            callback_data=CB_ADD_SERVICE,
        )
    )
    
    # List existing services
    for service in services:
        service_id = service["id"]
        title = service["title"]
        price = service["price_rub"]
        is_active = service.get("is_active", True)
        
        status_emoji = "✅" if is_active else "⏸️"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} {title} — {price}₽",
                callback_data=f"{CB_EDIT_SERVICE_PREFIX}{service_id}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=CB_BACK_NUTRITIONIST,
        )
    )
    
    return builder.as_markup()


def get_service_edit_keyboard(service_id: str, is_active: bool) -> InlineKeyboardMarkup:
    """Edit options for a single service."""
    builder = InlineKeyboardBuilder()
    
    toggle_text = "⏸️ Деактивировать" if is_active else "✅ Активировать"
    
    builder.row(
        InlineKeyboardButton(
            text=toggle_text,
            callback_data=f"{CB_SERVICE_TOGGLE_PREFIX}{service_id}",
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🗑️ Удалить",
            callback_data=f"{CB_DELETE_SERVICE_PREFIX}{service_id}",
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад к услугам",
            callback_data=CB_MY_SERVICES,
        )
    )
    
    return builder.as_markup()


def get_confirm_delete_keyboard(service_id: str) -> InlineKeyboardMarkup:
    """Confirm service deletion."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"{CB_CONFIRM_DELETE_PREFIX}{service_id}",
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_MY_SERVICES,
        ),
    )
    
    return builder.as_markup()


def get_specializations_keyboard(
    available: list[dict],
    selected: list[str],
) -> InlineKeyboardMarkup:
    """Multi-select specializations keyboard."""
    builder = InlineKeyboardBuilder()
    
    for spec in available:
        spec_id = spec["id"]
        label = spec["label"]
        is_selected = spec_id in selected
        
        prefix = "✅ " if is_selected else ""
        
        builder.row(
            InlineKeyboardButton(
                text=f"{prefix}{label}",
                callback_data=f"{CB_SPEC_PREFIX}{spec_id}",
            )
        )
    
    # Done button (only if at least one selected)
    if selected:
        builder.row(
            InlineKeyboardButton(
                text="✓ Готово",
                callback_data=CB_SPEC_DONE,
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_PROFILE,
        )
    )
    
    return builder.as_markup()


def get_tags_keyboard(
    available: list[dict],
    selected: list[str],
) -> InlineKeyboardMarkup:
    """Multi-select tags keyboard (optional)."""
    builder = InlineKeyboardBuilder()
    
    for tag in available:
        tag_id = tag["id"]
        label = tag["label"]
        is_selected = tag_id in selected
        
        prefix = "✅ " if is_selected else ""
        
        builder.row(
            InlineKeyboardButton(
                text=f"{prefix}{label}",
                callback_data=f"{CB_TAG_PREFIX}{tag_id}",
            )
        )
    
    # Done/Skip button
    if selected:
        builder.row(
            InlineKeyboardButton(
                text="✓ Готово",
                callback_data=CB_TAG_DONE,
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="⏭️ Пропустить",
                callback_data=CB_SKIP_TAGS,
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_PROFILE,
        )
    )
    
    return builder.as_markup()


def get_skip_keyboard(skip_callback: str) -> InlineKeyboardMarkup:
    """Simple skip button."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="⏭️ Пропустить",
            callback_data=skip_callback,
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_PROFILE,
        )
    )
    
    return builder.as_markup()


def get_confirm_rules_keyboard() -> InlineKeyboardMarkup:
    """Confirm rules and restrictions."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Принимаю правила",
            callback_data=CB_CONFIRM_RULES,
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_PROFILE,
        )
    )
    
    return builder.as_markup()


def get_submit_profile_keyboard() -> InlineKeyboardMarkup:
    """Final profile submission confirmation."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📤 Отправить на модерацию",
            callback_data=CB_SUBMIT_PROFILE,
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Редактировать",
            callback_data=CB_CREATE_PROFILE,
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_PROFILE,
        )
    )
    
    return builder.as_markup()


def get_confirm_service_keyboard() -> InlineKeyboardMarkup:
    """Confirm service creation."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Создать услугу",
            callback_data=CB_CONFIRM_SERVICE,
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_SERVICE,
        )
    )
    
    return builder.as_markup()


def get_reviews_keyboard(
    offset: int,
    total: int,
    limit: int = 5,
) -> InlineKeyboardMarkup:
    """Reviews pagination keyboard."""
    builder = InlineKeyboardBuilder()
    
    buttons = []
    
    # Previous page
    if offset > 0:
        buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=CB_REVIEWS_PREV,
            )
        )
    
    # Next page
    if offset + limit < total:
        buttons.append(
            InlineKeyboardButton(
                text="Далее ▶️",
                callback_data=CB_REVIEWS_NEXT,
            )
        )
    
    if buttons:
        builder.row(*buttons)
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ В кабинет",
            callback_data=CB_PERSONAL_CABINET,
        )
    )
    
    return builder.as_markup()


def get_calendar_keyboard(
    oauth_url: Optional[str] = None,
    is_connected: bool = False,
    can_select_calendar: bool = False,
) -> InlineKeyboardMarkup:
    """Calendar connection keyboard."""
    builder = InlineKeyboardBuilder()
    
    if oauth_url:
        builder.row(
            InlineKeyboardButton(
                text="🔗 Подключить Google Calendar",
                url=oauth_url,
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="🔄 Проверить подключение",
            callback_data=CB_CALENDAR_REFRESH,
        )
    )

    if is_connected and can_select_calendar:
        builder.row(
            InlineKeyboardButton(
                text="📌 Выбрать календарь",
                callback_data=CB_CALENDAR_SELECT,
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=CB_PERSONAL_CABINET,
        )
    )
    
    return builder.as_markup()


def get_calendar_select_keyboard(
    calendars: list[dict],
    selected_id: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """Calendar selection keyboard."""
    builder = InlineKeyboardBuilder()
    
    for idx, calendar in enumerate(calendars):
        summary = calendar.get("summary") or "Calendar"
        calendar_id = calendar.get("id")
        is_selected = selected_id and calendar_id == selected_id
        prefix = "✅ " if is_selected else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{prefix}{summary}",
                callback_data=f"{CB_CALENDAR_PICK_PREFIX}{idx}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=CB_CALENDAR,
        )
    )
    
    return builder.as_markup()


def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Simple back button."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=callback_data,
        )
    )
    
    return builder.as_markup()


def get_support_keyboard() -> InlineKeyboardMarkup:
    """Support cancel keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_SUPPORT,
        )
    )
    
    return builder.as_markup()


# ==========================================
# Schedule (Slot Management) Keyboards
# ==========================================

def get_schedule_keyboard(has_free_slots: bool = False) -> InlineKeyboardMarkup:
    """Schedule management keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить слот",
            callback_data=CB_ADD_SLOT,
        )
    )
    
    if has_free_slots:
        builder.row(
            InlineKeyboardButton(
                text="❌ Удалить слот",
                callback_data=CB_DELETE_SLOT,
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🕐 Рабочие часы",
            callback_data=CB_WORKING_HOURS,
        ),
        InlineKeyboardButton(
            text="📅 Исключения",
            callback_data=CB_EXCEPTIONS,
        ),
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data=CB_REFRESH_SCHEDULE,
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=CB_PERSONAL_CABINET,
        )
    )
    
    return builder.as_markup()


def get_slot_date_keyboard(dates: list[dict]) -> InlineKeyboardMarkup:
    """
    Keyboard for selecting slot date.
    dates: list of {"date": "2024-01-15", "label": "15 янв (Пн)"}
    """
    builder = InlineKeyboardBuilder()
    
    # Show dates in rows of 2
    row_buttons = []
    for date_info in dates:
        row_buttons.append(
            InlineKeyboardButton(
                text=date_info["label"],
                callback_data=f"{CB_SLOT_DATE_PREFIX}{date_info['date']}",
            )
        )
        if len(row_buttons) == 2:
            builder.row(*row_buttons)
            row_buttons = []
    
    # Add remaining buttons
    if row_buttons:
        builder.row(*row_buttons)
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_SLOT,
        )
    )
    
    return builder.as_markup()


def get_slot_duration_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting slot duration."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="30 минут",
            callback_data=f"{CB_SLOT_DURATION_PREFIX}30",
        ),
        InlineKeyboardButton(
            text="45 минут",
            callback_data=f"{CB_SLOT_DURATION_PREFIX}45",
        ),
    )
    
    builder.row(
        InlineKeyboardButton(
            text="60 минут",
            callback_data=f"{CB_SLOT_DURATION_PREFIX}60",
        ),
        InlineKeyboardButton(
            text="90 минут",
            callback_data=f"{CB_SLOT_DURATION_PREFIX}90",
        ),
    )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_SLOT,
        )
    )
    
    return builder.as_markup()


def get_confirm_slot_keyboard() -> InlineKeyboardMarkup:
    """Confirm slot creation keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Добавить слот",
            callback_data=CB_CONFIRM_SLOT,
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_SLOT,
        )
    )
    
    return builder.as_markup()


def get_delete_slot_keyboard(slots: list[dict]) -> InlineKeyboardMarkup:
    """
    Keyboard for selecting slot to delete.
    slots: list of {"id": "uuid", "label": "15 янв, 12:00–13:00"}
    """
    builder = InlineKeyboardBuilder()
    
    for slot in slots:
        builder.row(
            InlineKeyboardButton(
                text=slot["label"],
                callback_data=f"{CB_SELECT_SLOT_DELETE_PREFIX}{slot['id']}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_SCHEDULE,
        )
    )
    
    return builder.as_markup()


# ==========================================
# Bookings Keyboards
# ==========================================

def get_bookings_keyboard(
    offset: int = 0,
    total: int = 0,
    limit: int = 10,
) -> InlineKeyboardMarkup:
    """Bookings list keyboard with pagination."""
    builder = InlineKeyboardBuilder()
    
    nav_buttons = []
    
    # Previous page
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=CB_BOOKINGS_PREV,
            )
        )
    
    # Next page
    if offset + limit < total:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Далее ▶️",
                callback_data=CB_BOOKINGS_NEXT,
            )
        )
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data=CB_REFRESH_BOOKINGS,
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ В кабинет",
            callback_data=CB_PERSONAL_CABINET,
        )
    )
    
    return builder.as_markup()


# ==========================================
# Working Hours Template Keyboards
# ==========================================

def get_working_hours_keyboard() -> InlineKeyboardMarkup:
    """Working hours main keyboard."""
    builder = InlineKeyboardBuilder()
    
    # Days of week (Monday=0 to Sunday=6)
    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    day_buttons = []
    for day_num, day_name in enumerate(day_names):
        day_buttons.append(
            InlineKeyboardButton(
                text=day_name,
                callback_data=f"{CB_WORKING_HOURS_DAY_PREFIX}{day_num}",
            )
        )
        if len(day_buttons) == 3:
            builder.row(*day_buttons)
            day_buttons = []
    
    if day_buttons:
        builder.row(*day_buttons)
    
    builder.row(
        InlineKeyboardButton(
            text="💾 Сохранить шаблон",
            callback_data=CB_SAVE_TEMPLATE,
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=CB_SCHEDULE,
        )
    )
    
    return builder.as_markup()


def get_day_time_ranges_keyboard(time_ranges: Optional[list[dict]] = None) -> InlineKeyboardMarkup:
    """Keyboard for managing time ranges for a day."""
    builder = InlineKeyboardBuilder()

    ranges = time_ranges or []

    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить диапазон",
            callback_data=CB_ADD_TIME_RANGE,
        )
    )

    for index, time_range in enumerate(ranges):
        label = f"{time_range.get('start')}–{time_range.get('end')}"
        builder.row(
            InlineKeyboardButton(
                text=f"❌ {label}",
                callback_data=f"{CB_DELETE_TIME_RANGE_PREFIX}{index}",
            )
        )

    if ranges:
        builder.row(
            InlineKeyboardButton(
                text="🧹 Очистить день",
                callback_data=CB_CLEAR_DAY_RANGES,
            )
        )

    builder.row(
        InlineKeyboardButton(
            text="💾 Сохранить шаблон",
            callback_data=CB_SAVE_TEMPLATE,
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад к дням",
            callback_data=CB_WORKING_HOURS,
        )
    )

    return builder.as_markup()


def get_working_hours_input_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for working hours input steps."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад к дню",
            callback_data=CB_BACK_DAY,
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_WORKING_HOURS,
        ),
    )

    return builder.as_markup()


def get_confirm_time_range_keyboard() -> InlineKeyboardMarkup:
    """Confirm time range addition."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Добавить",
            callback_data=CB_CONFIRM_TIME_RANGE,
        ),
        InlineKeyboardButton(
            text="◀️ Назад к дню",
            callback_data=CB_BACK_DAY,
        ),
    )
    
    return builder.as_markup()


def get_confirm_template_keyboard() -> InlineKeyboardMarkup:
    """Confirm template save."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Сохранить",
            callback_data=CB_SAVE_TEMPLATE,
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_WORKING_HOURS,
        ),
    )
    
    return builder.as_markup()


# ==========================================
# Date Exceptions Keyboards
# ==========================================

def get_exceptions_keyboard(has_exceptions: bool = False) -> InlineKeyboardMarkup:
    """Exceptions main keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить исключение",
            callback_data=CB_ADD_EXCEPTION,
        )
    )
    
    if has_exceptions:
        builder.row(
            InlineKeyboardButton(
                text="❌ Удалить исключение",
                callback_data=CB_DELETE_EXCEPTION,
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=CB_SCHEDULE,
        )
    )
    
    return builder.as_markup()


def get_exception_date_keyboard(dates: list[dict]) -> InlineKeyboardMarkup:
    """Keyboard for selecting exception date."""
    builder = InlineKeyboardBuilder()
    
    # Show dates in rows of 2
    row_buttons = []
    for date_info in dates:
        row_buttons.append(
            InlineKeyboardButton(
                text=date_info["label"],
                callback_data=f"{CB_EXCEPTION_DATE_PREFIX}{date_info['date']}",
            )
        )
        if len(row_buttons) == 2:
            builder.row(*row_buttons)
            row_buttons = []
    
    if row_buttons:
        builder.row(*row_buttons)
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_EXCEPTION,
        )
    )
    
    return builder.as_markup()


def get_exception_type_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting exception type."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🚫 Выходной",
            callback_data=CB_EXCEPTION_TYPE_OFF,
        ),
        InlineKeyboardButton(
            text="🕐 Особые часы",
            callback_data=CB_EXCEPTION_TYPE_CUSTOM,
        ),
    )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_EXCEPTION,
        )
    )
    
    return builder.as_markup()


def get_confirm_exception_keyboard() -> InlineKeyboardMarkup:
    """Confirm exception creation."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Создать",
            callback_data=CB_CONFIRM_EXCEPTION,
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_CANCEL_EXCEPTION,
        ),
    )
    
    return builder.as_markup()


def get_delete_exception_keyboard(exceptions: list[dict]) -> InlineKeyboardMarkup:
    """Keyboard for selecting exception to delete."""
    builder = InlineKeyboardBuilder()
    
    for exc in exceptions:
        builder.row(
            InlineKeyboardButton(
                text=exc["label"],
                callback_data=f"{CB_EXCEPTION_DELETE_PREFIX}{exc['id']}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=CB_EXCEPTIONS,
        )
    )
    
    return builder.as_markup()
