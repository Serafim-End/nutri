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
    get_document_type_keyboard,
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
    CB_DOC_TYPE_DIPLOMA,
    CB_DOC_TYPE_CERTIFICATE,
    CB_DOC_TYPE_OTHER,
    CB_DOC_DONE,
    CB_DOC_SKIP,
)


logger = logging.getLogger(__name__)
router = Router(name="profile")

# Static specializations (same as client goals)
SPECIALIZATIONS = [
    {"id": "weight_loss", "label": "Снижение веса"},
    {"id": "muscle_gain", "label": "Набор массы"},
    {"id": "better_nutrition", "label": "Здоровое питание"},
    {"id": "gut_health", "label": "Здоровье ЖКТ"},
    {"id": "sports_nutrition", "label": "Спортивное питание"},
    {"id": "pregnancy", "label": "Питание при беременности/кормлении"},
    {"id": "pediatric_nutrition", "label": "Детское питание (работа с родителями)"},
    {"id": "other", "label": "Другое"},
]

# Static tags
TAGS = [
    {"id": "vegetarian", "label": "Вегетарианство"},
    {"id": "vegan", "label": "Веганство"},
    {"id": "allergy", "label": "Аллергия/непереносимость"},
    {"id": "online_only", "label": "Только онлайн"},
]

# Rules text
RULES_TEXT = """📋 <b>Правила и ограничения</b>

Работая на платформе NutriMatch, вы соглашаетесь:

1️⃣ <b>Квалификация</b>
➖ Иметь профильное образование или сертификацию
➖ Предоставить документы для верификации

2️⃣ <b>Этика</b>
<b>Специалист обязуется:</b>
➖ Работать исключительно в рамках своей компетенции
➖ Опираться на принципы доказательной медицины и актуальные научные данные
➖ Чётко разграничивать нутрициологические рекомендации и медицинскую помощь
➖ Действовать в интересах клиента, уважая его границы и решения
➖ Соблюдать конфиденциальность и бережно обращаться с персональными данными
➖ Если в ходе работы специалист замечает симптомы или жалобы, выходящие за рамки нутрициологической поддержки, он корректно и бережно рекомендует клиенту обратиться к врачу для дополнительной оценки.

3️⃣ <b>Качество услуг</b>
➖ Проводить консультации вовремя
➖ Предупреждать об отменах за 12 часов
➖ Отвечать на сообщения в течение 24 часов

4️⃣ <b>Финансы</b>
➖ Комиссия платформы: 15%
➖ Выплаты: еженедельно

5️⃣ <b>Отмена бронирования</b>
➖ Клиент может отменить за 24+ часа: полный возврат
➖ Отмена менее чем за 24 часа: 50% возврат
➖ Неявка: без возврата

🔴В рамках работы на платформе запрещается:
➖ Назначать анализы
➖ Запрашивать анализы клиента для интерпретации или «расшифровки»
➖ Ставить медицинские диагнозы или делать выводы о состоянии здоровья
➖ Назначать или рекомендовать БАДы или лекарственные препараты
➖ Отменять или корректировать назначения врача
➖ Использовать детоксы, чистки, голодания и любые методы «очищения организма»
➖ Применять псевдонаучные практики
➖ Давать гарантии результата или обещания «лечения»

🔴При выявлении нарушений этических и профессиональных стандартов платформа оставляет за собой право:
➖ Приостановить доступ к платформе
➖ Отказать в верификации профиля
➖ Удалить профиль без компенсации
➖ Ограничить повторную регистрацию"""


