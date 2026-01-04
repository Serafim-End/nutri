"""
Profile Creation/Update Handlers
FSM-based flow for nutritionist profile management.
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from api_client import get_api_client
from states import ProfileStates
from keyboards import (
    get_nutritionist_menu_keyboard,
    get_skip_keyboard,
    get_specializations_keyboard,
    get_tags_keyboard,
    get_confirm_rules_keyboard,
    get_submit_profile_keyboard,
    CB_CREATE_PROFILE,
    CB_UPDATE_PROFILE,
    CB_SKIP_PHOTO,
    CB_SKIP_BIO,
    CB_SKIP_TAGS,
    CB_SPEC_PREFIX,
    CB_SPEC_DONE,
    CB_TAG_PREFIX,
    CB_TAG_DONE,
    CB_CONFIRM_RULES,
    CB_SUBMIT_PROFILE,
    CB_CANCEL_PROFILE,
)


logger = logging.getLogger(__name__)
router = Router(name="profile")

# Static specializations (should match backend filter options)
SPECIALIZATIONS = [
    {"id": "weight_management", "label": "Управление весом"},
    {"id": "sports_nutrition", "label": "Спортивное питание"},
    {"id": "gut_health", "label": "Здоровье ЖКТ"},
    {"id": "diabetes", "label": "Диабет"},
    {"id": "hormonal_health", "label": "Гормональное здоровье"},
    {"id": "pediatric", "label": "Детское питание"},
    {"id": "pregnancy", "label": "Питание при беременности"},
    {"id": "eating_disorders", "label": "Расстройства пищевого поведения"},
    {"id": "autoimmune", "label": "Аутоиммунные заболевания"},
    {"id": "plant_based", "label": "Растительное питание"},
]

# Static tags
TAGS = [
    {"id": "vegetarian", "label": "Вегетарианство"},
    {"id": "vegan", "label": "Веганство"},
    {"id": "keto", "label": "Кето-диета"},
    {"id": "intermittent_fasting", "label": "Интервальное голодание"},
    {"id": "anti_aging", "label": "Anti-age питание"},
    {"id": "detox", "label": "Детокс"},
    {"id": "allergy", "label": "Аллергия/непереносимость"},
    {"id": "online_only", "label": "Только онлайн"},
]

# Rules text
RULES_TEXT = """📋 <b>Правила и ограничения</b>

Работая на платформе NutriMatch, вы соглашаетесь:

1️⃣ <b>Квалификация</b>
• Иметь профильное образование или сертификацию
• Предоставить документы для верификации

2️⃣ <b>Этика</b>
• Не давать медицинских диагнозов
• Направлять к врачу при необходимости
• Соблюдать конфиденциальность клиентов

3️⃣ <b>Качество услуг</b>
• Проводить консультации вовремя
• Предупреждать об отменах за 24 часа
• Отвечать на сообщения в течение 24 часов

4️⃣ <b>Финансы</b>
• Комиссия платформы: 15%
• Выплаты: еженедельно

