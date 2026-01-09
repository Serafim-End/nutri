# UX Map: Nutritionist Bot

## Overview
This document describes the complete user experience flow for nutritionists using the Telegram bot. It covers all screens, entry points, transitions, terminal states, and navigation rules.

**Scope:** UX structure only. No code, database, or API details.

---

## Entry Points

### Primary Entry Points
1. **`/start` command**
   - Triggers: User sends `/start` command
   - Owner: Any user (resolved to role)
   - Action: Resolves user role → shows Main Menu

2. **Main Menu → "Для нутрициологов"**
   - Triggers: Callback button from Main Menu
   - Owner: Any user
   - Action: Shows Nutritionist Menu

---

## Screen Catalog

### 1. Start/Welcome Screen
- **Owner:** System (entry resolution)
- **Entry:** `/start` command
- **Exit:** Always transitions to Main Menu
- **Content:** Welcome message, role detection result
- **Navigation:** Inline button to Main Menu

### 2. Main Menu
- **Owner:** Client/Nutritionist/Admin (all users)
- **Entry:** 
  - From `/start` command
  - From "Назад" in Nutritionist Menu
- **Exit:**
  - "Открыть мини-приложение" → Opens WebApp (external)
  - "Для нутрициологов" → Nutritionist Menu
- **Content:** Welcome text, role indicator
- **Navigation:** Inline buttons only

### 3. Nutritionist Menu
- **Owner:** Nutritionist
- **Entry:**
  - From Main Menu → "Для нутрициологов"
  - From "Назад" in various screens
- **Exit:**
  - If no profile:
    - "Я нутрициолог" → Updates intent, stays on Nutritionist Menu
    - "Создать профиль" → Profile Creation Flow (Step 1)
  - If has profile:
    - "Обновить профиль" → Profile Creation Flow (Step 1, pre-filled)
    - "Личный кабинет" → Personal Cabinet
  - "Назад" → Main Menu
- **Content:** Profile status (if exists), menu options
- **Navigation:** Inline buttons only

### 4. Profile Creation Flow (FSM)
**Multi-step form with state management**

#### 4a. Profile Step 1: Full Name
- **Owner:** Nutritionist
- **Entry:**
  - From Nutritionist Menu → "Создать профиль" or "Обновить профиль"
- **Exit:**
  - Text input → Step 2 (Photo)
  - `/skip` command → Step 2 (Photo, keeps existing)
- **Content:** Instructions to enter full name
- **Navigation:** Reply (text input) or Inline (skip via Cancel)

#### 4b. Profile Step 2: Photo
- **Owner:** Nutritionist
- **Entry:** From Step 1 (Full Name)
- **Exit:**
  - Photo upload → Step 3 (Bio)
  - "Пропустить" button → Step 3 (Bio)
- **Content:** Instructions to upload photo
- **Navigation:** Reply (photo) or Inline (skip button)

#### 4c. Profile Step 3: Bio
- **Owner:** Nutritionist
- **Entry:** From Step 2 (Photo)
- **Exit:**
  - Text input → Step 4 (Specializations)
  - "Пропустить" button → Step 4 (Specializations)
- **Content:** Instructions to write bio (max 300 chars)
- **Navigation:** Reply (text) or Inline (skip button)

#### 4d. Profile Step 4: Specializations (Multi-select)
- **Owner:** Nutritionist
- **Entry:** From Step 3 (Bio)
- **Exit:**
  - Toggle specializations → Stays on same screen (updates selection)
  - "Готово" button → Step 5 (Tags) [requires at least 1 selection]
  - "Отмена" → Returns to Nutritionist Menu, cancels flow
- **Content:** List of specializations with checkmarks for selected
- **Navigation:** Inline buttons only (toggle selection, done, cancel)

#### 4e. Profile Step 5: Tags (Multi-select, Optional)
- **Owner:** Nutritionist
- **Entry:** From Step 4 (Specializations)
- **Exit:**
  - Toggle tags → Stays on same screen (updates selection)
  - "Готово" button → Step 6 (Rules Confirmation)
  - "Пропустить" button → Step 6 (Rules Confirmation)
  - "Отмена" → Returns to Nutritionist Menu, cancels flow
