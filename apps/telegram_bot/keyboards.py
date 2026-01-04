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


def get_calendar_keyboard(oauth_url: Optional[str] = None) -> InlineKeyboardMarkup:
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
            text="◀️ Назад",
            callback_data=CB_PERSONAL_CABINET,
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

