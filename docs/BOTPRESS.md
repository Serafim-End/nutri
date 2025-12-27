# Botpress Integration Guide

This guide explains how to integrate Botpress with the NutriMatch API for nutritionist onboarding.

## Overview

Botpress bots handle the nutritionist-facing workflow:
1. Collect profile information via conversational UI
2. Guide document upload process
3. Help set up services and availability
4. Track verification status

## API Endpoints for Botpress

### Base URL
```
https://your-api-domain.com/api
```

### Authentication

For Botpress integration, the nutritionist endpoints are currently open (no JWT required) for simplicity. In production, you may want to:

1. **Option A**: Use API keys for bot authentication
2. **Option B**: Implement a service account with admin privileges
3. **Option C**: Use Telegram bot identity verification

---

## Workflow 1: Nutritionist Onboarding

### Step 1: Create/Update Profile

When a nutritionist starts the onboarding process, create or update their profile:

```http
POST /api/nutritionists/upsert
Content-Type: application/json

{
  "telegram_user_id": 123456789,
  "full_name": "Dr. Jane Smith",
  "photo_url": "https://t.me/i/userpic/...",
  "bio": "Certified clinical nutritionist with 10 years of experience.",
  "tags": ["vegetarian", "vegan", "sports_nutrition"],
  "specializations": ["weight_loss", "diabetes", "gut_health"],
  "submit_for_verification": false
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `telegram_user_id` | integer | Yes | Telegram user ID |
| `full_name` | string | Yes | Full name |
| `photo_url` | string | No | Profile photo URL |
| `bio` | string | No | Professional bio |
| `tags` | string[] | No | Dietary tags they support |
| `specializations` | string[] | No | Areas of expertise |
| `submit_for_verification` | boolean | No | Submit for admin review |

**Response:**
```json
{
  "nutritionist": {
    "nutritionist_id": "uuid",
    "bio": "...",
    "verification_status": "draft",
    "profile": {
      "full_name": "Dr. Jane Smith",
      "telegram_user_id": 123456789
    }
  },
  "is_new": true
}
```

### Step 2: Upload Document Metadata

After the nutritionist uploads documents to your storage (Supabase Storage, S3, etc.), register the metadata:

```http
POST /api/nutritionists/{nutritionist_id}/documents
Content-Type: application/json

{
  "type": "diploma",
  "file_path": "https://storage.supabase.co/bucket/documents/diploma.pdf"
}
```

**Document Types:**
- `diploma` - Educational diploma
- `certificate` - Professional certification
- `other` - Other supporting documents

### Step 3: Create Services

Help the nutritionist set up their service offerings:

```http
POST /api/nutritionists/{nutritionist_id}/services
Content-Type: application/json

{
  "title": "Initial Consultation",
  "description": "60-minute comprehensive health assessment",
  "duration_minutes": 60,
  "price_rub": 3000,
  "is_active": true
}
```

### Step 4: Set Up Availability

Create availability slots in bulk:

```http
POST /api/nutritionists/{nutritionist_id}/slots
Content-Type: application/json

{
  "slots": [
    {"start_at": "2024-01-15T09:00:00Z", "end_at": "2024-01-15T10:00:00Z"},
    {"start_at": "2024-01-15T10:00:00Z", "end_at": "2024-01-15T11:00:00Z"},
    {"start_at": "2024-01-15T14:00:00Z", "end_at": "2024-01-15T15:00:00Z"}
  ]
}
```

**Tips for Generating Slots:**
- Ask nutritionist for weekly availability pattern
- Generate recurring slots programmatically
- Slot duration should match service duration

### Step 5: Submit for Verification

Once the profile is complete:

```http
POST /api/nutritionists/upsert
Content-Type: application/json

