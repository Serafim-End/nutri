"""
Bot Texts - Single Source of Truth
All messages, button labels, and dynamic templates for the nutritionist bot.
Organized by screen/feature according to UX_MAP_NUTRITIONIST.md.
"""

# ==========================================
# 1. Start/Welcome Screen
# ==========================================

START_WELCOME = "👋 Привет, {user_name}!\n\nДобро пожаловать в NutriMatch — сервис подбора нутрициологов.\n\n"
START_ROLE_NUTRITIONIST = "🩺 Вы зарегистрированы как нутрициолог.\n\n"
START_ROLE_ADMIN = "👑 Вы администратор.\n\n"
START_SELECT_ACTION = "Выберите действие:"

# ==========================================
# 2. Main Menu
# ==========================================

MAIN_MENU_WELCOME = "👋 NutriMatch — сервис подбора нутрициологов\n\n"
MAIN_MENU_ROLE_NUTRITIONIST = "🩺 Вы зарегистрированы как нутрициолог.\n\n"
MAIN_MENU_SELECT_ACTION = "Выберите действие:"

# Button labels
BTN_OPEN_WEBAPP = "🍎 Открыть мини-приложение"
BTN_FOR_NUTRITIONISTS = "👩‍⚕️ Для нутрициологов"
BTN_BACK = "◀️ Назад"

# ==========================================
# 3. Nutritionist Menu
# ==========================================

NUTRITIONIST_MENU_TITLE = "👩‍⚕️ <b>Раздел для нутрициологов</b>\n\n"
NUTRITIONIST_MENU_PROFILE_STATUS = "Ваш профиль: {status_text}\n\n"
NUTRITIONIST_MENU_NO_PROFILE = (
    "Здесь вы можете создать профиль нутрициолога, "
    "управлять своими услугами и отслеживать статистику.\n\n"
)
NUTRITIONIST_MENU_SELECT_ACTION = "Выберите действие:"

# Profile status labels
PROFILE_STATUS_DRAFT = "📝 Черновик"
PROFILE_STATUS_PENDING = "⏳ На модерации"
PROFILE_STATUS_APPROVED = "✅ Подтверждён"
PROFILE_STATUS_REJECTED = "❌ Отклонён"
PROFILE_STATUS_NEEDS_UPDATE = "⚠️ Требуются изменения"

# Button labels
BTN_I_AM_NUTRITIONIST = "✨ Я нутрициолог"
BTN_CREATE_PROFILE = "📝 Создать профиль"
BTN_UPDATE_PROFILE = "✏️ Обновить профиль"
BTN_PERSONAL_CABINET = "🏠 Личный кабинет"

# Intent registration message
INTENT_REGISTERED_TITLE = "✨ <b>Отлично!</b>\n\n"
INTENT_REGISTERED_MESSAGE = (
    "Вы отметили, что являетесь нутрициологом.\n\n"
    "Чтобы начать принимать клиентов, необходимо:\n"
    "1️⃣ Заполнить профиль\n"
    "2️⃣ Добавить услуги\n"
    "3️⃣ Подключить календарь\n"
    "4️⃣ Пройти модерацию\n\n"
    "Начнём с создания профиля?"
)

# ==========================================
# 4. Profile Creation Flow
# ==========================================

# Step 1: Full Name
PROFILE_STEP1_TITLE = "📝 <b>Создание профиля нутрициолога</b>\n\n"
PROFILE_STEP1_INSTRUCTION = "Шаг 1 из 6: Введите ваше полное имя\n\n"
PROFILE_STEP1_CURRENT = "Текущее: <b>{full_name}</b>\n\n"
PROFILE_STEP1_HINT = "Отправьте новое имя или нажмите /skip для сохранения текущего."

# Step 1 validation
PROFILE_STEP1_NAME_TOO_SHORT = "⚠️ Имя слишком короткое. Введите полное имя:"
PROFILE_STEP1_NAME_TOO_LONG = "⚠️ Имя слишком длинное. Максимум 100 символов:"

# Step 2: Photo
PROFILE_STEP2_TITLE = "📸 <b>Шаг 2 из 6: Фото профиля</b>\n\n"
PROFILE_STEP2_INSTRUCTION = (
    "Отправьте фотографию для вашего профиля.\n"
    "Рекомендуется: качественное фото в профессиональном стиле."
)
PROFILE_STEP2_PHOTO_UPLOADED = "✅ Фото загружено!"
PROFILE_STEP2_PHOTO_SAVED = "✅ Фото сохранено!"
PROFILE_STEP2_UPLOAD_ERROR = "⚠️ Не удалось загрузить фото: {error}\nПродолжаем без фото."
PROFILE_STEP2_PROCESSING_ERROR = "⚠️ Ошибка при обработке фото. Продолжаем без фото."
PROFILE_STEP2_INVALID_INPUT = "⚠️ Пожалуйста, отправьте фотографию или нажмите «Пропустить»."