- **Content:** List of tags with checkmarks for selected
- **Navigation:** Inline buttons only

#### 4f. Profile Step 6: Rules Confirmation
- **Owner:** Nutritionist
- **Entry:** From Step 5 (Tags)
- **Exit:**
  - "Принимаю правила" → Step 7 (Final Confirmation)
  - "Отмена" → Returns to Nutritionist Menu, cancels flow
- **Content:** Rules and restrictions text
- **Navigation:** Inline buttons only

#### 4g. Profile Step 7: Final Confirmation
- **Owner:** Nutritionist
- **Entry:** From Step 6 (Rules Confirmation)
- **Exit:**
  - "Отправить на модерацию" → Terminal: Profile Submitted
  - "Редактировать" → Returns to Step 1 (restarts flow)
  - "Отмена" → Returns to Nutritionist Menu, cancels flow
- **Content:** Summary of all profile data
- **Navigation:** Inline buttons only

#### 4h. Profile Submitted (Terminal)
- **Owner:** Nutritionist
- **Entry:** From Step 7 (Final Confirmation) → successful submission
- **Exit:**
  - "Назад" → Nutritionist Menu (with updated profile status)
- **Content:** Success message, next steps
- **Navigation:** Inline buttons only

### 5. Personal Cabinet
- **Owner:** Nutritionist (requires profile)
- **Entry:**
  - From Nutritionist Menu → "Личный кабинет"
  - From various screens → "◀️ Назад" or "◀️ В кабинет"
- **Exit:**
  - "Расписание" → Schedule View
  - "Мои бронирования" → Bookings List
  - "Мои услуги" → Services List
  - "Календарь" → Calendar Settings
  - "Отзывы" → Reviews List
  - "Статистика" → Statistics View
  - "Настройки" → Settings View
  - "Поддержка" → Support Flow (Step 1)
  - "Назад" → Nutritionist Menu
- **Content:** Nutritionist name, basic stats (bookings, earnings)
- **Navigation:** Inline buttons only

### 6. Services List
- **Owner:** Nutritionist
- **Entry:**
  - From Personal Cabinet → "Мои услуги"
  - From Service Creation/Edit → "◀️ Назад к услугам"
- **Exit:**
  - Service item click → Service Details
  - "Добавить услугу" → Service Creation Flow (Step 1)
  - "Назад" → Nutritionist Menu
- **Content:** List of services with status, price, or empty state
- **Navigation:** Inline buttons only

### 7. Service Creation Flow (FSM)
**Multi-step form with state management**

#### 7a. Service Step 1: Title
- **Owner:** Nutritionist
- **Entry:** From Services List → "Добавить услугу"
- **Exit:**
  - Text input (3-100 chars) → Step 2 (Description)
- **Content:** Instructions to enter service title
- **Navigation:** Reply (text input)

#### 7b. Service Step 2: Description (Optional)
- **Owner:** Nutritionist
- **Entry:** From Step 1 (Title)
- **Exit:**
  - Text input → Step 3 (Duration)
  - "Пропустить" button → Step 3 (Duration)
- **Content:** Instructions to enter description (max 500 chars)
- **Navigation:** Reply (text) or Inline (skip button)

#### 7c. Service Step 3: Duration
- **Owner:** Nutritionist
- **Entry:** From Step 2 (Description)
- **Exit:**
  - Number input (15-240 minutes) → Step 4 (Price)
- **Content:** Instructions to enter duration in minutes
- **Navigation:** Reply (number input)

#### 7d. Service Step 4: Price
- **Owner:** Nutritionist
- **Entry:** From Step 3 (Duration)
- **Exit:**
  - Number input (100-100000₽) → Step 5 (Confirmation)
- **Content:** Instructions to enter price in rubles
- **Navigation:** Reply (number input)

#### 7e. Service Step 5: Confirmation
- **Owner:** Nutritionist
- **Entry:** From Step 4 (Price)
- **Exit:**
  - "Создать услугу" → Terminal: Service Created
  - "Отмена" → Returns to Services List, cancels flow
- **Content:** Summary of service data
- **Navigation:** Inline buttons only

