# cURL Examples for NutriMatch API

## Quick Reference

Base URL: `http://localhost:5000/api`

---

## Authentication

### Authenticate (Development Mode)

```bash
# Get JWT token with test data
curl -X POST http://localhost:5000/api/auth/telegram/verify \
  -H "Content-Type: application/json" \
  -d '{"init_data": "test_123456789_John_Doe"}'
```

### Dev Login (Stage 6 - Development Only)

```bash
# Login as the seeded client user (no Telegram required)
curl -X POST http://localhost:5000/api/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{"telegram_user_id": 300000001}'

# Available test users (after make seed):
# - Client: telegram_user_id = 300000001
# - Nutritionist (Elena): telegram_user_id = 200000001  
# - Nutritionist (Michael): telegram_user_id = 200000002
# - Admin: telegram_user_id = 100000001
```

Save the token:
```bash
export TOKEN="your-access-token-here"
```

---

## Client Flow

### 1. Submit Intake

```bash
curl -X POST http://localhost:5000/api/clients/intakes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "goals": ["weight_loss", "better_nutrition"],
    "dietary_restrictions": ["vegetarian"],
    "budget_min": 2000,
    "budget_max": 5000,
    "preferred_schedule": "weekends",
    "health_conditions": [],
    "additional_notes": "Looking for long-term support"
  }'
```

### 2. Get Matches

```bash
curl -X GET "http://localhost:5000/api/clients/matches?intake_id=YOUR_INTAKE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Browse Nutritionists (Public)

```bash
# List all
curl http://localhost:5000/api/public/nutritionists

# Filter by specialization
curl "http://localhost:5000/api/public/nutritionists?specialization=weight_loss"

# Filter by budget
curl "http://localhost:5000/api/public/nutritionists?budget=5000"
```

### 4. View Nutritionist Details

```bash
curl http://localhost:5000/api/public/nutritionists/NUTRITIONIST_ID
```

### 5. List Services

```bash
curl http://localhost:5000/api/public/nutritionists/NUTRITIONIST_ID/services
```

### 6. List Available Slots

```bash
curl "http://localhost:5000/api/public/nutritionists/NUTRITIONIST_ID/slots?service_id=SERVICE_ID"
```

### 7. Create Booking

```bash
curl -X POST http://localhost:5000/api/bookings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "service_id": "SERVICE_ID",
    "slot_id": "SLOT_ID"
  }'
```

### 8. Simulate Payment Success (Stage 6)

```bash
# Mark a pending booking as paid (atomic operation with slot lock)
curl -X POST http://localhost:5000/api/bookings/BOOKING_ID/mark-paid \
  -H "Authorization: Bearer $TOKEN"

# Legacy endpoint (still works)
curl -X POST http://localhost:5000/api/payments/test-success/BOOKING_ID
```

### 9. View Bookings

```bash
# List bookings (basic)
curl http://localhost:5000/api/clients/bookings \
  -H "Authorization: Bearer $TOKEN"

# List bookings with full details (Stage 6 - includes nutritionist info)
curl http://localhost:5000/api/clients/me/bookings \
  -H "Authorization: Bearer $TOKEN"
```

### 10. Cancel Booking

```bash
curl -X POST http://localhost:5000/api/bookings/BOOKING_ID/cancel \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"reason": "Changed my mind"}'
```

---

## Nutritionist Flow (Botpress)

### 1. Create/Update Profile

```bash
curl -X POST http://localhost:5000/api/nutritionists/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_user_id": 123456789,
    "full_name": "Dr. Jane Smith",
    "photo_url": "https://example.com/photo.jpg",
    "bio": "Certified nutritionist with 5 years of experience in sports nutrition and weight management.",
    "tags": ["vegetarian", "vegan", "sports_nutrition"],
    "specializations": ["weight_loss", "muscle_gain", "diabetes"],
    "submit_for_verification": false
  }'
```

### 2. Upload Document Metadata

```bash
curl -X POST http://localhost:5000/api/nutritionists/NUTRITIONIST_ID/documents \
  -H "Content-Type: application/json" \
  -d '{
    "type": "diploma",
    "file_path": "https://storage.supabase.co/documents/diploma.pdf"
  }'
```

### 3. Create Service

```bash
curl -X POST http://localhost:5000/api/nutritionists/NUTRITIONIST_ID/services \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Initial Consultation",
    "description": "Comprehensive 60-minute assessment of your health goals, current diet, and lifestyle. Includes personalized meal plan recommendations.",
    "duration_minutes": 60,
    "price_rub": 3000,
    "is_active": true
  }'
```

### 4. Create Multiple Slots

```bash
curl -X POST http://localhost:5000/api/nutritionists/NUTRITIONIST_ID/slots \
  -H "Content-Type: application/json" \
  -d '{
    "slots": [
      {"start_at": "2024-01-15T09:00:00Z", "end_at": "2024-01-15T10:00:00Z"},
      {"start_at": "2024-01-15T10:00:00Z", "end_at": "2024-01-15T11:00:00Z"},
      {"start_at": "2024-01-15T11:00:00Z", "end_at": "2024-01-15T12:00:00Z"},
      {"start_at": "2024-01-15T14:00:00Z", "end_at": "2024-01-15T15:00:00Z"},
      {"start_at": "2024-01-15T15:00:00Z", "end_at": "2024-01-15T16:00:00Z"}
    ]
  }'
```

### 5. Submit for Verification

```bash
curl -X POST http://localhost:5000/api/nutritionists/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_user_id": 123456789,
    "full_name": "Dr. Jane Smith",
    "submit_for_verification": true
  }'
