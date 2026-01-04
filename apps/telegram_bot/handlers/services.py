"""
Services Management Handlers
FSM-based flow for creating and managing services.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from api_client import get_api_client
from states import ServiceStates
from keyboards import (
    get_services_keyboard,
    get_service_edit_keyboard,
    get_confirm_delete_keyboard,
    get_confirm_service_keyboard,
    get_skip_keyboard,
    get_back_keyboard,
    CB_MY_SERVICES,
    CB_ADD_SERVICE,
    CB_EDIT_SERVICE_PREFIX,
    CB_DELETE_SERVICE_PREFIX,
    CB_CONFIRM_DELETE_PREFIX,
    CB_SERVICE_TOGGLE_PREFIX,
    CB_SKIP_DESCRIPTION,
    CB_CONFIRM_SERVICE,
    CB_CANCEL_SERVICE,
    CB_PERSONAL_CABINET,
)


logger = logging.getLogger(__name__)
router = Router(name="services")


@router.callback_query(F.data == CB_MY_SERVICES)
async def show_services(callback: CallbackQuery, state: FSMContext):
    """Show services list."""
    await callback.answer()
    
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    if not nutritionist_id:
        await callback.message.edit_text(
            text="❌ Профиль не найден. Сначала создайте профиль.",
            reply_markup=get_back_keyboard(CB_PERSONAL_CABINET),
        )
        return
    
    # Fetch services from backend
    api = get_api_client()
    response = await api.list_services(nutritionist_id)
    
    if not response.success:
        await callback.message.edit_text(
            text=f"❌ Ошибка загрузки услуг: {response.error}",
            reply_markup=get_back_keyboard(CB_PERSONAL_CABINET),
        )
        return
    
    services = response.data.get("services", []) if response.data else []
    await state.update_data(services=services)
    
    if not services:
        text = (
            "📋 <b>Мои услуги</b>\n\n"
            "У вас пока нет услуг.\n"
            "Добавьте первую услугу, чтобы клиенты могли записаться."
        )
    else:
        text = (
            "📋 <b>Мои услуги</b>\n\n"
            f"Всего услуг: {len(services)}\n"
            "Нажмите на услугу для редактирования."
        )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_services_keyboard(services),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_ADD_SERVICE)
async def start_add_service(callback: CallbackQuery, state: FSMContext):
    """Start service creation flow."""
    await callback.answer()
    
    # Initialize service draft
    await state.update_data(service_draft={})
    await state.set_state(ServiceStates.waiting_title)
    
    await callback.message.edit_text(
        text=(
            "➕ <b>Создание услуги</b>\n\n"
            "Шаг 1 из 4: Название услуги\n\n"
            "Введите название услуги (например, «Консультация по питанию»):"
        ),
        parse_mode="HTML",
    )


@router.message(ServiceStates.waiting_title)
async def process_service_title(message: Message, state: FSMContext):
    """Process service title input."""
    title = message.text.strip() if message.text else ""
    
    if len(title) < 3:
        await message.answer("⚠️ Название слишком короткое. Минимум 3 символа:")
        return
    
    if len(title) > 100:
        await message.answer("⚠️ Название слишком длинное. Максимум 100 символов:")
        return
    
    data = await state.get_data()
    service_draft = data.get("service_draft", {})
    service_draft["title"] = title
    await state.update_data(service_draft=service_draft)
    
    await state.set_state(ServiceStates.waiting_description)
    
    await message.answer(
        text=(
            "📝 <b>Шаг 2 из 4: Описание (опционально)</b>\n\n"
            "Опишите, что включает услуга.\n"
            "Это поможет клиентам понять, чего ожидать."
        ),
        reply_markup=get_skip_keyboard(CB_SKIP_DESCRIPTION),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_SKIP_DESCRIPTION, ServiceStates.waiting_description)
async def skip_service_description(callback: CallbackQuery, state: FSMContext):
    """Skip description."""
    await callback.answer()
    await move_to_duration_step(callback.message, state, is_callback=True)


@router.message(ServiceStates.waiting_description)
async def process_service_description(message: Message, state: FSMContext):
    """Process service description."""
    description = message.text.strip() if message.text else ""
    
    if len(description) > 500:
        await message.answer("⚠️ Описание слишком длинное. Максимум 500 символов:")
        return
    
    if description:
        data = await state.get_data()
        service_draft = data.get("service_draft", {})
        service_draft["description"] = description
        await state.update_data(service_draft=service_draft)
    
    await move_to_duration_step(message, state, is_callback=False)


async def move_to_duration_step(message: Message, state: FSMContext, is_callback: bool):
    """Move to duration input step."""
    await state.set_state(ServiceStates.waiting_duration)
    
    text = (
        "⏱️ <b>Шаг 3 из 4: Длительность</b>\n\n"
        "Введите длительность консультации в минутах.\n\n"
        "Примеры: 30, 45, 60, 90"
    )
    
    if is_callback:
        await message.edit_text(text=text, parse_mode="HTML")
    else:
        await message.answer(text=text, parse_mode="HTML")


@router.message(ServiceStates.waiting_duration)
async def process_service_duration(message: Message, state: FSMContext):
    """Process service duration."""
    text = message.text.strip() if message.text else ""
    
    try:
        duration = int(text)
        if duration < 15:
            await message.answer("⚠️ Минимальная длительность — 15 минут:")
            return
        if duration > 240:
            await message.answer("⚠️ Максимальная длительность — 240 минут (4 часа):")
            return
    except ValueError:
        await message.answer("⚠️ Введите число минут (например, 60):")
        return
    
    data = await state.get_data()
    service_draft = data.get("service_draft", {})
    service_draft["duration_minutes"] = duration
    await state.update_data(service_draft=service_draft)
    
    await state.set_state(ServiceStates.waiting_price)
    
    await message.answer(
        text=(
            "💰 <b>Шаг 4 из 4: Цена</b>\n\n"
            "Введите стоимость консультации в рублях.\n\n"
            "Примеры: 2000, 3500, 5000"
        ),
        parse_mode="HTML",
    )


@router.message(ServiceStates.waiting_price)
async def process_service_price(message: Message, state: FSMContext):
    """Process service price."""
    text = message.text.strip().replace(" ", "").replace("₽", "") if message.text else ""
    
    try:
        price = int(text)
        if price < 100:
            await message.answer("⚠️ Минимальная цена — 100₽:")
            return
        if price > 100000:
            await message.answer("⚠️ Максимальная цена — 100 000₽:")
            return
    except ValueError:
        await message.answer("⚠️ Введите сумму в рублях (например, 3000):")
        return
    
    data = await state.get_data()
    service_draft = data.get("service_draft", {})
    service_draft["price_rub"] = price
    await state.update_data(service_draft=service_draft)
    
    await state.set_state(ServiceStates.confirming_service)
    
    # Show confirmation
    title = service_draft.get("title", "")
    description = service_draft.get("description", "Не указано")
    duration = service_draft.get("duration_minutes", 60)
    
    text = (
        "✅ <b>Проверьте данные услуги</b>\n\n"
        f"<b>Название:</b> {title}\n"
        f"<b>Описание:</b> {description[:100]}{'...' if len(description) > 100 else ''}\n"
        f"<b>Длительность:</b> {duration} мин\n"
        f"<b>Цена:</b> {price:,}₽\n\n"
        "Создать услугу?"
    )
    
    await message.answer(
        text=text,
        reply_markup=get_confirm_service_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_CONFIRM_SERVICE, ServiceStates.confirming_service)
async def confirm_create_service(callback: CallbackQuery, state: FSMContext):
    """Confirm and create service."""
    await callback.answer("Создаём...")
    
    data = await state.get_data()
    service_draft = data.get("service_draft", {})
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    if not nutritionist_id:
        await callback.message.edit_text(
            text="❌ Профиль не найден.",
            reply_markup=get_back_keyboard(CB_MY_SERVICES),
        )
        return
    
    # Create service via backend
    api = get_api_client()
    response = await api.create_service(
        nutritionist_id=nutritionist_id,
        title=service_draft.get("title", ""),
        duration_minutes=service_draft.get("duration_minutes", 60),
        price_rub=service_draft.get("price_rub", 0),
        description=service_draft.get("description"),
    )
    
    await state.set_state(None)
    await state.update_data(service_draft=None)
    
    if response.success:
        service = response.data.get("service", {})
        
        await callback.message.edit_text(
            text=(
                "🎉 <b>Услуга создана!</b>\n\n"
                f"<b>{service.get('title')}</b>\n"
                f"Цена: {service.get('price_rub', 0):,}₽\n\n"
                "Услуга доступна клиентам для записи."
            ),
            reply_markup=get_back_keyboard(CB_MY_SERVICES),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            text=f"❌ Ошибка создания: {response.error}",
            reply_markup=get_back_keyboard(CB_MY_SERVICES),
        )


@router.callback_query(F.data == CB_CANCEL_SERVICE)
async def cancel_service_creation(callback: CallbackQuery, state: FSMContext):
    """Cancel service creation."""
    await callback.answer("Отменено")
    await state.set_state(None)
    await state.update_data(service_draft=None)
    
    await callback.message.edit_text(
        text="❌ Создание услуги отменено.",
        reply_markup=get_back_keyboard(CB_MY_SERVICES),
    )


@router.callback_query(F.data.startswith(CB_EDIT_SERVICE_PREFIX))
async def show_service_details(callback: CallbackQuery, state: FSMContext):
    """Show service details with edit options."""
    await callback.answer()
    
    service_id = callback.data.replace(CB_EDIT_SERVICE_PREFIX, "")
    
    data = await state.get_data()
    services = data.get("services", [])
    
    # Find service
    service = next((s for s in services if s["id"] == service_id), None)
    
    if not service:
        await callback.message.edit_text(
            text="❌ Услуга не найдена.",
            reply_markup=get_back_keyboard(CB_MY_SERVICES),
        )
        return
    
    is_active = service.get("is_active", True)
    status = "✅ Активна" if is_active else "⏸️ Неактивна"
    
    text = (
        f"📋 <b>{service.get('title')}</b>\n\n"
        f"<b>Описание:</b> {service.get('description') or 'Не указано'}\n"
        f"<b>Длительность:</b> {service.get('duration_minutes')} мин\n"
        f"<b>Цена:</b> {service.get('price_rub', 0):,}₽\n"
        f"<b>Статус:</b> {status}\n\n"
        "Выберите действие:"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_service_edit_keyboard(service_id, is_active),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith(CB_SERVICE_TOGGLE_PREFIX))
async def toggle_service_active(callback: CallbackQuery, state: FSMContext):
    """Toggle service active status."""
    await callback.answer()
    
    service_id = callback.data.replace(CB_SERVICE_TOGGLE_PREFIX, "")
    
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    services = data.get("services", [])
    
    # Find service
    service = next((s for s in services if s["id"] == service_id), None)
    if not service:
        await callback.message.edit_text(
            text="❌ Услуга не найдена.",
            reply_markup=get_back_keyboard(CB_MY_SERVICES),
        )
        return
    
    new_status = not service.get("is_active", True)
    
    # Update via backend
    api = get_api_client()
    response = await api.update_service(
        nutritionist_id=nutritionist_id,
        service_id=service_id,
        is_active=new_status,
    )
    
    if response.success:
        # Update local cache
        service["is_active"] = new_status
        await state.update_data(services=services)
        
        status_text = "активирована" if new_status else "деактивирована"
        await callback.answer(f"Услуга {status_text}", show_alert=True)
        
        # Refresh view
        await show_service_details(callback, state)
    else:
        await callback.answer(f"Ошибка: {response.error}", show_alert=True)


@router.callback_query(F.data.startswith(CB_DELETE_SERVICE_PREFIX))
async def confirm_delete_service(callback: CallbackQuery):
    """Show delete confirmation."""
    await callback.answer()
    
    service_id = callback.data.replace(CB_DELETE_SERVICE_PREFIX, "")
    
    await callback.message.edit_text(
        text=(
            "⚠️ <b>Удаление услуги</b>\n\n"
            "Вы уверены? Это действие нельзя отменить.\n"
            "Существующие записи на эту услугу сохранятся."
        ),
        reply_markup=get_confirm_delete_keyboard(service_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith(CB_CONFIRM_DELETE_PREFIX))
async def delete_service(callback: CallbackQuery, state: FSMContext):
    """Delete service."""
    await callback.answer("Удаляем...")
    
    service_id = callback.data.replace(CB_CONFIRM_DELETE_PREFIX, "")
    
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    
    # Delete via backend
    api = get_api_client()
    response = await api.delete_service(nutritionist_id, service_id)
    
    if response.success:
        # Remove from local cache
        services = data.get("services", [])
        services = [s for s in services if s["id"] != service_id]
        await state.update_data(services=services)
        
        await callback.message.edit_text(
            text="✅ Услуга удалена.",
            reply_markup=get_back_keyboard(CB_MY_SERVICES),
        )
    else:
        await callback.message.edit_text(
            text=f"❌ Ошибка удаления: {response.error}",
            reply_markup=get_back_keyboard(CB_MY_SERVICES),
        )