#### 7f. Service Created (Terminal)
- **Owner:** Nutritionist
- **Entry:** From Step 5 (Confirmation) → successful creation
- **Exit:**
  - "Назад" → Services List (with new service)
- **Content:** Success message, service details
- **Navigation:** Inline buttons only

### 8. Service Details
- **Owner:** Nutritionist
- **Entry:** From Services List → Service item click
- **Exit:**
  - "Активировать/Деактивировать" → Stays on screen (updates status)
  - "Удалить" → Delete Confirmation
  - "Назад к услугам" → Services List
- **Content:** Service details (title, description, duration, price, status)
- **Navigation:** Inline buttons only

### 9. Delete Service Confirmation
- **Owner:** Nutritionist
- **Entry:** From Service Details → "Удалить"
- **Exit:**
  - "Да, удалить" → Terminal: Service Deleted
  - "Отмена" → Services List
- **Content:** Warning about deletion
- **Navigation:** Inline buttons only

### 10. Service Deleted (Terminal)
- **Owner:** Nutritionist
- **Entry:** From Delete Confirmation → successful deletion
- **Exit:**
  - "Назад" → Services List (without deleted service)
- **Content:** Success message
- **Navigation:** Inline buttons only

### 11. Schedule View
- **Owner:** Nutritionist
- **Entry:**
  - From Personal Cabinet → "Расписание"
  - From Add/Delete Slot flows → "Назад"
  - From Add Slot Success → Returns here
- **Exit:**
  - "Добавить слот" → Add Slot Flow (Step 1)
  - "Удалить слот" (if free slots exist) → Delete Slot Flow
  - "Обновить" → Refreshes same screen
  - "Назад" → Personal Cabinet
- **Content:** List of slots grouped by date (next 14 days), status indicators
- **Navigation:** Inline buttons only

### 12. Add Slot Flow (FSM)
**Multi-step wizard with state management**

#### 12a. Add Slot Step 1: Date Selection
- **Owner:** Nutritionist
- **Entry:** From Schedule View → "Добавить слот"
- **Exit:**
  - Date button click → Step 2 (Start Time)
  - "Отмена" → Schedule View
- **Content:** List of next 14 days for selection
- **Navigation:** Inline buttons only (date buttons, cancel)

#### 12b. Add Slot Step 2: Start Time
- **Owner:** Nutritionist
- **Entry:** From Step 1 (Date Selection)
- **Exit:**
  - Time input (HH:MM format, future time) → Step 3 (Duration)
  - Invalid input → Stays on screen with error
- **Content:** Instructions to enter start time
- **Navigation:** Reply (time input in HH:MM format)

#### 12c. Add Slot Step 3: Duration
- **Owner:** Nutritionist
- **Entry:** From Step 2 (Start Time)
- **Exit:**
  - Duration button click (30/45/60/90 min) → Step 4 (Confirmation)
  - "Отмена" → Schedule View
- **Content:** Duration options
- **Navigation:** Inline buttons only

#### 12d. Add Slot Step 4: Confirmation
- **Owner:** Nutritionist
- **Entry:** From Step 3 (Duration)
- **Exit:**
  - "Добавить слот" → Terminal: Slot Created
  - "Отмена" → Schedule View
- **Content:** Summary of slot (date, time range, duration)
- **Navigation:** Inline buttons only

#### 12e. Slot Created (Terminal)
- **Owner:** Nutritionist
- **Entry:** From Step 4 (Confirmation) → successful creation
- **Exit:**
  - "Назад" → Schedule View (with new slot)
- **Content:** Success message, slot details
- **Navigation:** Inline buttons only

### 13. Delete Slot Flow

#### 13a. Delete Slot Selection
- **Owner:** Nutritionist
- **Entry:** From Schedule View → "Удалить слот" (if free slots exist)
- **Exit:**
  - Slot button click → Terminal: Slot Deleted (immediate deletion)
  - "Отмена" → Schedule View
  - No free slots → Shows error, stays on Schedule View
- **Content:** List of free slots available for deletion
- **Navigation:** Inline buttons only