@router.callback_query(F.data.in_({CB_CREATE_PROFILE, CB_UPDATE_PROFILE}))
async def start_profile_flow(callback: CallbackQuery, state: FSMContext):
    """Start profile creation/update flow."""
    await callback.answer()
    
    # Initialize profile data in state
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")

    if nutritionist_id:
        api = get_api_client()
        response = await api.get_nutritionist_dashboard(nutritionist_id)
        if response.success and response.data:
            nutritionist = response.data.get("nutritionist", nutritionist)
            await state.update_data(nutritionist=nutritionist)
    
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
        "Шаг 1 из 7: Введите ваше полное имя\n\n"
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
            "📸 <b>Шаг 2 из 7: Фото профиля</b>\n\n"
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
        "📝 <b>Шаг 3 из 7: О себе</b>\n\n"
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
        "🏷️ <b>Шаг 4 из 7: Специализации</b>\n\n"
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
        "🏷️ <b>Шаг 4 из 7: Специализации</b>\n\n"
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
        "🏷️ <b>Шаг 5 из 7: Теги (опционально)</b>\n\n"
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
        "🏷️ <b>Шаг 5 из 7: Теги (опционально)</b>\n\n"
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

    data = await state.get_data()
    profile_draft = data.get("profile_draft", {})
    telegram_user_id = data.get("telegram_user_id", callback.from_user.id)

    api = get_api_client()
    upsert_response = await api.upsert_nutritionist(
        telegram_user_id=telegram_user_id,
        full_name=profile_draft.get("full_name", callback.from_user.full_name),
        photo_url=profile_draft.get("photo_url"),
        bio=profile_draft.get("bio"),
        specializations=profile_draft.get("specializations", []),
        tags=profile_draft.get("tags", []),
        submit_for_verification=False,
    )

    if not upsert_response.success:
        await callback.message.edit_text(
            text=f"❌ Ошибка сохранения профиля: {upsert_response.error}\n\nПопробуйте ещё раз.",
            reply_markup=get_nutritionist_menu_keyboard(has_profile=False),
        )
        return

    nutritionist = upsert_response.data.get("nutritionist") if upsert_response.data else None
    await state.update_data(nutritionist=nutritionist)

    # Move to documents step
    await state.set_state(ProfileStates.selecting_document_type)
    await state.update_data(current_doc_type=None, uploaded_docs=[])

    await callback.message.edit_text(
        text=(
            "📄 <b>Шаг 6 из 7: Документы</b>\n\n"
            "Загрузите диплом и/или сертификаты.\n"
            "Поддерживаются: PDF, JPG, PNG.\n"
            "Этот шаг необязателен.\n\n"
            "Выберите тип документа и отправьте файл."
        ),
        reply_markup=get_document_type_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(
    F.data.in_({CB_DOC_TYPE_DIPLOMA, CB_DOC_TYPE_CERTIFICATE, CB_DOC_TYPE_OTHER}),
    ProfileStates.selecting_document_type,
)
async def select_document_type(callback: CallbackQuery, state: FSMContext):
    """Select document type and prompt for upload."""
    await callback.answer()

    if callback.data == CB_DOC_TYPE_DIPLOMA:
        doc_type = "diploma"
        label = "Диплом"
    elif callback.data == CB_DOC_TYPE_CERTIFICATE:
        doc_type = "certificate"
        label = "Сертификат"
    else:
        doc_type = "other"
        label = "Другое"

    await state.update_data(current_doc_type=doc_type)
    await state.set_state(ProfileStates.waiting_document_upload)

    await callback.message.edit_text(
        text=(
            f"📎 <b>Тип документа:</b> {label}\n\n"
            "Отправьте файл (PDF/JPG/PNG).\n"
            "Можно отправить фото документа."
        ),
        parse_mode="HTML",
    )


@router.message(ProfileStates.waiting_document_upload, F.document)
async def process_document_file(message: Message, state: FSMContext, bot: Bot):
    """Handle document file upload."""
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    doc_type = data.get("current_doc_type") or "other"

    if not nutritionist_id:
        await message.answer("❌ Профиль не найден.")
        return

    document = message.document
    try:
        file = await bot.get_file(document.file_id)
        file_bytes = await bot.download_file(file.file_path)
        filename = document.file_name or file.file_path.split("/")[-1] or "document"

        api = get_api_client()
        response = await api.upload_document(
            nutritionist_id=nutritionist_id,
            file_bytes=file_bytes.read(),
            filename=filename,
            document_type=doc_type,
        )

        if response.success:
            uploaded_docs = data.get("uploaded_docs", [])
            doc = response.data.get("document") if response.data else None
            if doc:
                uploaded_docs.append(doc)
            await state.update_data(uploaded_docs=uploaded_docs, current_doc_type=None)
            await state.set_state(ProfileStates.selecting_document_type)
            await message.answer(
                text=(
                    "✅ Документ загружен.\n"
                    f"Загружено: {len(uploaded_docs)}"
                ),
                reply_markup=get_document_type_keyboard(),
            )
        else:
            await message.answer(f"❌ Ошибка загрузки: {response.error}")
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        await message.answer("❌ Не удалось загрузить документ. Попробуйте ещё раз.")


@router.message(ProfileStates.waiting_document_upload, F.photo)
async def process_document_photo(message: Message, state: FSMContext, bot: Bot):
    """Handle document photo upload."""
    data = await state.get_data()
    nutritionist = data.get("nutritionist", {})
    nutritionist_id = nutritionist.get("nutritionist_id")
    doc_type = data.get("current_doc_type") or "other"

    if not nutritionist_id:
        await message.answer("❌ Профиль не найден.")
        return

    photo = message.photo[-1]
    try:
        file = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file.file_path)
        filename = file.file_path.split("/")[-1] or f"{photo.file_id}.jpg"

        api = get_api_client()
        response = await api.upload_document(
            nutritionist_id=nutritionist_id,
            file_bytes=file_bytes.read(),
            filename=filename,
            document_type=doc_type,
        )

        if response.success:
            uploaded_docs = data.get("uploaded_docs", [])
            doc = response.data.get("document") if response.data else None
            if doc:
                uploaded_docs.append(doc)
            await state.update_data(uploaded_docs=uploaded_docs, current_doc_type=None)
            await state.set_state(ProfileStates.selecting_document_type)
            await message.answer(
                text=(
                    "✅ Документ загружен.\n"
                    f"Загружено: {len(uploaded_docs)}"
                ),
                reply_markup=get_document_type_keyboard(),
            )
        else:
            await message.answer(f"❌ Ошибка загрузки: {response.error}")
    except Exception as e:
        logger.error(f"Document photo upload error: {e}")
        await message.answer("❌ Не удалось загрузить документ. Попробуйте ещё раз.")


