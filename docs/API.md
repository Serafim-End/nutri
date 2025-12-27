# NutriMatch API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication

All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

### Obtain Token

```http
POST /auth/telegram/verify
Content-Type: application/json

{
  "init_data": "<Telegram Mini App initData string>"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "profile": {
    "id": "uuid",
    "role": "client",
    "telegram_user_id": 123456789,
    "full_name": "John Doe",
    "photo_url": null,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

**Development Mode:**
In debug mode, use test data: `test_<telegram_user_id>_<first_name>_<last_name>`

---

## Client Endpoints

### Submit Intake

```http
POST /clients/intakes
Authorization: Bearer <token>
Content-Type: application/json

{
  "goals": ["weight_loss", "better_nutrition"],
  "dietary_restrictions": ["vegetarian"],
  "budget_min": 2000,
  "budget_max": 5000,
  "preferred_schedule": "weekends",
  "health_conditions": [],
  "additional_notes": "Looking for long-term support"
}
```

**Response:**
```json
{
  "intake": {
    "id": "uuid",
    "client_id": "uuid",
    "answers": {...},
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  },
  "message": "Intake submitted successfully"
}
```

### Get Matches

```http
GET /clients/matches?intake_id=<uuid>
Authorization: Bearer <token>
```

**Response:**
```json
{
  "matches": [
    {
      "nutritionist_id": "uuid",
      "bio": "Certified nutritionist...",
      "tags": ["vegetarian"],
      "specializations": ["weight_loss"],
      "rating": 4.85,
      "reviews_count": 47,
      "profile": {
        "full_name": "Dr. Elena Petrova",
        "photo_url": "https://..."
      }
    }
  ],
  "total": 1
}
```

### List Bookings

```http
GET /clients/bookings
Authorization: Bearer <token>
```

---

## Public Endpoints

### List Nutritionists

```http
GET /public/nutritionists?specialization=weight_loss&budget=5000
```

**Query Parameters:**
- `specialization` (optional): Filter by specialization
- `budget` (optional): Maximum price filter
- `tags` (optional): Filter by tags (can be repeated)

### Get Nutritionist

```http
GET /public/nutritionists/<nutritionist_id>
```

### List Services

```http
GET /public/nutritionists/<nutritionist_id>/services
```

### List Available Slots

```http
GET /public/nutritionists/<nutritionist_id>/slots?service_id=<uuid>
```

---

## Booking Endpoints

### Create Booking

Creates a booking and holds the slot for 10 minutes.

```http
POST /bookings
Authorization: Bearer <token>
Content-Type: application/json

{
  "service_id": "uuid",
  "slot_id": "uuid"
}
```

**Response:**
```json
{
  "booking": {
    "id": "uuid",
    "client_id": "uuid",
    "nutritionist_id": "uuid",
    "service_id": "uuid",
    "slot_id": "uuid",
    "status": "pending_payment",
    "price_rub": 3000,
    "currency": "RUB",
    "created_at": "2024-01-01T00:00:00"
  },
  "payment": {
    "payment_id": "uuid",
    "provider": "telegram",
    "amount_rub": 3000,
    "currency": "RUB",
    "payment_url": "https://pay.example.com/...",
    "expires_at": "2024-01-01T00:10:00"
  }
}
```

### Cancel Booking

```http
POST /bookings/<booking_id>/cancel
Authorization: Bearer <token>
Content-Type: application/json

{
  "reason": "Changed my mind"
}
```

### Release Expired Holds (Cron)

```http
POST /bookings/release-expired-holds
```

---

## Payment Endpoints

### Payment Webhook

```http
POST /payments/webhook
Content-Type: application/json

{
  "provider": "telegram",
  "payment_id": "provider_payment_123",
  "booking_id": "uuid",
  "amount_rub": 3000,
  "status": "succeeded",
  "signature": "hmac_signature"
}
```

**Signature Verification:**
```
message = f"{booking_id}:{payment_id}:{amount_rub}"
signature = HMAC-SHA256(PAYMENT_WEBHOOK_SECRET, message)
```

---

## Nutritionist Endpoints (Botpress)

### Upsert Profile

```http
POST /nutritionists/upsert
Content-Type: application/json

{
  "telegram_user_id": 123456789,
  "full_name": "Dr. Jane Smith",
  "photo_url": "https://example.com/photo.jpg",
  "bio": "Certified nutritionist...",
  "tags": ["vegetarian", "sports_nutrition"],
  "specializations": ["weight_loss", "diabetes"],
  "submit_for_verification": true
}
```

### Add Document

```http
POST /nutritionists/<nutritionist_id>/documents
Content-Type: application/json

{
  "type": "diploma",
  "file_path": "https://storage.example.com/doc.pdf"
}
```

**Document Types:** `diploma`, `certificate`, `other`

### Create Service

```http
POST /nutritionists/<nutritionist_id>/services
Content-Type: application/json

{
  "title": "Initial Consultation",
  "description": "60-minute comprehensive assessment",
  "duration_minutes": 60,
  "price_rub": 3000,
  "is_active": true
}
```

### Create Slots (Bulk)

```http
POST /nutritionists/<nutritionist_id>/slots
Content-Type: application/json

{
  "slots": [
    {
      "start_at": "2024-01-15T10:00:00Z",
      "end_at": "2024-01-15T11:00:00Z"
    },
    {
      "start_at": "2024-01-15T14:00:00Z",
      "end_at": "2024-01-15T15:00:00Z"
    }
  ]
}
```

### Get Dashboard

```http
GET /nutritionists/<nutritionist_id>/dashboard
```

**Response:**
```json
{
  "nutritionist": {...},
  "services": [...],
  "upcoming_slots": [...],
  "stats": {
    "total_bookings": 10,
    "completed_bookings": 8,
    "total_earnings_rub": 24000
  }
}
```

---

## Admin Endpoints

All admin endpoints require `role: admin` in the JWT.

### List Pending Nutritionists

```http
GET /admin/nutritionists?status=pending
Authorization: Bearer <admin_token>
```

### Approve Nutritionist

```http
POST /admin/nutritionists/<nutritionist_id>/approve
Authorization: Bearer <admin_token>
```

### Reject Nutritionist

```http
POST /admin/nutritionists/<nutritionist_id>/reject
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "reason": "Missing required documents"
}
```

---

## Error Responses

**400 Bad Request:**
```json
{
  "error": "Validation error",
  "details": [...]
}
```

**401 Unauthorized:**
```json
{
  "error": "Invalid or expired initData"
}
```

**403 Forbidden:**
```json
{
  "error": "Not authorized"
}
```

**404 Not Found:**
```json
{
  "error": "Resource not found"
}
```

---

## Status Enums

### Verification Status
- `draft` - Initial state
- `pending` - Submitted for review
- `approved` - Verified and active
- `rejected` - Verification failed
- `needs_update` - Changes requested

### Slot Status
- `free` - Available for booking
- `held` - Temporarily reserved
- `booked` - Confirmed booking
- `cancelled` - Cancelled

### Booking Status
- `pending_payment` - Waiting for payment
- `paid` - Payment confirmed
- `cancelled` - Cancelled by user
- `completed` - Consultation completed
- `no_show` - Client didn't show up
- `refunded` - Payment refunded

### Payment Status
- `created` - Payment initiated
- `succeeded` - Payment successful
- `failed` - Payment failed
- `refunded` - Payment refunded