#### 13b. Slot Deleted (Terminal)
- **Owner:** Nutritionist
- **Entry:** From Delete Slot Selection → successful deletion
- **Exit:**
  - "Назад" → Schedule View (without deleted slot)
- **Content:** Success message
- **Navigation:** Inline buttons only

### 14. Bookings List
- **Owner:** Nutritionist
- **Entry:**
  - From Personal Cabinet → "Мои бронирования"
  - From pagination → Next/Previous pages
- **Exit:**
  - "◀️ Назад" (pagination) → Previous page
  - "Далее ▶️" (pagination) → Next page
  - "Обновить" → Refreshes current page
  - "◀️ В кабинет" → Personal Cabinet
- **Content:** List of bookings with date, time, client name, service, status (paginated)
- **Navigation:** Inline buttons only (pagination, refresh, back)

### 15. Reviews List
- **Owner:** Nutritionist
- **Entry:**
  - From Personal Cabinet → "Отзывы"
  - From pagination → Next/Previous pages
- **Exit:**
  - "◀️ Назад" (pagination) → Previous page
  - "Далее ▶️" (pagination) → Next page
  - "◀️ В кабинет" → Personal Cabinet
- **Content:** List of reviews with rating, client name, comment, date (paginated), or empty state
- **Navigation:** Inline buttons only

### 16. Statistics View
- **Owner:** Nutritionist
- **Entry:** From Personal Cabinet → "Статистика"
- **Exit:**
  - "Назад" → Personal Cabinet
- **Content:** Statistics for last 30 days (income, consultations, rating, clients)
- **Navigation:** Inline buttons only

### 17. Calendar Settings
- **Owner:** Nutritionist
- **Entry:** From Personal Cabinet → "Календарь"
- **Exit:**
  - "Подключить Google Calendar" (if not connected) → External OAuth flow
  - "Назад" → Personal Cabinet
- **Content:** Connection status, instructions, benefits
- **Navigation:** Inline buttons only (or external URL button)

### 18. Settings View
- **Owner:** Nutritionist
- **Entry:** From Personal Cabinet → "Настройки"
- **Exit:**
  - "Назад" → Personal Cabinet
- **Content:** Cancellation policy and rules (read-only)
- **Navigation:** Inline buttons only

### 19. Support Flow (FSM)

#### 19a. Support Step 1: Message Input
- **Owner:** Nutritionist
- **Entry:** From Personal Cabinet → "Поддержка"
- **Exit:**
  - Text input (1-1000 chars) → Terminal: Message Sent
  - "Отмена" → Personal Cabinet
- **Content:** Instructions to describe problem/question
- **Navigation:** Reply (text input) or Inline (cancel button)

#### 19b. Message Sent (Terminal)
- **Owner:** Nutritionist
- **Entry:** From Step 1 → successful submission
- **Exit:**
  - "Назад" → Personal Cabinet
- **Content:** Success message
- **Navigation:** Inline buttons only

---

## Navigation Rules

### Reply vs Inline Navigation

**Reply Navigation (Text/Photo Input):**
- Used for: Free-form text input, photo uploads, numeric input
- Screens using Reply:
  - Profile Creation: Steps 1 (name), 2 (photo), 3 (bio)
  - Service Creation: Steps 1 (title), 2 (description), 3 (duration), 4 (price)
  - Add Slot: Step 2 (start time)
  - Support: Step 1 (message)

**Inline Navigation (Buttons):**
- Used for: Selection from options, navigation, confirmations, pagination
- All other screens use Inline buttons exclusively

### State Management

**FSM States (Multi-step flows):**
- Profile Creation: 7 steps with state persistence
- Service Creation: 5 steps with state persistence
- Add Slot: 4 steps with state persistence
- Support: 1 step (simple input)

**Non-FSM Screens (Direct navigation):**
- All menu screens, lists, views, settings
- Simple navigation via callback buttons
- No state persistence needed

### Cancel/Back Behavior

**Cancel Flow:**
- Available in all FSM flows
- Clears state and returns to entry point or menu
- Always accessible via "Отмена" or "❌ Отмена" buttons

**Back Navigation:**
- Most screens have "◀️ Назад" button
- Returns to previous screen in navigation hierarchy
- Hierarchy: Main Menu → Nutritionist Menu → Personal Cabinet → Specific screens