```

### 6. View Dashboard

```bash
curl http://localhost:5000/api/nutritionists/NUTRITIONIST_ID/dashboard
```

---

## Admin Flow

### Get Admin Token

```bash
# First create an admin user via seed.py
# Then authenticate as admin (telegram_user_id: 100000001)
curl -X POST http://localhost:5000/api/auth/telegram/verify \
  -H "Content-Type: application/json" \
  -d '{"init_data": "test_100000001_Admin_User"}'

export ADMIN_TOKEN="admin-token-here"
```

### List Pending Nutritionists

```bash
curl http://localhost:5000/api/admin/nutritionists?status=pending \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Review Nutritionist Details

```bash
curl http://localhost:5000/api/admin/nutritionists/NUTRITIONIST_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Approve Nutritionist

```bash
curl -X POST http://localhost:5000/api/admin/nutritionists/NUTRITIONIST_ID/approve \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Reject Nutritionist

```bash
curl -X POST http://localhost:5000/api/admin/nutritionists/NUTRITIONIST_ID/reject \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"reason": "Missing required diploma documentation"}'
```

### Request Updates

```bash
curl -X POST http://localhost:5000/api/admin/nutritionists/NUTRITIONIST_ID/request-update \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"notes": "Please upload your diploma and update your bio with credentials"}'
```

### Review Document

```bash
curl -X POST http://localhost:5000/api/admin/documents/DOCUMENT_ID/review \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"status": "accepted", "note": "Verified diploma from accredited institution"}'
```

---

## Payment Webhook

### Simulate Success (Production Format)

```bash
curl -X POST http://localhost:5000/api/payments/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "telegram",
    "payment_id": "telegram_payment_12345",
    "booking_id": "BOOKING_ID",
    "amount_rub": 3000,
    "status": "succeeded",
    "signature": "test_signature"
  }'
```

### Simulate Failure

```bash
curl -X POST http://localhost:5000/api/payments/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "yookassa",
    "payment_id": "yookassa_payment_12345",
    "booking_id": "BOOKING_ID",
    "amount_rub": 3000,
    "status": "failed",
    "signature": "test_signature"
  }'
```

---

## Cron Jobs

### Release Expired Holds

Run every 5 minutes:
```bash
curl -X POST http://localhost:5000/api/bookings/release-expired-holds
```

---

## Health Check

```bash
curl http://localhost:5000/health
```

Response:
```json
{"status": "healthy", "service": "nutrimatch-api"}
```

---

## Stage 6: Complete Booking Flow Example

Here's a complete flow from start to finish:

```bash
# 1. Dev login (get token)
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{"telegram_user_id": 300000001}' | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. List nutritionists
curl -s http://localhost:5000/api/public/nutritionists | jq '.nutritionists[0]'

# 3. Get nutritionist ID and services
NUTRI_ID=$(curl -s http://localhost:5000/api/public/nutritionists | jq -r '.nutritionists[0].nutritionist_id')
curl -s http://localhost:5000/api/public/nutritionists/$NUTRI_ID/services | jq

# 4. Get service ID and available slots
SERVICE_ID=$(curl -s http://localhost:5000/api/public/nutritionists/$NUTRI_ID/services | jq -r '.services[0].id')
curl -s "http://localhost:5000/api/public/nutritionists/$NUTRI_ID/slots?service_id=$SERVICE_ID" | jq

# 5. Get slot ID and create booking
SLOT_ID=$(curl -s "http://localhost:5000/api/public/nutritionists/$NUTRI_ID/slots?service_id=$SERVICE_ID" | jq -r '.slots[0].id')
BOOKING=$(curl -s -X POST http://localhost:5000/api/bookings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"service_id\": \"$SERVICE_ID\", \"slot_id\": \"$SLOT_ID\"}")
echo "$BOOKING" | jq

# 6. Extract booking ID and hold expiration
BOOKING_ID=$(echo "$BOOKING" | jq -r '.booking.id')
HOLD_EXPIRES=$(echo "$BOOKING" | jq -r '.booking.slot.hold_expires_at')
echo "Booking ID: $BOOKING_ID"
echo "Hold expires at: $HOLD_EXPIRES"

# 7. Simulate payment success (before hold expires!)
curl -s -X POST http://localhost:5000/api/bookings/$BOOKING_ID/mark-paid \
  -H "Authorization: Bearer $TOKEN" | jq

# 8. View my bookings
curl -s http://localhost:5000/api/clients/me/bookings \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Testing Hold Expiration

```bash
# 1. Create a booking (as above)
# 2. Wait for hold to expire (10 minutes by default)
# 3. Release expired holds
curl -X POST http://localhost:5000/api/bookings/release-expired-holds

# 4. Check booking status (should be cancelled)
curl -s http://localhost:5000/api/bookings/$BOOKING_ID \
  -H "Authorization: Bearer $TOKEN" | jq '.booking.status'
```

### Testing Race Conditions

```bash
# Open two terminals and run simultaneously:

# Terminal 1:
SLOT_ID="your-slot-id"
curl -X POST http://localhost:5000/api/bookings \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d "{\"service_id\": \"$SERVICE_ID\", \"slot_id\": \"$SLOT_ID\"}"

# Terminal 2:
curl -X POST http://localhost:5000/api/bookings \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d "{\"service_id\": \"$SERVICE_ID\", \"slot_id\": \"$SLOT_ID\"}"

# Only one should succeed (201), the other gets 409 Conflict
```