# Step 3: Bio
PROFILE_STEP3_TITLE = "📝 <b>Шаг 3 из 6: О себе</b>\n\n"
PROFILE_STEP3_INSTRUCTION = (
    "Расскажите о себе и своём опыте (до 300 символов).\n"
    "Это описание увидят клиенты.\n\n"
)
PROFILE_STEP3_CURRENT = "Текущее описание:\n<i>{current_bio}</i>\n\n"
PROFILE_STEP3_TOO_LONG = (
    "⚠️ Текст слишком длинный ({length} символов). Максимум 300.\n"
    "Сократите описание:"
)

# Step 4: Specializations
PROFILE_STEP4_TITLE = "🏷️ <b>Шаг 4 из 6: Специализации</b>\n\n"
PROFILE_STEP4_INSTRUCTION = (
    "Выберите ваши специализации (можно несколько).\n"
    "Это поможет клиентам найти вас.\n\n"
)
PROFILE_STEP4_SELECTED_COUNT = "Выбрано: {count}"
PROFILE_STEP4_REQUIRE_ONE = "⚠️ Выберите хотя бы одну специализацию"

# Specialization labels
SPEC_WEIGHT_MANAGEMENT = "Управление весом"
SPEC_SPORTS_NUTRITION = "Спортивное питание"
SPEC_GUT_HEALTH = "Здоровье ЖКТ"
SPEC_DIABETES = "Диабет"
SPEC_HORMONAL_HEALTH = "Гормональное здоровье"
SPEC_PEDIATRIC = "Детское питание"
SPEC_PREGNANCY = "Питание при беременности"
SPEC_EATING_DISORDERS = "Расстройства пищевого поведения"
SPEC_AUTOIMMUNE = "Аутоиммунные заболевания"
SPEC_PLANT_BASED = "Растительное питание"

# Step 5: Tags
PROFILE_STEP5_TITLE = "🏷️ <b>Шаг 5 из 6: Теги (опционально)</b>\n\n"
PROFILE_STEP5_INSTRUCTION = (
    "Добавьте теги для более точного поиска.\n"
    "Это необязательный шаг.\n\n"
)
PROFILE_STEP5_SELECTED_COUNT = "Выбрано: {count}"

# Tag labels
TAG_VEGETARIAN = "Вегетарианство"
TAG_VEGAN = "Веганство"
TAG_ALLERGY = "Аллергия/непереносимость"
TAG_ONLINE_ONLY = "Только онлайн"