### Terminal States

**Success Terminals (require action to continue):**
- Profile Submitted → Returns to Nutritionist Menu
- Service Created → Returns to Services List
- Slot Created → Returns to Schedule View
- Service Deleted → Returns to Services List
- Slot Deleted → Returns to Schedule View
- Message Sent → Returns to Personal Cabinet

**Error Handling:**
- All flows show error messages on failure
- User can retry or cancel
- Never leaves user in dead-end state

---

## Transition Map

### Main Navigation Paths

```
/start
  ↓
Main Menu
  ├─→ Open WebApp (external)
  └─→ Nutritionist Menu
      ├─→ Profile Creation Flow (if no profile)
      │   └─→ [7 steps] → Profile Submitted → Nutritionist Menu
      └─→ Personal Cabinet (if has profile)
          ├─→ Schedule View
          │   ├─→ Add Slot Flow [4 steps] → Slot Created → Schedule View
          │   └─→ Delete Slot Flow → Slot Deleted → Schedule View
          ├─→ Bookings List (paginated)
          ├─→ Services List
          │   ├─→ Service Creation Flow [5 steps] → Service Created → Services List
          │   └─→ Service Details
          │       └─→ Delete Confirmation → Service Deleted → Services List
          ├─→ Reviews List (paginated)
          ├─→ Statistics View
          ├─→ Calendar Settings
          ├─→ Settings View
          └─→ Support Flow [1 step] → Message Sent → Personal Cabinet
```

### Entry Point Resolution

```
/start command
  ↓
Resolve user role
  ↓
Main Menu (with role indicator)
```

### Profile Status Handling

```
Nutritionist Menu
  ├─ No profile → Show "Создать профиль"
  └─ Has profile → Show status + "Обновить профиль"
      ├─ draft → "Черновик"
      ├─ pending → "На модерации"
      ├─ approved → "Подтверждён"
      ├─ rejected → "Отклонён"
      └─ needs_update → "Требуются изменения"
```

---

## Dead-End Prevention

**All screens have exit paths:**
- ✅ Every FSM step has Cancel option
- ✅ Every terminal state has Back/Continue button
- ✅ Every list/view has Back navigation
- ✅ Error states allow retry or cancel
- ✅ Empty states provide guidance and navigation

**No dead-end states confirmed:**
- Profile flow: Can cancel at any step
- Service flow: Can cancel at any step
- Slot flow: Can cancel at any step
- Support flow: Can cancel
- All menu screens: Always have Back button
- All terminal states: Return to appropriate menu

---

## Special Cases

### Calendar OAuth
- External URL button opens browser
- Returns to Calendar Settings after completion
- Status updates on refresh

### WebApp Integration
- Main Menu → "Открыть мини-приложение"
- Opens external WebApp (not bot flow)
- User can return to bot anytime

### Pagination
- Bookings List: 10 items per page
- Reviews List: 5 items per page
- Always show Previous/Next when applicable
- Offset persisted in FSM state during session

### Multi-select Interactions
- Specializations: Toggle on/off, require at least 1
- Tags: Toggle on/off, optional (can skip)
- Screen updates immediately on toggle
- Done button only appears when selection made

### Validation and Errors
- All input validated before progression
- Error messages show in same screen
- User can correct and retry
- Cancel always available to exit

---

## Summary

**Total Screens:** 19 unique screens (excluding flow steps)

**FSM Flows:**
- Profile Creation: 8 screens (7 steps + terminal)
- Service Creation: 6 screens (5 steps + terminal)
- Add Slot: 5 screens (4 steps + terminal)
- Support: 2 screens (1 step + terminal)

**Non-FSM Screens:** 14 screens (menus, lists, views)

**Navigation Type Distribution:**
- Reply Navigation: 8 input steps
- Inline Navigation: All other screens (31+)

**Owner Distribution:**
- Nutritionist: All screens
- System: Start/Welcome (temporary)

**Entry Points:** 2 (command + menu button)

**Terminal States:** 6 (all with exit paths)

✅ **No dead-end states** — every screen has clear exit path.