{
  "telegram_user_id": 123456789,
  "full_name": "Dr. Jane Smith",
  "submit_for_verification": true
}
```

This changes the status from `draft` to `pending`.

---

## Workflow 2: Dashboard & Status Check

### Get Dashboard Data

```http
GET /api/nutritionists/{nutritionist_id}/dashboard
```

**Response:**
```json
{
  "nutritionist": {
    "nutritionist_id": "uuid",
    "verification_status": "approved",
    "rating": 4.85,
    "reviews_count": 47,
    "is_active": true
  },
  "services": [...],
  "upcoming_slots": [...],
  "stats": {
    "total_bookings": 10,
    "completed_bookings": 8,
    "total_earnings_rub": 24000
  }
}
```

### Status Messages

Based on `verification_status`, show appropriate messages:

| Status | Message |
|--------|---------|
| `draft` | "Your profile is incomplete. Please fill in all required information." |
| `pending` | "Your profile is under review. We'll notify you within 24-48 hours." |
| `approved` | "Congratulations! Your profile is verified and visible to clients." |
| `rejected` | "Unfortunately, your application was not approved. Reason: {reason}" |
| `needs_update` | "Please update your profile based on our feedback: {notes}" |

---

## Workflow 3: Managing Availability

### List Existing Slots

Use the public endpoint to show current slots:

```http
GET /api/public/nutritionists/{nutritionist_id}/slots
```

### Add New Slots

```http
POST /api/nutritionists/{nutritionist_id}/slots
Content-Type: application/json

{
  "slots": [
    {"start_at": "2024-01-20T10:00:00Z", "end_at": "2024-01-20T11:00:00Z"}
  ]
}
```

---

## Sample Botpress Conversation Flow

```
Bot: 👋 Welcome! I'll help you set up your nutritionist profile.
     What's your full name?

User: Dr. Elena Petrova

Bot: Great, Dr. Elena Petrova! Now tell me about yourself.
     What's your professional background and expertise?

User: I'm a certified clinical nutritionist with 10 years of 
      experience specializing in weight management and diabetes care.

Bot: Excellent! What are your main areas of specialization?
     [Weight Loss] [Muscle Gain] [Diabetes] [Gut Health] [Sports Nutrition]

User: *selects Weight Loss, Diabetes*

Bot: Do you support any special dietary approaches?
     [Vegetarian] [Vegan] [Gluten Free] [None]

User: *selects Vegetarian*

Bot: Perfect! Now let's add your services.
     What's your first service called?

User: Initial Consultation

Bot: How long is the session (in minutes)?

User: 60

Bot: What's the price in rubles?

User: 3500

Bot: Great! I've created your service:
     📋 Initial Consultation
     ⏱ 60 minutes
     💰 3,500 ₽
     
     Want to add another service? [Yes] [No, continue]

User: No, continue

Bot: Now I need your diploma or certification.
     Please upload a photo or PDF of your credential.

User: *uploads file*

Bot: Got it! Your document has been uploaded for verification.
     
     Ready to submit your profile for review? [Submit] [Edit Profile]

User: Submit

Bot: ✅ Your profile has been submitted!
     Our team will review it within 24-48 hours.
     I'll notify you when your profile is approved.
```

---

## Error Handling

### Common Errors

**400 Bad Request:**
```json
{
  "error": "Validation error",
  "details": [
    {"loc": ["body", "price_rub"], "msg": "must be >= 0"}
  ]
}
```

**404 Not Found:**
```json
{
  "error": "Nutritionist not found"
}
```

### Retry Logic

Implement exponential backoff for transient failures:
```javascript
async function apiCall(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(Math.pow(2, i) * 1000);
    }
  }
}
```

---

## Webhooks (Future)

For real-time updates, you can implement webhooks to notify Botpress of:
- Profile verification status changes
- New bookings
- Payment confirmations
- Booking cancellations

Contact the development team to set up webhook endpoints.

---

## Testing

Use these test Telegram user IDs after running `seed.py`:

| Role | Telegram User ID | Name |
|------|------------------|------|
| Nutritionist 1 | 200000001 | Dr. Elena Petrova |
| Nutritionist 2 | 200000002 | Michael Chen, RD |
| Admin | 100000001 | Admin User |

For authentication testing in debug mode:
```
init_data: test_200000001_Elena
```


