# NutriMatch Telegram Bot — Manual QA Checklist

## Overview

This document provides step-by-step manual testing procedures for the NutriMatch Telegram bot nutritionist features. Each section includes:
- **Preconditions**: Required setup before testing
- **Steps**: Exact actions to perform
- **Expected Results**: What should happen
- **Verification**: Where to look in logs/DB to confirm

---

## Prerequisites

### Environment Setup
1. Bot is running in polling mode (`TELEGRAM_MODE=polling`)
2. Backend is running and accessible (`BACKEND_URL` configured)
3. Database is seeded with test data (run `python scripts/seed_test_users.py`)
4. Debug mode enabled (`BOT_DEBUG=true`)

### Test Accounts
- **Test Client**: Telegram account for client flow testing
- **Test Nutritionist**: Telegram account for nutritionist flow testing

---

## A) Start / Client Routing

### A1. /start Command — Fresh User

**Preconditions:**
- User has never interacted with bot before OR FSM state is cleared
- Use `/debug` → "Сбросить FSM состояние" to reset

**Steps:**
1. Send `/start` command to bot

**Expected Results:**
- [ ] Bot responds with Russian greeting: "👋 Привет, [Name]!"
- [ ] Message includes "Добро пожаловать в NutriMatch"
- [ ] Inline keyboard shows:
  - "🍎 Открыть мини-приложение" (WebApp button)
  - "👩‍⚕️ Для нутрициологов"

**Verification:**
- Logs: `[REQ] corr_id=xxx user_id=xxx type=message action=command:/start`
- Logs: `[OK] corr_id=xxx` within 2 seconds
- DB: Check `bot_states` table for user entry

---

### A2. WebApp Button — Opens Mini App

**Preconditions:**
- `/start` command completed
- `WEBAPP_URL` environment variable is set correctly

**Steps:**
1. Tap "🍎 Открыть мини-приложение" button

**Expected Results:**
- [ ] Telegram opens Mini App URL from `WEBAPP_URL`
- [ ] Mini App loads without errors
- [ ] No error message in bot

**Verification:**
- Check `WEBAPP_URL` env var matches opened URL
- Browser console (if WebApp): no JS errors

---

### A3. Returning User — Shows Correct Role

**Preconditions:**
- User is registered as nutritionist in backend

**Steps:**
1. Send `/start` command

**Expected Results:**
- [ ] Greeting includes "🩺 Вы зарегистрированы как нутрициолог"
- [ ] User's name from profile is displayed

**Verification:**
- Logs: `[API] ... resolve-telegram-user status=200`
- `/debug` shows: Role from Backend = nutritionist

---

## B) Nutritionist Entry

### B1. "Для нутрициологов" Menu

**Preconditions:**
- User is on main menu (after /start)

**Steps:**
1. Tap "👩‍⚕️ Для нутрициологов" button

**Expected Results:**
- [ ] Screen shows "👩‍⚕️ Раздел для нутрициологов"
- [ ] For new users, buttons include:
  - "✨ Я нутрициолог"
  - "📝 Создать профиль"
  - "◀️ Назад"
- [ ] For existing nutritionists, buttons include:
  - "✏️ Обновить профиль"
  - "🏠 Личный кабинет"
  - "◀️ Назад"

**Verification:**
- FSM state remains `None` (no state change)

---

### B2. "Я нутрициолог" — Role Selection

**Preconditions:**
- User is new (no nutritionist profile)
- User is on nutritionist menu

**Steps:**
1. Tap "✨ Я нутрициолог" button

**Expected Results:**
- [ ] Bot confirms role: "✨ Отлично!"
- [ ] Message explains next steps (4 steps: profile, services, calendar, moderation)
- [ ] Buttons change to show "✏️ Обновить профиль" and "🏠 Личный кабинет"
- [ ] `/debug` shows: Role = nutritionist

**Verification:**
- Logs: `[API] ... /api/nutritionists/upsert status=200`
- DB: `profiles` table shows `role='nutritionist'`
- DB: `nutritionist_profiles` entry created with `verification_status='draft'`

---

## C) Profile Creation/Update Flow (FSM)

### C1. Start Profile Wizard

