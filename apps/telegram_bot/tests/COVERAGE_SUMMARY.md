# Test Coverage Summary for Nutritionist Bot Flows

This document summarizes test coverage for all flows defined in `UX_MAP_NUTRITIONIST.md`.

## Test Files

1. **test_handlers_start.py** - Entry points and `/start` command
2. **test_handlers_menu.py** - Main menu and nutritionist menu navigation
3. **test_handlers_profile.py** - Profile creation flow (basic steps)
4. **test_handlers_profile_extended.py** - Profile creation flow (extended: photo, tags, rules, cancel)
5. **test_handlers_services.py** - Service creation flow
6. **test_handlers_services_extended.py** - Service details, toggle, delete
7. **test_handlers_schedule.py** - Schedule view, add slot flow, delete slot flow
8. **test_handlers_cabinet.py** - Personal cabinet views (reviews, statistics, calendar, settings, support)

## Flow Coverage

### ✅ Entry Points
- [x] `/start` command → Main Menu
- [x] Main Menu → "Для нутрициологов" → Nutritionist Menu

### ✅ Main Menu
- [x] Shows WebApp button
- [x] Shows nutritionist role message
- [x] Clears FSM state on start

### ✅ Nutritionist Menu
- [x] Shows options for new users ("Я нутрициолог", "Создать профиль")
- [x] Shows options for existing nutritionists ("Обновить профиль", "Личный кабинет")
- [x] Shows verification status
- [x] "Я нутрициолог" creates profile

### ✅ Profile Creation Flow (7 steps + terminal)
- [x] Step 1: Full Name input (validation: min 2, max 100 chars)
- [x] Step 2: Photo upload (skip option)
- [x] Step 3: Bio input (validation: max 300 chars, skip option)
- [x] Step 4: Specializations multi-select (toggle, require at least 1)
- [x] Step 5: Tags multi-select (toggle, optional, can skip)
- [x] Step 6: Rules confirmation
- [x] Step 7: Final confirmation with summary
- [x] Terminal: Profile Submitted
- [x] Cancel at any step

### ✅ Personal Cabinet
- [x] Shows cabinet with stats
- [x] Shows error without profile
- [x] Has all menu options

### ✅ Services List
- [x] Shows empty state
- [x] Shows services list with status and price

### ✅ Service Creation Flow (5 steps + terminal)
- [x] Step 1: Title input (validation: 3-100 chars)
- [x] Step 2: Description input (optional, max 500 chars, skip option)
- [x] Step 3: Duration input (validation: 15-240 minutes)
- [x] Step 4: Price input (validation: 100-100000₽)
- [x] Step 5: Confirmation with summary
- [x] Terminal: Service Created
- [x] Cancel at any step

### ✅ Service Details
- [x] Shows service details (title, description, duration, price, status)
- [x] Shows active/inactive status
- [x] Error for non-existent service

### ✅ Service Toggle
- [x] Toggle service to active
- [x] Toggle service to inactive
- [x] Updates local cache

### ✅ Service Deletion
- [x] Shows delete confirmation
- [x] Deletes service successfully
- [x] Error handling for deletion failures
- [x] Terminal: Service Deleted

### ✅ Schedule View
- [x] Shows empty schedule
- [x] Shows slots grouped by date
- [x] Clears FSM state

### ✅ Add Slot Flow (4 steps + terminal)
- [x] Step 1: Date selection (next 14 days)
- [x] Step 2: Start time input (HH:MM format, must be future)
- [x] Step 3: Duration selection (30/45/60/90 min)
- [x] Step 4: Confirmation
- [x] Terminal: Slot Created
- [x] Cancel at any step
- [x] Validation: time format, past time error

### ✅ Delete Slot Flow
- [x] Shows only free slots for deletion
- [x] Shows message when no free slots
- [x] Deletes slot successfully
- [x] Terminal: Slot Deleted

### ✅ Bookings List
- [x] Shows empty bookings
- [x] Shows bookings with pagination
- [x] Pagination (next/prev)

### ✅ Reviews List
- [x] Shows empty reviews
- [x] Shows reviews with rating and comments
- [x] Pagination (next/prev)

### ✅ Statistics View
- [x] Shows statistics (income, consultations, rating, clients)
- [x] Falls back to dashboard stats if statistics endpoint fails

### ✅ Calendar Settings
- [x] Shows connected calendar status
- [x] Shows disconnected calendar with OAuth button

### ✅ Settings View
- [x] Shows cancellation policy

### ✅ Support Flow (1 step + terminal)
- [x] Step 1: Message input (validation: 1-1000 chars)
- [x] Terminal: Message Sent
- [x] Cancel option
- [x] Empty message error
- [x] Too long message error

## Test Statistics

- **Total test files**: 8
- **Total test classes**: ~30
- **Total test methods**: ~80+

## Coverage Verification

All flows from `UX_MAP_NUTRITIONIST.md` are covered:

✅ **Entry Points**: 2/2
✅ **FSM Flows**: 4/4 (Profile, Service, Add Slot, Support)
✅ **Non-FSM Screens**: 14/14
✅ **Terminal States**: 6/6
✅ **Navigation**: All transitions tested
✅ **Validation**: All input validations tested
✅ **Error Handling**: All error cases tested

## Notes

- All tests mock the backend API client
- Tests focus on bot behavior and state transitions
- No backend assertions (as per requirements)
- Tests verify Russian text in responses
- Tests verify FSM state transitions
- Tests verify keyboard/button presence
