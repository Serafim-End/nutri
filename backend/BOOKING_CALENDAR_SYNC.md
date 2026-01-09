# Booking Google Calendar Sync

## Overview

This document describes the Google Calendar synchronization for bookings. The sync is idempotent and has no side effects when Google Calendar is not connected.

## Booking States

The booking model uses the following states (defined in `app/models/booking.py`):

- `pending_payment` - Initial state, waiting for payment
- `paid` - **Triggers calendar event creation**
- `cancelled` - **Triggers calendar event deletion**
- `completed` - Consultation completed
- `no_show` - Client didn't show up
- `refunded` - Payment refunded

## Calendar Sync Triggers

### 1. Booking Paid → Create Event

**Trigger:** When booking status transitions to `paid`

**Location:** `PaymentService.finalize_payment()` (line ~253)

**Flow:**
1. `PaymentService.finalize_payment()` sets `booking.status = "paid"`
2. Calls `BookingCalendarSync.sync_booking_paid(booking)`
3. If Google Calendar connected and event doesn't exist:
   - Creates calendar event via `GoogleCalendarService.create_event()`
   - Stores event ID in `booking.google_calendar_event_id`
4. If Google Calendar not connected: No side effects, logs debug message

**Idempotency:** If `booking.google_calendar_event_id` already exists, skips creation.

### 2. Booking Cancelled → Delete Event

**Trigger:** When booking status transitions to `cancelled`

**Locations:**
- `BookingHoldService.cancel_booking()` (line ~390)
- `BookingHoldService.release_expired_holds()` (line ~200)

**Flow:**
1. Booking status set to `cancelled`
2. Calls `BookingCalendarSync.sync_booking_cancelled(booking)`
3. If Google Calendar connected and event exists:
   - Deletes calendar event via `GoogleCalendarService.delete_event()`
   - Clears `booking.google_calendar_event_id`
4. If Google Calendar not connected: No side effects, logs debug message

**Idempotency:** 
- If `booking.google_calendar_event_id` is None, skips deletion
- If event already deleted (404), treats as success (idempotent)

## Implementation Details

### Google Calendar Service

**File:** `app/services/google_calendar.py`

**Scopes Required:**
- `https://www.googleapis.com/auth/calendar.readonly`
- `https://www.googleapis.com/auth/calendar.freebusy`
- `https://www.googleapis.com/auth/calendar.events` (for creating/deleting events)

**Methods:**
- `create_event()` - Creates a calendar event, returns event ID
- `delete_event()` - Deletes a calendar event, handles 404 gracefully

### Booking Calendar Sync Service

**File:** `app/services/booking_calendar_sync.py`

**Methods:**
- `sync_booking_paid(booking)` - Creates calendar event when booking is paid
- `sync_booking_cancelled(booking)` - Deletes calendar event when booking is cancelled

**Key Features:**
- Idempotent operations (safe to call multiple times)
- No side effects if Google Calendar not connected
- Non-blocking (wrapped in try/except, doesn't fail main flow)

## Database Schema

**Migration:** `20250102_000001_add_google_calendar_event_id_to_bookings.py`

**Field Added:**
- `bookings.google_calendar_event_id` (String(255), nullable, indexed)

## Tests

**File:** `tests/test_booking_calendar_sync.py`

**Coverage:**
- ✅ Creating events when bookings are paid
- ✅ Deleting events when bookings are cancelled
- ✅ Idempotency (multiple calls)
- ✅ No side effects when Google Calendar not connected
- ✅ Integration with payment finalization
- ✅ Integration with booking cancellation
- ✅ Handling 404 (event already deleted)

## Error Handling

All calendar sync operations are wrapped in try/except blocks and log warnings on failure. They never raise exceptions that would affect the main booking flow.

**Example:**
```python
try:
    BookingCalendarSync.sync_booking_paid(booking)
except Exception as e:
    logger.warning(f"Failed to sync booking to calendar: {e}")
```

## Removed Unused Helpers

The following unused methods were removed from `BookingHoldService`:
- `mark_booking_paid()` - Replaced by `PaymentService.finalize_payment()`
- `confirm_booking()` - Alias for `mark_booking_paid()`, also unused

Payment finalization now goes through `PaymentService.finalize_payment()` which includes calendar sync.