**Preconditions:**
- User is identified as nutritionist
- On nutritionist menu

**Steps:**
1. Tap "📝 Создать профиль" or "✏️ Обновить профиль"

**Expected Results:**
- [ ] Bot shows "📝 Создание профиля нутрициолога"
- [ ] Shows "Шаг 1 из 6: Введите ваше полное имя"
- [ ] Current name is pre-filled

**Verification:**
- FSM state: `ProfileStates:waiting_full_name`

---

### C2. Full Name Input — Valid

**Preconditions:**
- In profile wizard, step 1

**Steps:**
1. Type "Иван Петров" and send

**Expected Results:**
- [ ] Bot accepts name
- [ ] Moves to step 2: photo prompt
- [ ] Shows "📸 Шаг 2 из 6: Фото профиля"
- [ ] Shows "⏭️ Пропустить" and "❌ Отмена" buttons

**Verification:**
- FSM state: `ProfileStates:waiting_photo`

---

### C3. Full Name Input — Error: Too Short

**Preconditions:**
- In profile wizard, step 1

**Steps:**
1. Type "А" (single character) and send

**Expected Results:**
- [ ] Bot shows error: "⚠️ Имя слишком короткое"
- [ ] Stays on step 1
- [ ] FSM state unchanged

---

### C4. Full Name Input — Error: Too Long

**Preconditions:**
- In profile wizard, step 1

**Steps:**
1. Type 101+ characters

**Expected Results:**
- [ ] Bot shows error: "⚠️ Имя слишком длинное. Максимум 100 символов"
- [ ] Stays on step 1

---

### C5. Photo Upload — Valid Image

**Preconditions:**
- In profile wizard, step 2

**Steps:**
1. Send a photo (not document, actual photo)

**Expected Results:**
- [ ] Bot confirms: "✅ Фото загружено!" or "✅ Фото сохранено!"
- [ ] Moves to step 3: bio prompt

**Verification:**
- Logs: `[API] ... upload-photo status=200`
- FSM state: `ProfileStates:waiting_bio`

---

### C6. Photo Upload — Skip

**Preconditions:**
- In profile wizard, step 2

**Steps:**
1. Tap "⏭️ Пропустить"

**Expected Results:**
- [ ] Moves to step 3 without photo
- [ ] Shows bio prompt

---

### C7. Photo Upload — Error: Non-Photo File

**Preconditions:**
- In profile wizard, step 2

**Steps:**
1. Send a text message instead of photo

**Expected Results:**
- [ ] Bot shows: "⚠️ Пожалуйста, отправьте фотографию или нажмите «Пропустить»"
- [ ] Stays on step 2

---

### C8. Bio Input — Valid (Under 300 chars)

**Preconditions:**
- In profile wizard, step 3

**Steps:**
1. Type bio text (under 300 characters)

**Expected Results:**
- [ ] Bio is saved
- [ ] Moves to step 4: specializations

**Verification:**
- FSM state: `ProfileStates:selecting_specializations`

---

### C9. Bio Input — Error: Over 300 Characters

**Preconditions:**
- In profile wizard, step 3

**Steps:**
1. Type 301+ characters

**Expected Results:**
- [ ] Bot shows: "⚠️ Текст слишком длинный (N символов). Максимум 300"
- [ ] Stays on step 3

---

### C10. Specializations — Multi-Select

**Preconditions:**
- In profile wizard, step 4

**Steps:**
1. Tap on "Управление весом"
2. Tap on "Спортивное питание"
3. Verify checkmarks appear
4. Tap "✓ Готово"

**Expected Results:**
- [ ] Each tap toggles ✅ prefix on button
- [ ] Counter updates: "Выбрано: 2"
- [ ] "✓ Готово" button appears after first selection
- [ ] Moves to step 5 after "Готово"

---

### C11. Specializations — Error: None Selected

**Preconditions:**
- In profile wizard, step 4
- No specializations selected

**Steps:**
1. Try to find "Готово" button

**Expected Results:**
- [ ] "✓ Готово" button is NOT shown when nothing selected
- [ ] Only "❌ Отмена" is available

---

### C12. Tags — Optional Skip

**Preconditions:**
- In profile wizard, step 5