5️⃣ <b>Отмена бронирования</b>
• Клиент может отменить за 24+ часа: полный возврат
• Отмена менее чем за 24 часа: 50% возврат
• Неявка: без возврата"""


@router.callback_query(F.data.in_({CB_CREATE_PROFILE, CB_UPDATE_PROFILE}))
async def start_profile_flow(callback: CallbackQuery, state: FSMContext):
    """Start profile creation/update flow."""
    await callback.answer()
    
    # Initialize profile data in state
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    
    # Pre-fill with existing data if updating
    profile_data = {
        "full_name": nutritionist.get("profile", {}).get("full_name", callback.from_user.full_name),
        "photo_url": nutritionist.get("profile", {}).get("photo_url"),
        "bio": nutritionist.get("bio"),
        "specializations": nutritionist.get("specializations", []),
        "tags": nutritionist.get("tags", []),
    }
    
    await state.update_data(profile_draft=profile_data)
    await state.set_state(ProfileStates.waiting_full_name)
    
    text = (
        "📝 <b>Создание профиля нутрициолога</b>\n\n"
        "Шаг 1 из 6: Введите ваше полное имя\n\n"
        f"Текущее: <b>{profile_data['full_name']}</b>\n\n"
        "Отправьте новое имя или нажмите /skip для сохранения текущего."
    )
    
    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
    )


@router.message(ProfileStates.waiting_full_name)
async def process_full_name(message: Message, state: FSMContext):
    """Process full name input."""
    text = message.text.strip() if message.text else ""
    
    if text.lower() == "/skip":
        # Keep existing name
        pass
    elif len(text) < 2:
        await message.answer("⚠️ Имя слишком короткое. Введите полное имя:")
        return
    elif len(text) > 100:
        await message.answer("⚠️ Имя слишком длинное. Максимум 100 символов:")
        return
    else:
        data = await state.get_data()
        profile_draft = data.get("profile_draft", {})
        profile_draft["full_name"] = text
        await state.update_data(profile_draft=profile_draft)
    
    # Move to photo step
    await state.set_state(ProfileStates.waiting_photo)
    
    await message.answer(
        text=(
            "📸 <b>Шаг 2 из 6: Фото профиля</b>\n\n"
            "Отправьте фотографию для вашего профиля.\n"
            "Рекомендуется: качественное фото в профессиональном стиле."
        ),
        reply_markup=get_skip_keyboard(CB_SKIP_PHOTO),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_SKIP_PHOTO, ProfileStates.waiting_photo)
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    """Skip photo upload."""
    await callback.answer()
    await move_to_bio_step(callback.message, state, is_callback=True)


@router.message(ProfileStates.waiting_photo, F.photo)
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    """Process photo upload."""
    # Get largest photo
    photo = message.photo[-1]
    
    # Download photo via Telegram API
    try:
        file = await bot.get_file(photo.file_id)
        photo_bytes = await bot.download_file(file.file_path)
        
        # Get nutritionist ID
        data = await state.get_data()
        nutritionist = data.get("nutritionist", {})
        nutritionist_id = nutritionist.get("nutritionist_id")
        
        if nutritionist_id:
            # Upload to backend
            api = get_api_client()
            response = await api.upload_photo(
                nutritionist_id=nutritionist_id,
                photo_bytes=photo_bytes.read(),
                filename=f"{photo.file_id}.jpg",
            )
            
            if response.success:
                photo_url = response.data.get("photo_url")
                profile_draft = data.get("profile_draft", {})
                profile_draft["photo_url"] = photo_url
                await state.update_data(profile_draft=profile_draft)
                await message.answer("✅ Фото загружено!")
            else:
                await message.answer(
                    f"⚠️ Не удалось загрузить фото: {response.error}\n"
                    "Продолжаем без фото."
                )
        else:
            # Store file_id for later upload
            profile_draft = data.get("profile_draft", {})
            profile_draft["photo_file_id"] = photo.file_id
            await state.update_data(profile_draft=profile_draft)
            await message.answer("✅ Фото сохранено!")
        
    except Exception as e:
        logger.error(f"Photo processing error: {e}")
        await message.answer("⚠️ Ошибка при обработке фото. Продолжаем без фото.")
    
    await move_to_bio_step(message, state, is_callback=False)


@router.message(ProfileStates.waiting_photo)
async def process_photo_invalid(message: Message):
    """Handle non-photo input in photo step."""
    await message.answer(
        "⚠️ Пожалуйста, отправьте фотографию или нажмите «Пропустить».",
        reply_markup=get_skip_keyboard(CB_SKIP_PHOTO),
    )


async def move_to_bio_step(message: Message, state: FSMContext, is_callback: bool = False):
    """Move to bio input step."""
    await state.set_state(ProfileStates.waiting_bio)
    
    data = await state.get_data()
    profile_draft = data.get("profile_draft", {})
    current_bio = profile_draft.get("bio", "")
    
    text = (
        "📝 <b>Шаг 3 из 6: О себе</b>\n\n"
        "Расскажите о себе и своём опыте (до 300 символов).\n"
        "Это описание увидят клиенты.\n\n"
    )
    
    if current_bio:
        text += f"Текущее описание:\n<i>{current_bio}</i>\n\n"
    
    if is_callback:
        await message.edit_text(
            text=text,
            reply_markup=get_skip_keyboard(CB_SKIP_BIO),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            text=text,
            reply_markup=get_skip_keyboard(CB_SKIP_BIO),
            parse_mode="HTML",
        )


@router.callback_query(F.data == CB_SKIP_BIO, ProfileStates.waiting_bio)
async def skip_bio(callback: CallbackQuery, state: FSMContext):
    """Skip bio input."""
    await callback.answer()
    await move_to_specializations_step(callback.message, state)


@router.message(ProfileStates.waiting_bio)
async def process_bio(message: Message, state: FSMContext):
    """Process bio input."""
    text = message.text.strip() if message.text else ""
    
    if len(text) > 300:
        await message.answer(
            f"⚠️ Текст слишком длинный ({len(text)} символов). Максимум 300.\n"
            "Сократите описание:"
        )
        return
    
    if text:
        data = await state.get_data()
        profile_draft = data.get("profile_draft", {})
        profile_draft["bio"] = text
        await state.update_data(profile_draft=profile_draft)
    
    await move_to_specializations_step(message, state)


async def move_to_specializations_step(message: Message, state: FSMContext):
    """Move to specializations selection."""
    await state.set_state(ProfileStates.selecting_specializations)
    
    data = await state.get_data()
    profile_draft = data.get("profile_draft", {})
    selected = profile_draft.get("specializations", [])
    
    text = (
        "🏷️ <b>Шаг 4 из 6: Специализации</b>\n\n"
        "Выберите ваши специализации (можно несколько).\n"
        "Это поможет клиентам найти вас.\n\n"
        f"Выбрано: {len(selected)}"
    )
    
    await message.answer(
        text=text,
        reply_markup=get_specializations_keyboard(SPECIALIZATIONS, selected),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith(CB_SPEC_PREFIX), ProfileStates.selecting_specializations)
async def toggle_specialization(callback: CallbackQuery, state: FSMContext):
    """Toggle specialization selection."""
    await callback.answer()
    
    spec_id = callback.data.replace(CB_SPEC_PREFIX, "")
    
    data = await state.get_data()
    profile_draft = data.get("profile_draft", {})
    selected = profile_draft.get("specializations", [])
    
    if spec_id in selected:
        selected.remove(spec_id)
    else:
        selected.append(spec_id)
    
    profile_draft["specializations"] = selected
    await state.update_data(profile_draft=profile_draft)
    
    text = (
        "🏷️ <b>Шаг 4 из 6: Специализации</b>\n\n"
        "Выберите ваши специализации (можно несколько).\n\n"
        f"Выбрано: {len(selected)}"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_specializations_keyboard(SPECIALIZATIONS, selected),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_SPEC_DONE, ProfileStates.selecting_specializations)
async def specializations_done(callback: CallbackQuery, state: FSMContext):
    """Finish specializations selection."""
    await callback.answer()
    
    data = await state.get_data()
    profile_draft = data.get("profile_draft", {})
    selected = profile_draft.get("specializations", [])
    
    if not selected:
        await callback.answer("⚠️ Выберите хотя бы одну специализацию", show_alert=True)
        return
    
    # Move to tags
    await state.set_state(ProfileStates.selecting_tags)
    
    selected_tags = profile_draft.get("tags", [])
    
    text = (
        "🏷️ <b>Шаг 5 из 6: Теги (опционально)</b>\n\n"
        "Добавьте теги для более точного поиска.\n"
        "Это необязательный шаг.\n\n"
        f"Выбрано: {len(selected_tags)}"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_tags_keyboard(TAGS, selected_tags),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith(CB_TAG_PREFIX), ProfileStates.selecting_tags)
async def toggle_tag(callback: CallbackQuery, state: FSMContext):
    """Toggle tag selection."""
    await callback.answer()
    
    tag_id = callback.data.replace(CB_TAG_PREFIX, "")
    
    data = await state.get_data()
    profile_draft = data.get("profile_draft", {})
    selected = profile_draft.get("tags", [])
    
    if tag_id in selected:
        selected.remove(tag_id)
    else:
        selected.append(tag_id)
    
    profile_draft["tags"] = selected
    await state.update_data(profile_draft=profile_draft)
    
    text = (
        "🏷️ <b>Шаг 5 из 6: Теги (опционально)</b>\n\n"
        "Добавьте теги для более точного поиска.\n\n"
        f"Выбрано: {len(selected)}"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_tags_keyboard(TAGS, selected),
        parse_mode="HTML",
    )


@router.callback_query(F.data.in_({CB_TAG_DONE, CB_SKIP_TAGS}), ProfileStates.selecting_tags)
async def tags_done(callback: CallbackQuery, state: FSMContext):
    """Finish tags selection."""
    await callback.answer()
    
    # Move to rules confirmation
    await state.set_state(ProfileStates.confirming_rules)
    
    await callback.message.edit_text(
        text=RULES_TEXT,
        reply_markup=get_confirm_rules_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_CONFIRM_RULES, ProfileStates.confirming_rules)
async def confirm_rules(callback: CallbackQuery, state: FSMContext):
    """Confirm rules acceptance."""
    await callback.answer()
    
    # Move to final confirmation
    await state.set_state(ProfileStates.confirming_submission)
    
    data = await state.get_data()
    profile_draft = data.get("profile_draft", {})
    
    # Build summary
    full_name = profile_draft.get("full_name", "Не указано")
    bio = profile_draft.get("bio", "Не указано")
    specs = profile_draft.get("specializations", [])
    tags = profile_draft.get("tags", [])
    has_photo = bool(profile_draft.get("photo_url") or profile_draft.get("photo_file_id"))
    
    # Get labels for specs and tags
    spec_labels = [s["label"] for s in SPECIALIZATIONS if s["id"] in specs]
    tag_labels = [t["label"] for t in TAGS if t["id"] in tags]
    
    text = (
        "✅ <b>Шаг 6 из 6: Проверка</b>\n\n"
        f"<b>Имя:</b> {full_name}\n"
        f"<b>Фото:</b> {'✅ Загружено' if has_photo else '❌ Не загружено'}\n"
        f"<b>О себе:</b> {bio[:100]}{'...' if len(bio) > 100 else ''}\n\n"
        f"<b>Специализации:</b>\n• " + "\n• ".join(spec_labels) + "\n\n"
    )
    
    if tag_labels:
        text += f"<b>Теги:</b>\n• " + "\n• ".join(tag_labels) + "\n\n"
    
    text += (
        "✓ Правила приняты\n\n"
        "Отправить профиль на модерацию?"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_submit_profile_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == CB_SUBMIT_PROFILE, ProfileStates.confirming_submission)
async def submit_profile(callback: CallbackQuery, state: FSMContext):
    """Submit profile for moderation."""
    await callback.answer("Отправляем...")
    
    data = await state.get_data()
    profile_draft = data.get("profile_draft", {})
    telegram_user_id = data.get("telegram_user_id", callback.from_user.id)
    
    # Submit to backend
    api = get_api_client()
    response = await api.upsert_nutritionist(
        telegram_user_id=telegram_user_id,
        full_name=profile_draft.get("full_name", callback.from_user.full_name),
        photo_url=profile_draft.get("photo_url"),
        bio=profile_draft.get("bio"),
        specializations=profile_draft.get("specializations", []),
        tags=profile_draft.get("tags", []),
        submit_for_verification=True,
    )
    
    if response.success:
        nutritionist = response.data.get("nutritionist")
        await state.update_data(nutritionist=nutritionist, profile_draft=None)
        await state.set_state(None)
        
        text = (
            "🎉 <b>Профиль отправлен на модерацию!</b>\n\n"
            "Мы проверим ваши данные в течение 24-48 часов.\n"
            "Вы получите уведомление о результате.\n\n"
            "А пока вы можете:\n"
            "• Добавить услуги\n"
            "• Подключить календарь"
        )
        
        await callback.message.edit_text(
            text=text,
            reply_markup=get_nutritionist_menu_keyboard(has_profile=True),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            text=f"❌ Ошибка: {response.error}\n\nПопробуйте ещё раз.",
            reply_markup=get_nutritionist_menu_keyboard(has_profile=True),
            parse_mode="HTML",
        )


@router.callback_query(F.data == CB_CANCEL_PROFILE)
async def cancel_profile(callback: CallbackQuery, state: FSMContext):
    """Cancel profile creation."""
    await callback.answer("Отменено")
    
    # Clear FSM state but keep user data
    data = await state.get_data()
    await state.set_state(None)
    await state.update_data(profile_draft=None)
    
    nutritionist = data.get("nutritionist")
    has_profile = nutritionist is not None
    
    await callback.message.edit_text(
        text="❌ Создание профиля отменено.",
        reply_markup=get_nutritionist_menu_keyboard(has_profile),
    )

