# Working Hours Template & Date Exceptions API Usage

## Overview
This document describes the backend APIs for managing weekly working hours templates and date exceptions for nutritionists. These APIs support the Calendar Settings screen (UX_MAP screen 17).

## Endpoints

### Working Hours Template

#### `GET /api/nutritionists/<nutritionist_id>/working-hours-template`
**Purpose:** Retrieve the weekly working hours template for a nutritionist.

**Used in:**
- **UX_MAP Screen 17: Calendar Settings** - When displaying current working hours configuration

**Response:**
```json
{
  "template": {
    "id": "uuid",
    "nutritionist_id": "uuid",
    "weekly_schedule": {
      "0": [{"start": "09:00", "end": "12:00"}, {"start": "14:00", "end": "18:00"}],
      "1": [{"start": "09:00", "end": "12:00"}],
      ...
    },
    "created_at": "2024-12-30T00:00:00",
    "updated_at": "2024-12-30T00:00:00"
  }
}
```

**Notes:**
- Day numbers: 0=Monday, 6=Sunday
- Returns empty template if none exists

---

#### `PUT /api/nutritionists/<nutritionist_id>/working-hours-template`
**Purpose:** Create or update the weekly working hours template.

**Used in:**
- **UX_MAP Screen 17: Calendar Settings** - When nutritionist saves their weekly schedule

**Request:**
```json
{
  "weekly_schedule": {
    "0": [{"start": "09:00", "end": "12:00"}, {"start": "14:00", "end": "18:00"}],
    "1": [{"start": "09:00", "end": "12:00"}],
    "2": [],
    ...
  }
}
```

**Response:**
```json
{
  "template": {
    "id": "uuid",
    "nutritionist_id": "uuid",
    "weekly_schedule": {...},
    "created_at": "2024-12-30T00:00:00",
    "updated_at": "2024-12-30T00:00:00"
  }
}
```

---

### Date Exceptions

#### `GET /api/nutritionists/<nutritionist_id>/date-exceptions`
**Purpose:** List all date exceptions for a nutritionist.

**Used in:**
- **UX_MAP Screen 17: Calendar Settings** - When displaying list of exceptions (holidays, custom hours)

**Query Parameters:**
- `start_date` (optional): Filter from date (YYYY-MM-DD)
- `end_date` (optional): Filter to date (YYYY-MM-DD)

**Response:**
```json
{
  "exceptions": [
    {
      "id": "uuid",
      "nutritionist_id": "uuid",
      "exception_date": "2024-12-31",
      "exception_type": "off",
      "custom_hours": null,
      "created_at": "2024-12-30T00:00:00",
      "updated_at": "2024-12-30T00:00:00"
    },
    {
      "id": "uuid",
      "nutritionist_id": "uuid",
      "exception_date": "2025-01-01",
      "exception_type": "custom",
      "custom_hours": [{"start": "10:00", "end": "14:00"}],
      "created_at": "2024-12-30T00:00:00",
      "updated_at": "2024-12-30T00:00:00"
    }
  ],
  "total": 2
}
```

---

#### `POST /api/nutritionists/<nutritionist_id>/date-exceptions`
**Purpose:** Create a new date exception (day off or custom hours).

**Used in:**
- **UX_MAP Screen 17: Calendar Settings** - When nutritionist adds a holiday or custom hours for a specific date

**Request:**
```json
{
  "exception_date": "2024-12-31",
  "exception_type": "off"
}
```

or

```json
{
  "exception_date": "2025-01-01",
  "exception_type": "custom",
  "custom_hours": [{"start": "10:00", "end": "14:00"}]
}
```

**Response:**
```json
{
  "exception": {
    "id": "uuid",
    "nutritionist_id": "uuid",
    "exception_date": "2024-12-31",
    "exception_type": "off",
    "custom_hours": null,
    "created_at": "2024-12-30T00:00:00",
    "updated_at": "2024-12-30T00:00:00"
  }
}
```

**Error Codes:**
- `409`: Exception already exists for this date

---

#### `GET /api/nutritionists/<nutritionist_id>/date-exceptions/<exception_id>`
**Purpose:** Get a specific date exception by ID.

**Used in:**
- **UX_MAP Screen 17: Calendar Settings** - When viewing/editing a specific exception

**Response:**
```json
{
  "exception": {
    "id": "uuid",
    "nutritionist_id": "uuid",
    "exception_date": "2024-12-31",
    "exception_type": "off",
    "custom_hours": null,
    "created_at": "2024-12-30T00:00:00",
    "updated_at": "2024-12-30T00:00:00"
  }
}
```

---

#### `PUT /api/nutritionists/<nutritionist_id>/date-exceptions/<exception_id>`
**Purpose:** Update an existing date exception.

**Used in:**
- **UX_MAP Screen 17: Calendar Settings** - When nutritionist modifies an exception (e.g., change from "off" to "custom" hours)

**Request:**
```json
{
  "exception_type": "custom",
  "custom_hours": [{"start": "10:00", "end": "14:00"}]
}
```

**Response:**
```json
{
  "exception": {
    "id": "uuid",
    "nutritionist_id": "uuid",
    "exception_date": "2024-12-31",
    "exception_type": "custom",
    "custom_hours": [{"start": "10:00", "end": "14:00"}],
    "created_at": "2024-12-30T00:00:00",
    "updated_at": "2024-12-30T00:00:00"
  }
}
```

---

#### `DELETE /api/nutritionists/<nutritionist_id>/date-exceptions/<exception_id>`
**Purpose:** Delete a date exception.

**Used in:**
- **UX_MAP Screen 17: Calendar Settings** - When nutritionist removes an exception

**Response:**
```json
{
  "message": "Exception deleted"
}
```

---

## Data Models

### WorkingHoursTemplate
- One template per nutritionist (unique constraint on `nutritionist_id`)
- `weekly_schedule`: JSONB storing `{day_number: [time_ranges]}`
  - Day numbers: 0=Monday, 1=Tuesday, ..., 6=Sunday
  - Time ranges: `[{"start": "HH:MM", "end": "HH:MM"}, ...]`

### DateException
- Multiple exceptions per nutritionist
- Unique constraint: `(nutritionist_id, exception_date)`
- `exception_type`: "off" or "custom"
- `custom_hours`: JSONB array of time ranges (null for "off" type)

---

## UX_MAP Reference

**Screen 17: Calendar Settings**
- Entry: Personal Cabinet → "Календарь"
- Exit: "Назад" → Personal Cabinet
- Content: Connection status, instructions, benefits

**Note:** The UX_MAP mentions Google Calendar, but per requirements, we only implement the data model and APIs. The actual calendar integration UI is not part of this scope.

---

## Authentication

All endpoints use `@jwt_required(optional=True)`, meaning:
- Authentication is optional (for bot integration)
- If authenticated, user must be the nutritionist or admin
- Authorization checks should be added in the bot/frontend layer

---

## Validation Rules

1. **Time Format:** HH:MM (24-hour format, e.g., "09:00", "18:30")
2. **Time Range:** End time must be after start time
3. **Day Numbers:** 0-6 (Monday=0, Sunday=6)
4. **Exception Type:** "off" or "custom"
5. **Custom Hours:** Required when `exception_type="custom"`, ignored when `exception_type="off"`
6. **Date Uniqueness:** Only one exception per date per nutritionist