**Steps:**
1. Tap "⏭️ Пропустить"

**Expected Results:**
- [ ] Moves to step 6: rules confirmation
- [ ] No tags are saved

---

### C13. Rules Confirmation

**Preconditions:**
- In profile wizard, after tags

**Steps:**
1. Read rules text
2. Tap "✅ Принимаю правила"

**Expected Results:**
- [ ] Rules text is in Russian
- [ ] Includes: qualification, ethics, quality, finances, cancellation policy
- [ ] After confirming, shows profile summary

**Verification:**
- FSM state: `ProfileStates:confirming_submission`

---

### C14. Profile Submission

**Preconditions:**
- In profile wizard, step 6

**Steps:**
1. Review summary
2. Tap "📤 Отправить на модерацию"

**Expected Results:**
- [ ] Bot shows: "🎉 Профиль отправлен на модерацию!"
- [ ] Message mentions 24-48 hour review time
- [ ] Returns to nutritionist menu

**Verification:**
- Logs: `[API] ... /api/nutritionists/upsert ... submit_for_verification=true`
- DB: `nutritionist_profiles.verification_status = 'pending'`
- FSM state: `None` (cleared)

---

### C15. Profile Wizard — Cancel at Any Step

**Preconditions:**
- In any step of profile wizard

**Steps:**
1. Tap "❌ Отмена"

**Expected Results:**
- [ ] Bot shows: "❌ Создание профиля отменено"
- [ ] Returns to nutritionist menu
- [ ] FSM state cleared

---

## D) Documents Upload

### D1. Upload Diploma as Image

**Preconditions:**
- Nutritionist profile exists
- In personal cabinet or documents section

**Steps:**
1. Navigate to documents upload (if available)
2. Send diploma photo

**Expected Results:**
- [ ] Bot downloads file via Telegram getFile
- [ ] Bot sends to backend as multipart
- [ ] Bot confirms: "✅ Документ загружен"

**Verification:**
- Logs: `[API] ... documents/upload status=200`
- DB: `nutritionist_documents` entry created

---

### D2. Upload Certificate as PDF

**Preconditions:**
- Same as D1

**Steps:**
1. Send PDF file as document

**Expected Results:**
- [ ] If PDF supported: upload succeeds
- [ ] If not supported: clear error message in Russian

---

### D3. Upload Error — Oversized File

**Preconditions:**
- Same as D1

**Steps:**
1. Try to send file over Telegram limit (20MB)

**Expected Results:**
- [ ] User-friendly Russian error message
- [ ] Suggestion to compress or retry

---

### D4. Upload Error — Backend Failure

**Preconditions:**
- Backend is down or returns error

**Steps:**
1. Try to upload document

**Expected Results:**
- [ ] Bot shows: error message with retry suggestion
- [ ] Correlation ID shown for support reference

---

## E) Services CRUD

### E1. View Services List — Empty

**Preconditions:**
- Nutritionist has no services
- In personal cabinet

**Steps:**
1. Tap "📋 Мои услуги"

**Expected Results:**
- [ ] Shows: "У вас пока нет услуг"
- [ ] Shows: "➕ Добавить услугу" button

---

### E2. Add Service — Complete Flow

**Preconditions:**
- In services list

**Steps:**
1. Tap "➕ Добавить услугу"
2. Enter title: "Консультация"
3. Skip description
4. Enter duration: 60
5. Enter price: 3000
6. Confirm creation

**Expected Results:**
- [ ] Step 1: Title prompt appears
- [ ] Step 2: Description prompt with skip option
- [ ] Step 3: Duration prompt (numeric)
- [ ] Step 4: Price prompt (numeric)
- [ ] Step 5: Confirmation shows all data
- [ ] After confirm: "🎉 Услуга создана!"

**Verification:**
- Logs: `[API] ... /services status=201`
- DB: `services` table has new entry

---

### E3. Add Service — Validation: Duration

**Preconditions:**
- In service creation, duration step

**Steps:**
1. Enter "abc" (non-numeric)
2. Enter "10" (too short)
3. Enter "300" (too long)