@router.message(ProfileStates.waiting_document_upload)
async def process_document_invalid(message: Message):
    await message.answer("⚠️ Пожалуйста, отправьте файл или фото документа.")


@router.callback_query(F.data == CB_DOC_DONE, ProfileStates.selecting_document_type)
async def documents_done(callback: CallbackQuery, state: FSMContext):
    """Finish document upload and move to final review."""
    await callback.answer()
    data = await state.get_data()
    uploaded_docs = data.get("uploaded_docs", [])

    await show_submission_summary(callback.message, state, is_callback=True)


@router.callback_query(F.data == CB_DOC_SKIP, ProfileStates.selecting_document_type)
async def documents_skip(callback: CallbackQuery, state: FSMContext):
    """Skip document upload and move to final review."""
    await callback.answer()
    await show_submission_summary(callback.message, state, is_callback=True)


async def show_submission_summary(message: Message, state: FSMContext, is_callback: bool = False):
    """Show final summary before submission."""
    await state.set_state(ProfileStates.confirming_submission)

    data = await state.get_data()
    profile_draft = data.get("profile_draft", {})
    uploaded_docs = data.get("uploaded_docs", [])

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
        "✅ <b>Шаг 7 из 7: Проверка</b>\n\n"
        f"<b>Имя:</b> {full_name}\n"
        f"<b>Фото:</b> {'✅ Загружено' if has_photo else '❌ Не загружено'}\n"
        f"<b>Документы:</b> {len(uploaded_docs)}\n"
        f"<b>О себе:</b> {bio[:100]}{'...' if len(bio) > 100 else ''}\n\n"
        f"<b>Специализации:</b>\n• " + "\n• ".join(spec_labels) + "\n\n"
    )

    if tag_labels:
        text += f"<b>Теги:</b>\n• " + "\n• ".join(tag_labels) + "\n\n"

    text += (
        "✓ Правила приняты\n\n"
        "Отправить профиль на модерацию?"
    )

    if is_callback:
        await message.edit_text(
            text=text,
            reply_markup=get_submit_profile_keyboard(),
            parse_mode="HTML",
        )
    else:
        await message.answer(
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
        await state.update_data(
            nutritionist=nutritionist,
            profile_draft=None,
            uploaded_docs=None,
            current_doc_type=None,
        )
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
