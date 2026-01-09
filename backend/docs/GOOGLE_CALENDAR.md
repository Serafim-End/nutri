# Google Calendar Integration

This document describes the Google Calendar integration for nutritionists, including how to use the freeBusy output.

## Overview

The Google Calendar integration allows nutritionists to:
1. Connect their Google Calendar account via OAuth
2. List available calendars
3. Select a calendar to use for availability checks
4. Query free/busy information from the selected calendar

## API Endpoints

### Connect Google Calendar

**GET** `/api/nutritionists/<nutritionist_id>/calendar/connect`

Returns the OAuth authorization URL. Redirect the user to this URL to authorize access.

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

### OAuth Callback

**GET** `/api/nutritionists/<nutritionist_id>/calendar/callback?code=<auth_code>&state=<nutritionist_id>`

Handles the OAuth callback from Google. This endpoint is called by Google after user authorization.

**Response:**
```json
{
  "calendar": {
    "id": "uuid",
    "nutritionist_id": "uuid",
    "is_connected": true,
    "selected_calendar_id": null,
    "selected_calendar_summary": null,
    "connected_at": "2024-01-01T00:00:00Z"
  }
}
```

### Disconnect Google Calendar

**POST** `/api/nutritionists/<nutritionist_id>/calendar/disconnect`

Disconnects the Google Calendar connection.

**Response:**
```json
{
  "message": "Calendar disconnected"
}
```

### Get Connection Status

**GET** `/api/nutritionists/<nutritionist_id>/calendar/status`

Returns the current connection status.

**Response:**
```json
{
  "calendar": {
    "id": "uuid",
    "nutritionist_id": "uuid",
    "is_connected": true,
    "selected_calendar_id": "test@example.com",
    "selected_calendar_summary": "Test Calendar",
    "connected_at": "2024-01-01T00:00:00Z"
  }
}
```

### List Calendars

**GET** `/api/nutritionists/<nutritionist_id>/calendar/calendars`

Lists all calendars available to the nutritionist.

**Response:**
```json
{
  "calendars": [
    {
      "id": "primary",
      "summary": "Primary Calendar",
      "primary": true,
      "accessRole": "owner",
      "backgroundColor": "#9fe1e7",
      "foregroundColor": "#000000"
    },
    {
      "id": "test@example.com",
      "summary": "Test Calendar",
      "primary": false,
      "accessRole": "owner"
    }
  ]
}
```

### Select Calendar

**POST** `/api/nutritionists/<nutritionist_id>/calendar/select`

Selects a calendar to use for freebusy queries.

**Request:**
```json
{
  "calendar_id": "test@example.com"
}
```

**Response:**
```json
{
  "calendar": {
    "id": "uuid",
    "nutritionist_id": "uuid",
    "is_connected": true,
    "selected_calendar_id": "test@example.com",
    "selected_calendar_summary": "Test Calendar"
  }
}
```

### Get Free/Busy Information

**POST** `/api/nutritionists/<nutritionist_id>/calendar/freebusy`

Returns free/busy information for the selected calendar.

**Request:**
```json
{
  "time_min": "2024-01-01T00:00:00Z",
  "time_max": "2024-01-01T23:59:59Z"
}
```

**Response:**
```json
{
  "calendars": {
    "test@example.com": {
      "busy": [
        {
          "start": "2024-01-01T10:00:00Z",
          "end": "2024-01-01T11:00:00Z"
        },
        {
          "start": "2024-01-01T14:00:00Z",
          "end": "2024-01-01T15:30:00Z"
        }
      ]
    }
  },
  "timeMin": "2024-01-01T00:00:00Z",
  "timeMax": "2024-01-01T23:59:59Z"
}
```

## Consuming FreeBusy Output

The freeBusy output can be consumed in several ways:

### 1. Generate Availability Slots (source="calendar")

Use the freeBusy data to create availability slots by inverting the busy periods:

```python
from datetime import datetime, timedelta
from app.models import AvailabilitySlot

def generate_slots_from_freebusy(nutritionist_id, freebusy_result, time_min, time_max):
    """
    Generate availability slots from freebusy data.
    Creates slots for free periods (gaps between busy periods).
    """
    calendar_id = list(freebusy_result["calendars"].keys())[0]
    busy_periods = freebusy_result["calendars"][calendar_id].get("busy", [])
    
    # Parse busy periods
    busy_ranges = []
    for period in busy_periods:
        start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
        busy_ranges.append((start, end))
    
    # Sort by start time
    busy_ranges.sort(key=lambda x: x[0])
    
    # Generate free slots (gaps between busy periods)
    slots = []
    current_time = time_min
    
    for busy_start, busy_end in busy_ranges:
        # If there's a gap before this busy period, create a slot
        if current_time < busy_start:
            slot = AvailabilitySlot(
                nutritionist_id=nutritionist_id,
                start_at=current_time,
                end_at=busy_start,
                status="free",
                source="calendar",  # Mark as calendar-generated
            )
            slots.append(slot)
        current_time = max(current_time, busy_end)
    
    # Add final slot if there's time remaining
    if current_time < time_max:
        slot = AvailabilitySlot(
            nutritionist_id=nutritionist_id,
            start_at=current_time,
            end_at=time_max,
            status="free",
            source="calendar",
        )
        slots.append(slot)
    
    return slots
```

### 2. Filter Out Busy Times

When showing available slots, filter out times that are busy in Google Calendar:

```python
def filter_busy_slots(slots, freebusy_result):
    """
    Filter out slots that overlap with busy periods.
    """
    calendar_id = list(freebusy_result["calendars"].keys())[0]
    busy_periods = freebusy_result["calendars"][calendar_id].get("busy", [])
    
    # Parse busy periods
    busy_ranges = []
    for period in busy_periods:
        start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
        busy_ranges.append((start, end))
    
    # Filter slots that don't overlap with busy periods
    available_slots = []
    for slot in slots:
        slot_start = slot.start_at
        slot_end = slot.end_at
        
        # Check if slot overlaps with any busy period
        is_busy = any(
            not (slot_end <= busy_start or slot_start >= busy_end)
            for busy_start, busy_end in busy_ranges
        )
        
        if not is_busy:
            available_slots.append(slot)
    
    return available_slots
```

### 3. Sync Calendar Events with Availability Slots

Periodically sync calendar events to keep availability slots up to date:

```python
from app.services.google_calendar import GoogleCalendarService

def sync_calendar_availability(nutritionist_id):
    """
    Sync Google Calendar freebusy with availability slots.
    This can be called periodically (e.g., via cron job).
    """
    # Get freebusy for next 30 days
    time_min = datetime.now(timezone.utc)
    time_max = time_min + timedelta(days=30)
    
    freebusy_result = GoogleCalendarService.get_freebusy(
        nutritionist_id, time_min, time_max
    )
    
    # Generate or update slots based on freebusy data
    slots = generate_slots_from_freebusy(
        nutritionist_id, freebusy_result, time_min, time_max
    )
    
    # Save slots to database
    for slot in slots:
        # Check if slot already exists
        existing = AvailabilitySlot.query.filter_by(
            nutritionist_id=nutritionist_id,
            start_at=slot.start_at,
            end_at=slot.end_at,
            source="calendar",
        ).first()
        
        if not existing:
            db.session.add(slot)
    
    db.session.commit()
```

## Configuration

Set the following environment variables:

- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `GOOGLE_REDIRECT_URI`: OAuth redirect URI (can include `{nutritionist_id}` placeholder)

Example:
```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5000/api/nutritionists/{nutritionist_id}/calendar/callback
```

## Notes

- The integration uses OAuth 2.0 with offline access to get refresh tokens
- Tokens are automatically refreshed when expired
- Only the selected calendar is used for freebusy queries
- The `source` field in `AvailabilitySlot` can be set to `"calendar"` to distinguish calendar-generated slots from manual ones