**Expected Results:**
- [ ] Non-numeric: "⚠️ Введите число минут"
- [ ] Too short: "⚠️ Минимальная длительность — 15 минут"
- [ ] Too long: "⚠️ Максимальная длительность — 240 минут"

---

### E4. Add Service — Validation: Price

**Preconditions:**
- In service creation, price step

**Steps:**
1. Enter "50" (too low)
2. Enter "150000" (too high)

**Expected Results:**
- [ ] Too low: "⚠️ Минимальная цена — 100₽"
- [ ] Too high: "⚠️ Максимальная цена — 100 000₽"

---

### E5. Edit Service — Toggle Active

**Preconditions:**
- Service exists and is active

**Steps:**
1. Open services list
2. Tap on service
3. Tap "⏸️ Деактивировать"

**Expected Results:**
- [ ] Service status changes to inactive
- [ ] Button text changes to "✅ Активировать"
- [ ] List shows ⏸️ instead of ✅

**Verification:**
- DB: `services.is_active = false`

---

### E6. Delete Service

**Preconditions:**
- Service exists

**Steps:**
1. Open service details
2. Tap "🗑️ Удалить"
3. Confirm deletion

**Expected Results:**
- [ ] Confirmation prompt appears
- [ ] After confirm: "✅ Услуга удалена"
- [ ] Service removed from list

**Verification:**
- DB: Service record deleted
- Logs: `[API] ... DELETE ... status=200`

---

## F) Schedule Management (Manual Slots — PRIMARY)

> **Note:** Manual slots are the PRIMARY method for availability management.
> Google Calendar integration is OPTIONAL and non-blocking.

### F1. Schedule View — Empty State

**Preconditions:**
- Nutritionist has no availability slots
- In personal cabinet

**Steps:**
1. Tap "🕒 Расписание"

**Expected Results:**
- [ ] Shows: "У вас пока нет доступных слотов"
- [ ] Explains benefits of adding slots
- [ ] Shows "➕ Добавить слот" button
- [ ] Shows "🔄 Обновить" button
- [ ] Shows "◀️ Назад" button
- [ ] NO "❌ Удалить слот" button (no slots to delete)

---

### F2. Add Slot — Complete Flow

**Preconditions:**
- In schedule view

**Steps:**
1. Tap "➕ Добавить слот"
2. Select date (e.g., tomorrow)
3. Enter time: "14:00"
4. Select duration: "60 минут"
5. Confirm: "✅ Добавить слот"

**Expected Results:**
- [ ] Step 1: Date selection keyboard with next 14 days
- [ ] Each date shows: "15 янв (Пн)" format
- [ ] Step 2: Text input prompt for time (HH:MM)
- [ ] Step 3: Duration selection (30/45/60/90 минут)
- [ ] Step 4: Confirmation shows summary:
  - "📅 15 января"
  - "🕒 14:00–15:00"
  - "⏱ 60 минут"
- [ ] After confirm: "✅ Слот создан!"
- [ ] Returns to schedule view with new slot visible

**Verification:**
- Logs: `[API] ... /slots POST status=201`
- DB: `availability_slots` has new entry with `status='free'`, `source='manual'`

---

### F3. Add Slot — Validation: Invalid Time Format

**Preconditions:**
- In slot creation, time input step

**Steps:**
1. Enter "abc" (non-time format)
2. Enter "25:00" (invalid hour)
3. Enter "14:75" (invalid minutes)

**Expected Results:**
- [ ] Error: "⚠️ Неверный формат времени"
- [ ] Stays on time input step
- [ ] Shows example: "Введите время в формате ЧЧ:ММ"

---

### F4. Add Slot — Validation: Past Time

**Preconditions:**
- In slot creation, time input step
- Selected date is today

**Steps:**
1. Enter a time that has already passed today

**Expected Results:**
- [ ] Error: "⚠️ Время слота должно быть в будущем"
- [ ] Stays on time input step

---

### F5. Add Slot — Validation: Overlapping Slot

**Preconditions:**
- Existing slot: tomorrow 14:00–15:00

**Steps:**
1. Try to create slot: tomorrow 14:30–15:30

**Expected Results:**
- [ ] Error: "Этот слот пересекается с существующим. Выберите другое время."
- [ ] Returns to schedule view
- [ ] Original slot unchanged