# Step 6: Rules Confirmation
PROFILE_STEP6_RULES = """📋 <b>Правила и ограничения</b>

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

# Step 7: Final Confirmation
PROFILE_STEP7_TITLE = "✅ <b>Шаг 6 из 6: Проверка</b>\n\n"
PROFILE_STEP7_FIELD_NAME = "<b>Имя:</b> {full_name}\n"
PROFILE_STEP7_FIELD_PHOTO = "<b>Фото:</b> {status}\n"
PROFILE_STEP7_PHOTO_UPLOADED = "✅ Загружено"
PROFILE_STEP7_PHOTO_NOT_UPLOADED = "❌ Не загружено"
PROFILE_STEP7_FIELD_BIO = "<b>О себе:</b> {bio_preview}\n\n"
PROFILE_STEP7_FIELD_SPECS = "<b>Специализации:</b>\n• {specs_list}\n\n"
PROFILE_STEP7_FIELD_TAGS = "<b>Теги:</b>\n• {tags_list}\n\n"
PROFILE_STEP7_RULES_ACCEPTED = "✓ Правила приняты\n\n"
PROFILE_STEP7_CONFIRM = "Отправить профиль на модерацию?"

# Button labels
BTN_SKIP = "⏭️ Пропустить"
BTN_SPEC_DONE = "✓ Готово"
BTN_TAG_DONE = "✓ Готово"
BTN_TAG_SKIP = "⏭️ Пропустить"
BTN_CONFIRM_RULES = "✅ Принимаю правила"
BTN_SUBMIT_PROFILE = "📤 Отправить на модерацию"
BTN_EDIT_PROFILE = "◀️ Редактировать"
BTN_CANCEL = "❌ Отмена"

# Terminal: Profile Submitted
PROFILE_SUBMITTED_TITLE = "🎉 <b>Профиль отправлен на модерацию!</b>\n\n"
PROFILE_SUBMITTED_MESSAGE = (
    "Мы проверим ваши данные в течение 24-48 часов.\n"
    "Вы получите уведомление о результате.\n\n"
    "А пока вы можете:\n"
    "• Добавить услуги\n"
    "• Подключить календарь"
)
PROFILE_SUBMITTED_ERROR = "❌ Ошибка: {error}\n\nПопробуйте ещё раз."
PROFILE_CANCELED = "❌ Создание профиля отменено."
PROFILE_SUBMIT_LOADING = "Отправляем..."

# ==========================================
# 5. Personal Cabinet
# ==========================================

CABINET_TITLE = "🏠 <b>Личный кабинет</b>\n\n"
CABINET_NAME = "👤 {full_name}\n\n"
CABINET_STATS_TITLE = "📊 <b>Статистика:</b>\n"
CABINET_STATS_TOTAL_BOOKINGS = "• Всего записей: {count}\n"
CABINET_STATS_COMPLETED = "• Проведено: {count}\n"
CABINET_STATS_EARNINGS = "• Заработано: {earnings:,}₽\n\n"
CABINET_SELECT_SECTION = "Выберите раздел:"
CABINET_PROFILE_NOT_FOUND = "❌ Профиль нутрициолога не найден.\nСначала создайте профиль."
CABINET_LOAD_ERROR = (
    "🏠 <b>Личный кабинет</b>\n\n"
    "Не удалось загрузить данные.\n"
    "Попробуйте позже."
)

# Button labels
BTN_SCHEDULE = "🕒 Расписание"
BTN_MY_BOOKINGS = "📋 Мои бронирования"
BTN_MY_SERVICES = "📋 Мои услуги"
BTN_CALENDAR = "📅 Календарь"
BTN_REVIEWS = "⭐ Отзывы"
BTN_STATISTICS = "📊 Статистика"
BTN_SETTINGS = "⚙️ Настройки"
BTN_SUPPORT = "💬 Поддержка"
BTN_BACK_TO_CABINET = "◀️ В кабинет"

# ==========================================
# 6. Services List
# ==========================================

SERVICES_TITLE = "📋 <b>Мои услуги</b>\n\n"
SERVICES_EMPTY = (
    "У вас пока нет услуг.\n"
    "Добавьте первую услугу, чтобы клиенты могли записаться."
)
SERVICES_COUNT = "Всего услуг: {count}\n"
SERVICES_INSTRUCTION = "Нажмите на услугу для редактирования."
SERVICES_PROFILE_NOT_FOUND = "❌ Профиль не найден. Сначала создайте профиль."
SERVICES_LOAD_ERROR = "❌ Ошибка загрузки услуг: {error}"

# Button labels
BTN_ADD_SERVICE = "➕ Добавить услугу"
BTN_BACK_TO_SERVICES = "◀️ Назад к услугам"

# Service item format
SERVICE_ITEM_ACTIVE = "✅ {title} — {price}₽"
SERVICE_ITEM_INACTIVE = "⏸️ {title} — {price}₽"

# ==========================================
# 7. Service Creation Flow
# ==========================================

# Step 1: Title
SERVICE_STEP1_TITLE = "➕ <b>Создание услуги</b>\n\n"
SERVICE_STEP1_INSTRUCTION = "Шаг 1 из 4: Название услуги\n\n"
SERVICE_STEP1_HINT = "Введите название услуги (например, «Консультация по питанию»):"

# Step 1 validation
SERVICE_STEP1_TOO_SHORT = "⚠️ Название слишком короткое. Минимум 3 символа:"
SERVICE_STEP1_TOO_LONG = "⚠️ Название слишком длинное. Максимум 100 символов:"

# Step 2: Description
SERVICE_STEP2_TITLE = "📝 <b>Шаг 2 из 4: Описание (опционально)</b>\n\n"
SERVICE_STEP2_INSTRUCTION = (
    "Опишите, что включает услуга.\n"
    "Это поможет клиентам понять, чего ожидать."
)
SERVICE_STEP2_TOO_LONG = "⚠️ Описание слишком длинное. Максимум 500 символов:"

# Step 3: Duration
SERVICE_STEP3_TITLE = "⏱️ <b>Шаг 3 из 4: Длительность</b>\n\n"
SERVICE_STEP3_INSTRUCTION = "Введите длительность консультации в минутах.\n\n"
SERVICE_STEP3_EXAMPLES = "Примеры: 30, 45, 60, 90"
SERVICE_STEP3_TOO_SHORT = "⚠️ Минимальная длительность — 15 минут:"
SERVICE_STEP3_TOO_LONG = "⚠️ Максимальная длительность — 240 минут (4 часа):"
SERVICE_STEP3_INVALID = "⚠️ Введите число минут (например, 60):"

# Step 4: Price
SERVICE_STEP4_TITLE = "💰 <b>Шаг 4 из 4: Цена</b>\n\n"
SERVICE_STEP4_INSTRUCTION = "Введите стоимость консультации в рублях.\n\n"
SERVICE_STEP4_EXAMPLES = "Примеры: 2000, 3500, 5000"
SERVICE_STEP4_TOO_LOW = "⚠️ Минимальная цена — 100₽:"
SERVICE_STEP4_TOO_HIGH = "⚠️ Максимальная цена — 100 000₽:"
SERVICE_STEP4_INVALID = "⚠️ Введите сумму в рублях (например, 3000):"

# Step 5: Confirmation
SERVICE_STEP5_TITLE = "✅ <b>Проверьте данные услуги</b>\n\n"
SERVICE_STEP5_FIELD_TITLE = "<b>Название:</b> {title}\n"
SERVICE_STEP5_FIELD_DESCRIPTION = "<b>Описание:</b> {description_preview}\n"
SERVICE_STEP5_FIELD_DURATION = "<b>Длительность:</b> {duration} мин\n"
SERVICE_STEP5_FIELD_PRICE = "<b>Цена:</b> {price:,}₽\n\n"
SERVICE_STEP5_CONFIRM = "Создать услугу?"

# Button labels
BTN_CREATE_SERVICE = "✅ Создать услугу"
BTN_CANCEL_SERVICE = "❌ Отмена"

# Terminal: Service Created
SERVICE_CREATED_TITLE = "🎉 <b>Услуга создана!</b>\n\n"
SERVICE_CREATED_DETAILS = "<b>{title}</b>\nЦена: {price:,}₽\n\n"
SERVICE_CREATED_MESSAGE = "Услуга доступна клиентам для записи."
SERVICE_CREATED_ERROR = "❌ Ошибка создания: {error}"
SERVICE_CREATED_LOADING = "Создаём..."
SERVICE_CANCELED = "❌ Создание услуги отменено."

# ==========================================
# 8. Service Details
# ==========================================

SERVICE_DETAILS_TITLE = "📋 <b>{title}</b>\n\n"
SERVICE_DETAILS_DESCRIPTION = "<b>Описание:</b> {description}\n"
SERVICE_DETAILS_DURATION = "<b>Длительность:</b> {duration} мин\n"
SERVICE_DETAILS_PRICE = "<b>Цена:</b> {price:,}₽\n"
SERVICE_DETAILS_STATUS = "<b>Статус:</b> {status}\n\n"
SERVICE_DETAILS_SELECT_ACTION = "Выберите действие:"
SERVICE_DETAILS_NOT_FOUND = "❌ Услуга не найдена."

# Service status labels
SERVICE_STATUS_ACTIVE = "✅ Активна"
SERVICE_STATUS_INACTIVE = "⏸️ Неактивна"

# Button labels
BTN_ACTIVATE_SERVICE = "✅ Активировать"
BTN_DEACTIVATE_SERVICE = "⏸️ Деактивировать"
BTN_DELETE_SERVICE = "🗑️ Удалить"

# Service toggle messages
SERVICE_TOGGLE_ACTIVATED = "активирована"
SERVICE_TOGGLE_DEACTIVATED = "деактивирована"
SERVICE_TOGGLE_ERROR = "Ошибка: {error}"

# ==========================================
# 9. Delete Service Confirmation
# ==========================================

DELETE_SERVICE_TITLE = "⚠️ <b>Удаление услуги</b>\n\n"
DELETE_SERVICE_WARNING = (
    "Вы уверены? Это действие нельзя отменить.\n"
    "Существующие записи на эту услугу сохранятся."
)

# Button labels
BTN_CONFIRM_DELETE = "✅ Да, удалить"
BTN_CANCEL_DELETE = "❌ Отмена"

# ==========================================
# 10. Service Deleted (Terminal)
# ==========================================

SERVICE_DELETED = "✅ Услуга удалена."
SERVICE_DELETE_ERROR = "❌ Ошибка удаления: {error}"
SERVICE_DELETE_LOADING = "Удаляем..."

# ==========================================
# 11. Schedule View
# ==========================================

SCHEDULE_TITLE = "🕒 <b>Расписание</b> (ближайшие 14 дней)\n\n"
SCHEDULE_EMPTY = (
    "У вас пока нет доступных слотов.\n\n"
    "Добавьте слоты, чтобы клиенты могли записаться на консультацию.\n\n"
    "<i>💡 Совет: добавьте несколько слотов на ближайшие дни, "
    "чтобы увеличить шансы на запись.</i>"
)
SCHEDULE_LOAD_ERROR = (
    "🕒 <b>Расписание</b>\n\n"
    "⚠️ Не удалось загрузить расписание.\n"
    "Попробуйте позже."
)
SCHEDULE_DATE_HEADER = "📅 <b>{date}</b>\n"
SCHEDULE_SLOT_FREE = "  • {time_range} (свободно)\n"
SCHEDULE_SLOT_HELD = "  • {time_range} (удерживается)\n"
SCHEDULE_SLOT_BOOKED = "  • {time_range} (забронировано)\n"
SCHEDULE_CALENDAR_CONNECTED = "📅 <i>Google Calendar подключён</i>\n"

# Button labels
BTN_ADD_SLOT = "➕ Добавить слот"
BTN_DELETE_SLOT = "❌ Удалить слот"
BTN_REFRESH_SCHEDULE = "🔄 Обновить"

# ==========================================
# 12. Add Slot Flow
# ==========================================

# Step 1: Date Selection
ADD_SLOT_STEP1_TITLE = "➕ <b>Добавить слот</b>\n\n"
ADD_SLOT_STEP1_INSTRUCTION = "Выберите дату для нового слота:"

# Step 2: Start Time
ADD_SLOT_STEP2_TITLE = "➕ <b>Добавить слот</b>\n\n"
ADD_SLOT_STEP2_DATE = "📅 Дата: {date}\n\n"
ADD_SLOT_STEP2_INSTRUCTION = "Введите время начала в формате <b>ЧЧ:ММ</b>\n(например: 10:00, 14:30)"
ADD_SLOT_STEP2_INVALID_FORMAT = (
    "⚠️ Неверный формат времени.\n\n"
    "Введите время в формате <b>ЧЧ:ММ</b> (например: 10:00, 14:30)"
)
ADD_SLOT_STEP2_NOT_FUTURE = (
    "⚠️ Время слота должно быть в будущем.\n\n"
    "Введите другое время:"
)

# Step 3: Duration
ADD_SLOT_STEP3_TITLE = "➕ <b>Добавить слот</b>\n\n"
ADD_SLOT_STEP3_DATE = "📅 Дата: {date}\n"
ADD_SLOT_STEP3_TIME = "🕒 Начало: {time}\n\n"
ADD_SLOT_STEP3_INSTRUCTION = "Выберите продолжительность:"

# Step 4: Confirmation
ADD_SLOT_STEP4_TITLE = "➕ <b>Добавить слот</b>\n\n"
ADD_SLOT_STEP4_CONFIRM = "Подтвердите создание слота:\n\n"
ADD_SLOT_STEP4_DATE = "📅 {date}\n"
ADD_SLOT_STEP4_TIME = "🕒 {time_range}\n"
ADD_SLOT_STEP4_DURATION = "⏱ {duration} минут\n\n"
ADD_SLOT_STEP4_QUESTION = "Всё верно?"

# Button labels
BTN_SLOT_DURATION_30 = "30 минут"
BTN_SLOT_DURATION_45 = "45 минут"
BTN_SLOT_DURATION_60 = "60 минут"
BTN_SLOT_DURATION_90 = "90 минут"
BTN_CONFIRM_SLOT = "✅ Добавить слот"

# Terminal: Slot Created
SLOT_CREATED_TITLE = "✅ <b>Слот создан!</b>\n\n"
SLOT_CREATED_DATE = "📅 {date}\n"
SLOT_CREATED_TIME = "🕒 {time_range}\n\n"
SLOT_CREATED_MESSAGE = "Клиенты теперь могут записаться на это время."
SLOT_CREATE_ERROR_TITLE = "❌ <b>Не удалось создать слот</b>\n\n"
SLOT_CREATE_ERROR_OVERLAP = "Этот слот пересекается с существующим. Выберите другое время."
SLOT_CREATE_ERROR_NOT_FUTURE = "Слот должен быть в будущем."
SLOT_CREATE_ERROR_GENERIC = "{error}\n\nПопробуйте ещё раз."

# ==========================================
# 13. Delete Slot Flow
# ==========================================

DELETE_SLOT_TITLE = "❌ <b>Удаление слота</b>\n\n"
DELETE_SLOT_INSTRUCTION = "Выберите слот для удаления:"
DELETE_SLOT_NO_FREE = (
    "Нет свободных слотов для удаления.\n\n"
    "<i>Удалить можно только свободные слоты. "
    "Забронированные слоты удалить нельзя.</i>"
)
DELETE_SLOT_LOAD_ERROR = "⚠️ Не удалось загрузить слоты."

# ==========================================
# 14. Slot Deleted (Terminal)
# ==========================================

SLOT_DELETED = "✅ <b>Слот удалён!</b>"
SLOT_DELETE_ERROR_TITLE = "❌ <b>Не удалось удалить слот</b>\n\n"
SLOT_DELETE_ERROR_BOOKED = "Этот слот уже забронирован и не может быть удалён."
SLOT_DELETE_ERROR_GENERIC = "{error}"

# ==========================================
# 15. Bookings List
# ==========================================

BOOKINGS_TITLE = "📋 <b>Мои бронирования</b>\n\n"
BOOKINGS_TITLE_PAGINATED = "📋 <b>Мои бронирования</b> ({start}-{end} из {total})\n\n"
BOOKINGS_EMPTY = (
    "Пока нет предстоящих бронирований.\n\n"
    "<i>Когда клиенты запишутся на консультацию, "
    "их записи появятся здесь.</i>"
)
BOOKINGS_LOAD_ERROR = (
    "📋 <b>Мои бронирования</b>\n\n"
    "⚠️ Не удалось загрузить бронирования.\n"
    "Попробуйте позже."
)
BOOKINGS_ITEM_DATE = "📅 {date}, {time_range}\n"
BOOKINGS_ITEM_CLIENT = "👤 {client_name}\n"
BOOKINGS_ITEM_SERVICE = "💼 {service_title}\n"
BOOKINGS_STATUS_PAID = "✅ Подтверждено"
BOOKINGS_STATUS_COMPLETED = "☑️ Завершено"

# Button labels
BTN_REFRESH_BOOKINGS = "🔄 Обновить"
BTN_BOOKINGS_PREV = "◀️ Назад"
BTN_BOOKINGS_NEXT = "Далее ▶️"

# ==========================================
# 16. Reviews List
# ==========================================

REVIEWS_TITLE = "⭐ <b>Отзывы</b>\n\n"
REVIEWS_TITLE_PAGINATED = "⭐ <b>Отзывы</b> ({start}-{end} из {total})\n\n"
REVIEWS_EMPTY = (
    "У вас пока нет отзывов.\n\n"
    "После проведения консультаций клиенты смогут оставлять отзывы.\n"
    "Хорошие отзывы повышают ваш рейтинг и видимость."
)
REVIEWS_UNAVAILABLE = (
    "⭐ <b>Отзывы</b>\n\n"
    "⚙️ Отзывы пока недоступны\n\n"
    "После проведения консультаций клиенты смогут оставлять отзывы.\n"
    "Они появятся здесь."
)
REVIEWS_ITEM_RATING = "{stars} <b>{client_name}</b>\n"
REVIEWS_ITEM_COMMENT = "<i>{comment_preview}</i>\n"
REVIEWS_ITEM_DATE = "<code>{date}</code>\n\n"

# Button labels
BTN_REVIEWS_PREV = "◀️ Назад"
BTN_REVIEWS_NEXT = "Далее ▶️"

# ==========================================
# 17. Statistics View
# ==========================================

STATISTICS_TITLE_30D = "📊 <b>Статистика за 30 дней</b>\n\n"
STATISTICS_INCOME = "💰 <b>Доход:</b> {income:,}₽\n"
STATISTICS_CONSULTATIONS = "📅 <b>Консультаций:</b> {count}\n"
STATISTICS_RATING = "⭐ <b>Средний рейтинг:</b> {rating:.1f}\n"
STATISTICS_CLIENTS = "👥 <b>Всего клиентов:</b> {count}\n\n"
STATISTICS_UPDATE_NOTE = "<i>Статистика обновляется ежедневно</i>"

STATISTICS_TITLE_SIMPLE = "📊 <b>Статистика</b>\n\n"
STATISTICS_TOTAL_BOOKINGS = "📅 <b>Всего записей:</b> {count}\n"
STATISTICS_COMPLETED = "✅ <b>Проведено:</b> {count}\n"
STATISTICS_EARNINGS = "💰 <b>Заработано:</b> {earnings:,}₽\n\n"
STATISTICS_COMING_SOON = "<i>Подробная статистика скоро будет доступна</i>"

STATISTICS_UNAVAILABLE = (
    "📊 <b>Статистика</b>\n\n"
    "Данные пока недоступны.\n"
    "Статистика появится после первых консультаций."
)
STATISTICS_PROFILE_NOT_FOUND = "❌ Профиль не найден."

# ==========================================
# 18. Calendar Settings
# ==========================================

CALENDAR_TITLE = "📅 <b>Календарь</b>\n\n"
CALENDAR_CONNECTED = (
    "✅ Google Calendar подключён\n"
    "📧 {email}\n\n"
    "<b>Как это работает:</b>\n"
    "• Ваши свободные слоты определяются автоматически\n"
    "• Мы смотрим на занятые события в вашем календаре\n"
    "• Свободные промежутки становятся доступны для записи\n\n"
    "Чтобы отключить календарь, напишите в поддержку."
)
CALENDAR_NOT_CONNECTED = (
    "❌ Google Calendar не подключён\n\n"
    "<b>Зачем подключать?</b>\n"
    "• Автоматическое определение свободных слотов\n"
    "• Синхронизация записей в ваш календарь\n"
    "• Никаких накладок в расписании\n\n"
    "Нажмите кнопку ниже для подключения."
)
CALENDAR_IN_DEVELOPMENT = (
    "⚙️ Функция в разработке\n\n"
    "Скоро здесь появится возможность:\n"
    "• Подключить Google Calendar\n"
    "• Автоматически синхронизировать расписание\n"
    "• Управлять доступными слотами"
)
CALENDAR_PROFILE_NOT_FOUND = "❌ Профиль не найден."

# Button labels
BTN_CONNECT_CALENDAR = "🔗 Подключить Google Calendar"

# ==========================================
# 19. Settings View
# ==========================================

SETTINGS_TITLE = "⚙️ <b>Настройки</b>\n\n"
SETTINGS_CANCELLATION_POLICY_TITLE = "<b>📋 Политика отмены бронирования</b>\n\n"
SETTINGS_CANCELLATION_POLICY = (
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

# ==========================================
# 20. Support Flow
# ==========================================

# Step 1: Message Input
SUPPORT_STEP1_TITLE = "💬 <b>Поддержка</b>\n\n"
SUPPORT_STEP1_INSTRUCTION = (
    "Опишите вашу проблему или вопрос.\n"
    "Мы ответим в течение 24 часов.\n\n"
    "Отправьте сообщение:"
)
SUPPORT_STEP1_EMPTY = "⚠️ Отправьте текстовое сообщение."
SUPPORT_STEP1_TOO_LONG = "⚠️ Сообщение слишком длинное. Максимум 1000 символов."

# Terminal: Message Sent
SUPPORT_SENT_TITLE = "✅ <b>Сообщение отправлено!</b>\n\n"
SUPPORT_SENT_MESSAGE = (
    "Спасибо за обращение.\n"
    "Мы ответим вам в ближайшее время."
)
SUPPORT_SENT_FALLBACK = (
    "✅ <b>Сообщение получено!</b>\n\n"
    "Мы свяжемся с вами в ближайшее время."
)
SUPPORT_CANCELED = "❌ Обращение в поддержку отменено."
SUPPORT_CANCEL_ALERT = "Отменено"

# ==========================================
# Error Messages (General)
# ==========================================

ERROR_GENERIC = "😔 Произошла ошибка. Попробуйте ещё раз или напишите /start\n\n<code>ID: {corr_id}</code>"
ERROR_GENERIC_ALERT = "😔 Ошибка (ID: {corr_id}). Попробуйте ещё раз."
ERROR_PROFILE_NOT_FOUND = "❌ Профиль не найден."
ERROR_LOAD_FAILED = "⚠️ Не удалось загрузить данные.\nПопробуйте позже."

# ==========================================
# Throttling
# ==========================================

THROTTLE_MESSAGE = "Слишком быстро, подождите..."

# ==========================================
# Date/Time Formatting
# ==========================================

# Russian month names (genitive case)
MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}

# Weekday abbreviations
WEEKDAYS_RU = {
    0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс",
}

# ==========================================
# Specializations Data
# ==========================================

SPECIALIZATIONS = [
    {"id": "weight_management", "label": SPEC_WEIGHT_MANAGEMENT},
    {"id": "sports_nutrition", "label": SPEC_SPORTS_NUTRITION},
    {"id": "gut_health", "label": SPEC_GUT_HEALTH},
    {"id": "diabetes", "label": SPEC_DIABETES},
    {"id": "hormonal_health", "label": SPEC_HORMONAL_HEALTH},
    {"id": "pediatric", "label": SPEC_PEDIATRIC},
    {"id": "pregnancy", "label": SPEC_PREGNANCY},
    {"id": "eating_disorders", "label": SPEC_EATING_DISORDERS},
    {"id": "autoimmune", "label": SPEC_AUTOIMMUNE},
    {"id": "plant_based", "label": SPEC_PLANT_BASED},
]

# ==========================================
# Tags Data
# ==========================================

TAGS = [
    {"id": "vegetarian", "label": TAG_VEGETARIAN},
    {"id": "vegan", "label": TAG_VEGAN},
    {"id": "allergy", "label": TAG_ALLERGY},
    {"id": "online_only", "label": TAG_ONLINE_ONLY},
]

# ==========================================
# Profile Status Map
# ==========================================

PROFILE_STATUS_MAP = {
    "draft": PROFILE_STATUS_DRAFT,
    "pending": PROFILE_STATUS_PENDING,
    "approved": PROFILE_STATUS_APPROVED,
    "rejected": PROFILE_STATUS_REJECTED,
    "needs_update": PROFILE_STATUS_NEEDS_UPDATE,
}

# ==========================================
# 21. Working Hours Template
# ==========================================

WORKING_HOURS_TITLE = "🕐 <b>Рабочие часы</b>\n\n"
WORKING_HOURS_INSTRUCTION = (
    "Настройте ваше еженедельное расписание.\n\n"
    "Как это сделать:\n"
    "1) Выберите день недели.\n"
    "2) Добавьте один или несколько диапазонов времени.\n"
    "3) Нажмите «Сохранить шаблон».\n\n"
    "Выберите день недели для настройки:"
)
WORKING_HOURS_EMPTY = (
    "Рабочие часы не настроены.\n\n"
    "Выберите день недели для настройки:"
)
WORKING_HOURS_DAY_SELECTED = "📅 <b>{day_name}</b>\n\n"
WORKING_HOURS_CURRENT_RANGES = "Текущие часы:\n{time_ranges}\n\n"
WORKING_HOURS_NO_RANGES = "Часы не установлены.\n\n"
WORKING_HOURS_ADD_RANGE = (
    "Добавить временной диапазон?\n"
    "<i>Пример: 09:00–12:00 и 14:00–18:00</i>"
)
WORKING_HOURS_START_TIME = (
    "Введите время начала в формате <b>ЧЧ:ММ</b>\n"
    "(например: 09:00, 14:30)"
)
WORKING_HOURS_END_TIME = (
    "Введите время окончания в формате <b>ЧЧ:ММ</b>\n"
    "(например: 12:00, 18:00)"
)
WORKING_HOURS_INVALID_TIME = (
    "⚠️ Неверный формат времени.\n\n"
    "Введите время в формате <b>ЧЧ:ММ</b> (например: 09:00)"
)
WORKING_HOURS_END_BEFORE_START = (
    "⚠️ Время окончания должно быть позже времени начала.\n\n"
    "Введите другое время:"
)
WORKING_HOURS_CONFIRM_RANGE = (
    "Подтвердите временной диапазон:\n\n"
    "📅 {day_name}\n"
    "🕐 {start_time} – {end_time}\n\n"
    "Добавить?"
)
WORKING_HOURS_RANGE_ADDED = "✅ Временной диапазон добавлен!"
WORKING_HOURS_RANGE_REMOVED = "🗑️ Диапазон удалён."
WORKING_HOURS_DAY_CLEARED = "🧹 День очищен."
WORKING_HOURS_RANGE_OVERLAP = (
    "⚠️ Диапазон пересекается с существующим.\n"
    "Удалите старый диапазон или выберите другое время."
)
WORKING_HOURS_PRESET_APPLIED = "⚡️ Пресет применён."
WORKING_HOURS_COPY_PICK_TARGET = (
    "Копировать расписание из дня: <b>{day_name}</b>\n\n"
    "Выберите день, куда скопировать:"
)
WORKING_HOURS_COPY_EMPTY = "⚠️ Нечего копировать: для дня нет диапазонов."
WORKING_HOURS_COPY_DONE = "✅ Диапазоны скопированы."
WORKING_HOURS_SAVE_TEMPLATE = "Сохранить шаблон рабочих часов?"
WORKING_HOURS_TEMPLATE_SAVED = (
    "✅ <b>Шаблон рабочих часов сохранён!</b>\n\n"
    "Ваше расписание настроено."
)
WORKING_HOURS_TEMPLATE_ERROR = "❌ Ошибка сохранения: {error}"

# Day names
DAY_MONDAY = "Понедельник"
DAY_TUESDAY = "Вторник"
DAY_WEDNESDAY = "Среда"
DAY_THURSDAY = "Четверг"
DAY_FRIDAY = "Пятница"
DAY_SATURDAY = "Суббота"
DAY_SUNDAY = "Воскресенье"

DAY_NAMES = {
    0: DAY_MONDAY,
    1: DAY_TUESDAY,
    2: DAY_WEDNESDAY,
    3: DAY_THURSDAY,
    4: DAY_FRIDAY,
    5: DAY_SATURDAY,
    6: DAY_SUNDAY,
}

# Button labels
BTN_WORKING_HOURS = "🕐 Рабочие часы"
BTN_ADD_TIME_RANGE = "➕ Добавить диапазон"
BTN_SAVE_TEMPLATE = "💾 Сохранить шаблон"
BTN_CANCEL_WORKING_HOURS = "❌ Отмена"

# ==========================================
# 22. Date Exceptions
# ==========================================

EXCEPTIONS_TITLE = "📅 <b>Исключения</b>\n\n"
EXCEPTIONS_INSTRUCTION = (
    "Управляйте исключениями в расписании:\n"
    "• Выходные дни\n"
    "• Дни с особыми часами работы\n\n"
    "Выберите действие:"
)
EXCEPTIONS_LIST_TITLE = "📅 <b>Исключения</b>\n\n"
EXCEPTIONS_EMPTY = (
    "Исключений пока нет.\n\n"
    "Добавьте выходной день или день с особыми часами."
)
EXCEPTIONS_ITEM_OFF = "📅 {date} — Выходной"
EXCEPTIONS_ITEM_CUSTOM = "📅 {date} — {time_ranges}"
EXCEPTIONS_ADD_DATE = "Выберите дату для исключения:"
EXCEPTIONS_SELECT_TYPE = (
    "📅 Дата: {date}\n\n"
    "Выберите тип исключения:"
)
EXCEPTIONS_TYPE_OFF = "Выходной день"
EXCEPTIONS_TYPE_CUSTOM = "Особые часы работы"
EXCEPTIONS_CUSTOM_START_TIME = (
    "📅 Дата: {date}\n"
    "Тип: Особые часы\n\n"
    "Введите время начала в формате <b>ЧЧ:ММ</b>\n"
    "(например: 10:00)"
)
EXCEPTIONS_CUSTOM_END_TIME = (
    "📅 Дата: {date}\n"
    "🕐 Начало: {start_time}\n\n"
    "Введите время окончания в формате <b>ЧЧ:ММ</b>\n"
    "(например: 14:00)"
)
EXCEPTIONS_CONFIRM_OFF = (
    "Подтвердите выходной день:\n\n"
    "📅 {date}\n"
    "🚫 Выходной\n\n"
    "Создать?"
)
EXCEPTIONS_CONFIRM_CUSTOM = (
    "Подтвердите особые часы:\n\n"
    "📅 {date}\n"
    "🕐 {start_time} – {end_time}\n\n"
    "Создать?"
)
EXCEPTIONS_CREATED_OFF = (
    "✅ <b>Выходной день добавлен!</b>\n\n"
    "📅 {date}\n"
    "🚫 Выходной"
)
EXCEPTIONS_CREATED_CUSTOM = (
    "✅ <b>Особые часы добавлены!</b>\n\n"
    "📅 {date}\n"
    "🕐 {start_time} – {end_time}"
)
EXCEPTIONS_ERROR = "❌ Ошибка: {error}"
EXCEPTIONS_ALREADY_EXISTS = (
    "⚠️ Исключение для этой даты уже существует.\n\n"
    "Выберите другую дату или удалите существующее исключение."
)
EXCEPTIONS_DELETE_TITLE = "❌ <b>Удаление исключения</b>\n\n"
EXCEPTIONS_DELETE_SELECT = "Выберите исключение для удаления:"
EXCEPTIONS_DELETED = "✅ Исключение удалено!"

# Button labels
BTN_EXCEPTIONS = "📅 Исключения"
BTN_ADD_EXCEPTION = "➕ Добавить исключение"
BTN_DELETE_EXCEPTION = "❌ Удалить исключение"
BTN_EXCEPTION_OFF = "🚫 Выходной"
BTN_EXCEPTION_CUSTOM = "🕐 Особые часы"
BTN_CANCEL_EXCEPTION = "❌ Отмена"