**Verification:**
- Logs: `[API] ... /slots POST status=409`

---

### F6. Schedule View — With Slots

**Preconditions:**
- Nutritionist has multiple slots created

**Steps:**
1. Open "🕒 Расписание"

**Expected Results:**
- [ ] Shows slots grouped by date: "📅 15 января"
- [ ] Each slot shows: "• 12:00–13:00 (свободно)"
- [ ] Booked slots show: "• 15:00–16:00 (забронировано)"
- [ ] Held slots show: "• 17:00–18:00 (удерживается)"
- [ ] "❌ Удалить слот" button appears (has free slots)
- [ ] All text in Russian

---

### F7. Delete Slot — Free Slot

**Preconditions:**
- Free slot exists

**Steps:**
1. In schedule, tap "❌ Удалить слот"
2. Select a free slot from list
3. Confirm

**Expected Results:**
- [ ] Shows list of free slots only
- [ ] Each slot shows date and time: "15 янв (Пн), 14:00–15:00"
- [ ] After select: "✅ Слот удалён!"
- [ ] Slot disappears from schedule

**Verification:**
- Logs: `[API] ... /slots/{id} DELETE status=200`
- DB: Slot record deleted

---

### F8. Delete Slot — Booked Slot (Not Allowed)

**Preconditions:**
- Booked slot exists (status=booked)

**Steps:**
1. Tap "❌ Удалить слот"
2. Look for booked slot in list

**Expected Results:**
- [ ] Booked slots NOT shown in delete selection
- [ ] Only free slots available for deletion
- [ ] If no free slots: "Нет свободных слотов для удаления"

---

### F9. Delete Slot — Error Handling

**Preconditions:**
- Free slot in list
- Slot gets booked by another process during delete

**Steps:**
1. Select slot to delete
2. (Slot gets booked externally)
3. Confirm deletion

**Expected Results:**
- [ ] Error: "Слот уже используется и не может быть удалён"
- [ ] Returns to schedule view
- [ ] Slot visible with "забронировано" status

---

### F10. Cancel Slot Creation

**Preconditions:**
- In any step of slot creation wizard

**Steps:**
1. Tap "❌ Отмена"

**Expected Results:**
- [ ] Returns to schedule view
- [ ] No slot created
- [ ] FSM state cleared

---

### F11. Refresh Schedule

**Preconditions:**
- On schedule view

**Steps:**
1. Tap "🔄 Обновить"

**Expected Results:**
- [ ] Schedule reloads from backend
- [ ] Any new slots appear
- [ ] Any deleted slots disappear

---

## F-CAL) Calendar Integration (OPTIONAL)

> **Note:** Calendar integration is OPTIONAL and does NOT block manual slot creation.

### F-CAL1. Calendar Status — Not Connected

**Preconditions:**
- Google Calendar not connected

**Steps:**
1. Open personal cabinet
2. Tap "📅 Календарь"

**Expected Results:**
- [ ] Shows: "❌ Google Calendar не подключён"
- [ ] Manual slots still work independently
- [ ] Shows benefits of connecting (sync, no conflicts)

---

### F-CAL2. Calendar Status — Connected

**Preconditions:**
- Google Calendar connected (if implemented)

**Steps:**
1. Open "📅 Календарь"

**Expected Results:**
- [ ] Shows: "✅ Google Calendar подключён"
- [ ] Shows connected email
- [ ] In schedule view: "📅 Google Calendar подключён" note

---

### F-CAL3. Calendar Disconnected — Everything Works

**Preconditions:**
- Calendar NOT connected
- Manual slots exist

**Steps:**
1. Create manual slots
2. View schedule
3. Delete slots
4. View bookings

**Expected Results:**
- [ ] ALL features work without calendar
- [ ] No errors or warnings about calendar
- [ ] Manual slots are fully functional

---

## F-BOOK) Nutritionist Bookings View

### F-BOOK1. Bookings — Empty State

**Preconditions:**
- Nutritionist has no bookings

**Steps:**
1. Open personal cabinet
2. Tap "📋 Мои бронирования"

**Expected Results:**
- [ ] Shows: "Пока нет предстоящих бронирований"
- [ ] Explains that bookings appear after clients book
- [ ] Shows "🔄 Обновить" button
- [ ] Shows "◀️ В кабинет" button

---

### F-BOOK2. Bookings — With Data

**Preconditions:**
- Nutritionist has confirmed bookings

**Steps:**
1. Tap "📋 Мои бронирования"

**Expected Results:**
- [ ] Shows list of upcoming bookings
- [ ] Each booking shows:
  - "📅 15 янв, 14:00–15:00"
  - "👤 Имя клиента"
  - "💼 Название услуги"
  - "✅ Подтверждено" or "☑️ Завершено"
- [ ] Sorted by date (upcoming first)
- [ ] All text in Russian

---

### F-BOOK3. Bookings — Pagination

**Preconditions:**
- More than 10 bookings exist

**Steps:**
1. Open bookings
2. Tap "Далее ▶️"
3. Tap "◀️ Назад"

**Expected Results:**
- [ ] Page indicator: "1-10 из 15"
- [ ] Navigation buttons appear correctly
- [ ] "Далее ▶️" hidden on last page
- [ ] "◀️ Назад" hidden on first page

---

### F-BOOK4. Bookings — Refresh

**Preconditions:**
- On bookings view

**Steps:**
1. Tap "🔄 Обновить"

**Expected Results:**
- [ ] Bookings list reloads from backend
- [ ] Any new bookings appear
- [ ] Cancelled bookings disappear

---

## G) Reviews

### G1. Reviews — Empty State

**Preconditions:**
- Nutritionist has no reviews

**Steps:**
1. Open personal cabinet
2. Tap "⭐ Отзывы"

**Expected Results:**
- [ ] Shows: "У вас пока нет отзывов"
- [ ] Text is in Russian
- [ ] Explains that reviews appear after consultations

---

### G2. Reviews — With Data

**Preconditions:**
- Nutritionist has reviews in database

**Steps:**
1. Open reviews section

**Expected Results:**
- [ ] Shows list of reviews
- [ ] Each review shows: stars, client name, comment excerpt, date
- [ ] Pagination works (if more than 5)
- [ ] All text in Russian

---

### G3. Reviews — Pagination

**Preconditions:**
- More than 5 reviews exist

**Steps:**
1. Open reviews
2. Tap "Далее ▶️"
3. Tap "◀️ Назад"

**Expected Results:**
- [ ] Page numbers update: "1-5 из 10" → "6-10 из 10"
- [ ] Navigation buttons appear/disappear correctly

---

## H) Statistics

### H1. Statistics — Empty State

**Preconditions:**
- Nutritionist has no bookings

**Steps:**
1. Open personal cabinet
2. Tap "📊 Статистика"

**Expected Results:**
- [ ] Shows meaningful empty state
- [ ] Income: 0₽
- [ ] Consultations: 0
- [ ] Text in Russian

---

### H2. Statistics — With Data

**Preconditions:**
- Nutritionist has completed bookings

**Steps:**
1. Open statistics

**Expected Results:**
- [ ] Shows last 30 days data
- [ ] Income formatted with ₽ and thousands separator
- [ ] Consultations count shown
- [ ] Rating shown (if applicable)

---

## I) Settings

### I1. Settings — Cancellation Policy

**Preconditions:**
- In personal cabinet

**Steps:**
1. Tap "⚙️ Настройки"

**Expected Results:**
- [ ] Shows fixed cancellation policy text
- [ ] Policy includes:
  - 24+ hours: full refund
  - Less than 24h: 50% refund
  - No-show: no refund
  - Nutritionist cancels: full refund
- [ ] All text in Russian
- [ ] No editable options

---

### I2. Settings — No Language Switch

**Preconditions:**
- In settings

**Steps:**
1. Look for language selection

**Expected Results:**
- [ ] NO language switching option exists
- [ ] Only Russian is used

---

## J) Support

### J1. Support — Send Message

**Preconditions:**
- In personal cabinet

**Steps:**
1. Tap "💬 Поддержка"
2. Type: "Тестовое сообщение для поддержки"
3. Send

**Expected Results:**
- [ ] Prompt appears: "Опишите вашу проблему"
- [ ] After sending: "✅ Сообщение отправлено!"
- [ ] Confirmation: "Мы ответим в ближайшее время"

**Verification:**
- Logs: `Support message from user X: ...`
- Backend: Support endpoint called

---

### J2. Support — Cancel

**Preconditions:**
- In support message input

**Steps:**
1. Tap "❌ Отмена"

**Expected Results:**
- [ ] Returns to cabinet
- [ ] No message sent

---

### J3. Support — Message Too Long

**Preconditions:**
- In support input

**Steps:**
1. Type 1001+ characters
2. Send

**Expected Results:**
- [ ] Error: "⚠️ Сообщение слишком длинное. Максимум 1000 символов"

---

## K) Regression / Removability Checks

### K1. Bot Down — Backend Still Works

**Preconditions:**
- Backend and client running
- Bot stopped

**Steps:**
1. Stop bot process
2. Access client Mini App
3. Make API calls directly

**Expected Results:**
- [ ] Client Mini App works normally
- [ ] API responds correctly
- [ ] No dependency on bot

---

### K2. Bot Uses HTTP Only

**Preconditions:**
- Review bot code

**Steps:**
1. Check bot imports
2. Check bot dependencies

**Expected Results:**
- [ ] Bot does NOT import backend models
- [ ] Communication is via HTTP only
- [ ] Uses `api_client.py` for all backend calls

---

### K3. Backend Down — Bot Graceful Degradation

**Preconditions:**
- Bot running
- Backend stopped

**Steps:**
1. Try various bot commands
2. Check error handling

**Expected Results:**
- [ ] Bot shows user-friendly error messages
- [ ] Correlation ID provided for support
- [ ] Bot does not crash

---

## Debug Utilities

### Debug Commands (BOT_DEBUG=true required)

**Preconditions:**
- `BOT_DEBUG=true` environment variable set

**Steps:**
1. Send `/debug` command

**Expected Results:**
- [ ] Shows user info (Telegram ID, username)
- [ ] Shows role (from state and backend)
- [ ] Shows FSM state
- [ ] Shows backend URL and status
- [ ] Shows bot mode

---

### Debug — Reset FSM State

**Preconditions:**
- In debug menu

**Steps:**
1. Tap "🗑️ Сбросить FSM состояние"

**Expected Results:**
- [ ] FSM state cleared
- [ ] Confirmation shown
- [ ] Debug info refreshed

---

### Debug — Check Backend

**Preconditions:**
- In debug menu

**Steps:**
1. Tap "🏥 Проверить backend"

**Expected Results:**
- [ ] Health check result shown
- [ ] Service token auth verified
- [ ] User resolution tested

---

## Test Completion Checklist

After completing all tests, verify:

- [ ] All Russian text is grammatically correct
- [ ] No untranslated English text in user-facing messages
- [ ] All error messages include actionable guidance
- [ ] FSM states are properly cleared after flows complete
- [ ] All API calls include correlation IDs in logs
- [ ] No memory leaks in long sessions
- [ ] Rate limiting works (cannot spam buttons)

---

## Log Analysis Reference

### Log Format
```
[TYPE] corr_id=XXXXXXXX user_id=NNNNNNNN type=message|callback action=... fsm_state=...
```

### Key Log Patterns
- `[REQ]` — Incoming request
- `[OK]` — Successful completion
- `[ERR]` — Error occurred
- `[API]` — Backend API call
- `[THROTTLE]` — Rate limit hit
- `[FATAL]` — Unhandled exception

### Database Tables to Check
- `profiles` — User profiles with roles
- `nutritionist_profiles` — Nutritionist-specific data
- `services` — Services offered
- `bot_states` — FSM state storage
- `nutritionist_documents` — Uploaded documents

---

## Issue Reporting Template

When reporting issues, include:

```
## Issue: [Brief Description]

**Environment:**
- Bot Version: [commit hash]
- Backend Version: [commit hash]
- Test Date: YYYY-MM-DD

**Correlation ID:** [from error message]

**Steps to Reproduce:**
1. ...
2. ...

**Expected Result:**
...

**Actual Result:**
...

**Logs:**
[relevant log lines]

**Screenshots:**
[if applicable]
```

