# Architecture Freeze Document

**Date:** 2024-12-29  
**Purpose:** This document freezes the current architecture state of the NutriMatch project. It describes only what exists, not what is planned or suggested.

---

## 1. Backend Entities (Database Tables)

### 1.1 Profile
**Table:** `profiles`  
**Purpose:** Base user entity for all users (clients, nutritionists, admins)

**Fields:**
- `id` (UUID, PK)
- `role` (String, 20) - Values: `client`, `nutritionist`, `admin`
- `telegram_user_id` (BigInteger, unique, indexed)
- `full_name` (String, 255)
- `photo_url` (Text, nullable)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Relationships:**
- One-to-one with `NutritionistProfile` (if role is nutritionist)
- One-to-many with `Booking` (as client)
- One-to-many with `Intake`
- One-to-many with `PolicyAcknowledgement`

### 1.2 NutritionistProfile
**Table:** `nutritionist_profiles`  
**Purpose:** Extended profile information for nutritionists

**Fields:**
- `nutritionist_id` (UUID, PK, FK to profiles.id)
- `bio` (Text, nullable)
- `tags` (Array[Text])
- `specializations` (Array[Text])
- `verification_status` (String, 20) - Values: `draft`, `pending`, `approved`, `rejected`, `needs_update`
- `rating` (Numeric 3,2) - Default: 0.00
- `reviews_count` (Integer) - Default: 0
- `is_active` (Boolean) - Default: false
- `submitted_at` (DateTime, nullable)
- `verified_at` (DateTime, nullable)

**Relationships:**
- One-to-one with `Profile`
- One-to-many with `Service`
- One-to-many with `AvailabilitySlot`
- One-to-many with `NutritionistDocument`
- One-to-many with `Booking` (as nutritionist)

### 1.3 Service
**Table:** `services`  
**Purpose:** Services offered by nutritionists

**Fields:**
- `id` (UUID, PK)
- `nutritionist_id` (UUID, FK to nutritionist_profiles.nutritionist_id, indexed)
- `title` (String, 255)
- `description` (Text, nullable)
- `duration_minutes` (Integer) - Default: 60
- `price_rub` (Integer)
- `is_active` (Boolean) - Default: true
- `created_at` (DateTime)

**Relationships:**
- Many-to-one with `NutritionistProfile`
- One-to-many with `Booking`

### 1.4 AvailabilitySlot
**Table:** `availability_slots`  
**Purpose:** Time slots when nutritionists are available

**Fields:**
- `id` (UUID, PK)
- `nutritionist_id` (UUID, FK to nutritionist_profiles.nutritionist_id, indexed)
- `start_at` (DateTime with timezone, indexed)
- `end_at` (DateTime with timezone)
- `status` (String, 20) - Values: `free`, `held`, `booked`, `cancelled` - Default: `free`
- `source` (String, 20) - Values: `manual`, `calendar` - Default: `manual`
- `hold_expires_at` (DateTime with timezone, nullable)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Relationships:**
- Many-to-one with `NutritionistProfile`
- One-to-one with `Booking` (via slot_id)

### 1.5 Booking
**Table:** `bookings`  
**Purpose:** Consultation booking records

**Fields:**
- `id` (UUID, PK)
- `client_id` (UUID, FK to profiles.id, nullable, indexed)
- `nutritionist_id` (UUID, FK to nutritionist_profiles.nutritionist_id, nullable, indexed)
- `service_id` (UUID, FK to services.id, nullable)
- `slot_id` (UUID, FK to availability_slots.id, nullable, unique)
- `status` (String, 20) - Values: `pending_payment`, `paid`, `cancelled`, `completed`, `no_show`, `refunded` - Default: `pending_payment`
- `price_rub` (Integer)
- `currency` (String, 3) - Default: `RUB`
- `meeting_link` (Text, nullable)
- `created_at` (DateTime)
- `paid_at` (DateTime, nullable)
- `cancelled_at` (DateTime, nullable)

**Relationships:**
- Many-to-one with `Profile` (as client)
- Many-to-one with `NutritionistProfile`
- Many-to-one with `Service`
- One-to-one with `AvailabilitySlot`
- One-to-one with `Payment`

### 1.6 Payment
**Table:** `payments`  
**Purpose:** Payment records linked to bookings

**Fields:**
- `id` (UUID, PK)
- `booking_id` (UUID, FK to bookings.id, unique, indexed)
- `provider` (String, 50) - Values: `mock`, `telegram`, `yookassa`, `cloudpayments`
- `provider_payment_id` (Text, nullable)
- `amount_rub` (Integer)
- `currency` (String, 3) - Default: `RUB`
- `status` (String, 20) - Values: `created`, `succeeded`, `failed`, `refunded` - Default: `created`
- `raw_payload` (JSONB, nullable) - Webhook payload for debugging
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Relationships:**
- One-to-one with `Booking`

### 1.7 Intake
**Table:** `intakes`  
**Purpose:** Client intake questionnaire responses

**Fields:**
- `id` (UUID, PK)
- `client_id` (UUID, FK to profiles.id, indexed)
- `answers` (JSONB) - Structure:
  - `goals` (Array[String])
  - `dietary_restrictions` (Array[String])
  - `budget_min` (Integer)
  - `budget_max` (Integer)
  - `preferred_schedule` (String)
  - `health_conditions` (Array[String])
  - `additional_notes` (String)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Relationships:**
- Many-to-one with `Profile` (as client)
- One-to-one with `ClientFilterState` (via intake_id)

### 1.8 ClientFilterState
**Table:** `client_filter_states`  
**Purpose:** Persists client's current search filters

**Fields:**
- `client_id` (UUID, PK, FK to profiles.id)
- `intake_id` (UUID, FK to intakes.id, nullable, indexed)
- `filters` (JSONB) - Structure:
  - `goals` (Array[String])
  - `topics` (Array[String])
  - `budget_max_rub` (Integer)
  - `dietary` (Array[String])
  - `help_mode` (String) - Values: `one_time`, `plan`, `long_term`, or null
  - `specializations` (Array[String])
  - `tags` (Array[String])
- `updated_at` (DateTime with timezone)

**Relationships:**
- One-to-one with `Profile` (as client)
- One-to-one with `Intake`

### 1.9 NutritionistDocument
**Table:** `nutritionist_documents`  
**Purpose:** Document metadata for nutritionist verification

**Fields:**
- `id` (UUID, PK)
- `nutritionist_id` (UUID, FK to nutritionist_profiles.nutritionist_id, indexed)
- `type` (String, 50) - Values: `diploma`, `certificate`, `other`
- `file_path` (Text)
- `status` (String, 20) - Values: `uploaded`, `accepted`, `rejected` - Default: `uploaded`
- `review_note` (Text, nullable)
- `uploaded_at` (DateTime)

**Relationships:**
- Many-to-one with `NutritionistProfile`

### 1.10 PolicyAcknowledgement
**Table:** `policies_acknowledgements`  
**Purpose:** Tracks user acknowledgements of policies and terms

**Fields:**
- `id` (UUID, PK)
- `user_id` (UUID, FK to profiles.id, indexed)
- `policy_code` (String, 100)
- `policy_version` (String, 50)
- `accepted_at` (DateTime with timezone)

**Constraints:**
- Unique constraint on (`user_id`, `policy_code`, `policy_version`)

**Relationships:**
- Many-to-one with `Profile`

---

## 2. Backend Endpoints

### 2.1 Authentication Routes (`/api/auth`)

**POST `/api/auth/telegram/verify`**
- Authenticates user via Telegram Mini App initData
- Returns JWT token and profile data
- Creates profile if doesn't exist

**POST `/api/auth/dev-login`** (Development only)
- Bypasses Telegram authentication for testing
- Returns JWT token for seeded test user
- Disabled in production

### 2.2 Public Routes (`/api/public`)

**GET `/api/public/nutritionists`**
- Lists approved and active nutritionists
- Query params: `specialization`, `budget`, `tags[]`
- Returns list with total count

**GET `/api/public/nutritionists/<nutritionist_id>`**
- Gets single nutritionist details
- Only returns approved and active nutritionists

**GET `/api/public/nutritionists/<nutritionist_id>/services`**
- Lists active services for a nutritionist

**GET `/api/public/nutritionists/<nutritionist_id>/slots`**
- Lists free availability slots for a nutritionist
- Query param: `service_id` (optional)
- Only returns future free slots

**POST `/api/public/nutritionists/search`**
- Advanced search with filters and scoring
- Body: `{ filters: {...} }`
- Returns results sorted by relevance score

**GET `/api/public/filters/options`**
- Returns all available filter options for UI

### 2.3 Client Routes (`/api/clients`)

**POST `/api/clients/intakes`** (Auth required)
- Submits client intake form
- Creates/updates `ClientFilterState` with normalized filters
- Returns intake data and normalized filters

**GET `/api/clients/intakes`** (Auth required)
- Lists all intakes for current client

**GET `/api/clients/matches?intake_id=<id>`** (Auth required)
- Gets matching nutritionists for a specific intake
- Verifies intake belongs to current user

**GET `/api/clients/bookings`** (Auth required)
- Lists all bookings for current client

**GET `/api/clients/me/bookings`** (Auth required)
- Lists bookings with full relations (service, slot, nutritionist)

**GET `/api/clients/me/filters`** (Auth required)
- Gets current filter state and defaults from latest intake

**PUT `/api/clients/me/filters`** (Auth required)
- Updates client filter state
- Body: `{ filters: {...} }`

### 2.4 Nutritionist Routes (`/api/nutritionists`)

**POST `/api/nutritionists/upsert`**
- Creates or updates nutritionist profile
- Used by Botpress for onboarding
- Body: `NutritionistUpsertRequest`
- Can submit for verification

**POST `/api/nutritionists/<nutritionist_id>/documents`** (Auth optional)
- Adds document metadata for verification
- Body: `DocumentUploadRequest`

**POST `/api/nutritionists/<nutritionist_id>/services`** (Auth optional)
- Creates a new service
- Body: `ServiceCreateRequest`

**POST `/api/nutritionists/<nutritionist_id>/slots`** (Auth optional)
- Bulk creates availability slots
- Body: `BulkSlotCreateRequest`

**GET `/api/nutritionists/<nutritionist_id>/dashboard`** (Auth optional)
- Returns dashboard data: profile, services, upcoming slots, stats

### 2.5 Booking Routes (`/api/bookings`)

**POST `/api/bookings`** (Auth required)
- Creates booking and holds slot for 10 minutes
- Body: `BookingCreateRequest`
- Atomic operation with row-level locking
- Creates payment intent

**GET `/api/bookings/<booking_id>`** (Auth required)
- Gets booking details
- Verifies ownership (client or nutritionist)

**POST `/api/bookings/<booking_id>/mark-paid`** (Auth required, Dev only)
- Simulates successful payment
- Atomic operation: booking → paid, slot → booked
- Disabled in production

**POST `/api/bookings/<booking_id>/cancel`** (Auth required)
- Cancels booking and releases slot
- Only for `pending_payment` status
- Body: `{ reason?: string }`

**POST `/api/bookings/release-expired-holds`**
- Cron endpoint to release expired slot holds
- Idempotent and safe for parallel execution

### 2.6 Payment Routes (`/api/payments`)

**POST `/api/payments/create`** (Auth required)
- Creates payment intent for a booking
- Body: `{ booking_id: string }`
- Returns payment URL/intent data

**POST `/api/payments/webhook/<provider>`**
- Handles payment provider webhooks
- Providers: `telegram`, `yookassa`, `mock`
- Updates payment status and booking

**POST `/api/payments/webhook`** (Deprecated)
- Legacy webhook endpoint
- Determines provider from payload

**POST `/api/payments/mock-pay/<booking_id>`** (Dev only)
- Simulates payment via mock webhook
- Only available in dev mode or when PAYMENT_PROVIDER=mock

**GET `/api/payments/<booking_id>/status`** (Auth required)
- Gets payment status for a booking
- Verifies ownership

### 2.7 Bot API Routes (`/api/bot`)

**Authentication:** Requires `X-Service-Token` header

**GET `/api/bot/resolve-telegram-user?telegram_user_id=<id>`**
- Resolves user profile and role by telegram_user_id
- Returns profile, nutritionist data, and role

**GET `/api/bot/nutritionists/<nutritionist_id>/services`**
- Lists nutritionist's services

**PUT `/api/bot/nutritionists/<nutritionist_id>/services/<service_id>`**
- Updates a service

**DELETE `/api/bot/nutritionists/<nutritionist_id>/services/<service_id>`**
- Deletes a service

**GET `/api/bot/nutritionists/<nutritionist_id>/calendar/status`**
- Gets calendar connection status
- Returns: `{ connected: boolean, email: string | null }`

**GET `/api/bot/nutritionists/<nutritionist_id>/calendar/oauth-url`**
- Gets Google OAuth URL for calendar connection
- Currently returns placeholder (not implemented)

**GET `/api/bot/nutritionists/<nutritionist_id>/reviews`**
- Gets nutritionist reviews
- Currently returns empty list (reviews not implemented)

**GET `/api/bot/nutritionists/<nutritionist_id>/statistics?days=30`**
- Gets nutritionist statistics
- Returns: income, consultations, avg_rating, total_clients

**POST `/api/bot/nutritionists/<nutritionist_id>/upload-photo`**
- Uploads photo for nutritionist profile
- Currently returns placeholder URL (file storage not implemented)

**POST `/api/bot/support/messages`**
- Creates support message
- Currently just logs the message (support system not implemented)

**POST `/api/bot/nutritionists/<nutritionist_id>/slots`**
- Creates availability slot (manual)
- Validates overlap and future time
- Body: `{ start_at: datetime, end_at: datetime }`

**GET `/api/bot/nutritionists/<nutritionist_id>/slots`**
- Lists slots in date range
- Query params: `from`, `to` (default: now to +14 days)
- Returns slots with status: free, held, booked

**DELETE `/api/bot/nutritionists/<nutritionist_id>/slots/<slot_id>`**
- Deletes a slot
- Only for slots with status `free`

**GET `/api/bot/nutritionists/<nutritionist_id>/bookings`**
- Gets nutritionist's bookings
- Query params: `limit`, `offset`
- Returns upcoming paid/completed bookings with client and service info

### 2.8 Admin Routes (`/api/admin`)

**POST `/api/admin/auth/login`**
- Admin login with email/password
- Returns JWT token with admin role
- Credentials from environment variables

**GET `/api/admin/auth/me`** (Auth required)
- Gets current admin user info

**POST `/api/admin/auth/logout`** (Auth required)
- Admin logout (token invalidation placeholder)

**GET `/api/admin/nutritionists`** (Auth required, Admin only)
- Lists nutritionists for moderation
- Query param: `status` (default: `pending`)

**GET `/api/admin/nutritionists/<nutritionist_id>`** (Auth required, Admin only)
- Gets nutritionist details with documents

**POST `/api/admin/nutritionists/<nutritionist_id>/approve`** (Auth required, Admin only)
- Approves nutritionist
- Sets status to `approved`, `is_active` to true
- Sends notification

**POST `/api/admin/nutritionists/<nutritionist_id>/reject`** (Auth required, Admin only)
- Rejects nutritionist
- Body: `{ reason: string }`
- Sets status to `rejected`, `is_active` to false
- Sends notification

**POST `/api/admin/nutritionists/<nutritionist_id>/request-update`** (Auth required, Admin only)
- Requests updates from nutritionist
- Body: `{ notes: string }`
- Sets status to `needs_update`

**POST `/api/admin/nutritionists/<nutritionist_id>/disable`** (Auth required, Admin only)
- Disables an approved nutritionist
- Sets `is_active` to false

**GET `/api/admin/documents/<document_id>/url`** (Auth required, Admin only)
- Gets signed URL for downloading document
- Currently returns file_path directly (signed URLs not implemented)

**POST `/api/admin/documents/<document_id>/review`** (Auth required, Admin only)
- Reviews a document
- Body: `{ status: "accepted" | "rejected", note?: string }`
- Sends notification

**GET `/api/admin/bookings`** (Auth required, Admin only)
- Lists all bookings with filters
- Query params: `status`, `date_from`, `date_to`, `page`, `limit`
- Returns paginated results with expanded relations

**GET `/api/admin/bookings/<booking_id>`** (Auth required, Admin only)
- Gets detailed booking information

**POST `/api/admin/bookings/<booking_id>/cancel`** (Auth required, Admin only)
- Admin cancels a booking
- Body: `{ reason?: string }`
- Releases slot and sends notifications

**POST `/api/admin/bookings/<booking_id>/complete`** (Auth required, Admin only)
- Marks booking as completed
- Body: `{ notes?: string }`
- Only for `paid` bookings

**GET `/api/admin/stats`** (Auth required, Admin only)
- Gets dashboard statistics
- Returns: total_users, total_nutritionists, pending_verifications, total_bookings, revenue_this_month

---

## 3. Telegram Bot Flows

### 3.1 Start Flow
**Handler:** `handlers/start.py`

1. User sends `/start`
2. Bot resolves user via `/api/bot/resolve-telegram-user`
3. Shows welcome message based on role
4. Displays main menu keyboard

### 3.2 Menu Navigation
**Handler:** `handlers/menu.py`

**Main Menu Options:**
- "Для нутрициологов" → Nutritionist menu
- "Я нутрициолог" → Creates draft nutritionist profile
- "Личный кабинет" → Personal cabinet (nutritionists only)

**Nutritionist Menu:**
- Shows verification status if profile exists
- Options: Create/Update Profile, Services, Schedule, Personal Cabinet

### 3.3 Profile Creation/Update Flow
**Handler:** `handlers/profile.py`  
**FSM States:** `ProfileStates`

**Steps:**
1. Full name input (or skip to keep existing)
2. Photo upload (optional, skip allowed)
3. Bio text (optional, skip allowed, max 300 chars)
4. Specializations selection (multi-select, at least one required)
5. Tags selection (optional, multi-select)
6. Rules confirmation (must accept)
7. Final confirmation and submission

**Specializations (static list):**
- weight_management, sports_nutrition, gut_health, diabetes, hormonal_health, pediatric, pregnancy, eating_disorders, autoimmune, plant_based

**Tags (static list):**
- vegetarian, vegan, keto, intermittent_fasting, anti_aging, detox, allergy, online_only

**Submission:**
- Calls `/api/nutritionists/upsert` with `submit_for_verification=true`
- Sets status to `pending`

### 3.4 Services Management Flow
**Handler:** `handlers/services.py`  
**FSM States:** `ServiceStates`

**List Services:**
- Shows all services for nutritionist
- Click service to view details and edit

**Create Service:**
1. Title input (3-100 chars)
2. Description input (optional, max 500 chars, skip allowed)
3. Duration input (15-240 minutes)
4. Price input (100-100,000 RUB)
5. Confirmation
6. Creates via `/api/bot/nutritionists/<id>/services`

**Edit Service:**
- View service details
- Toggle active/inactive status
- Delete service (with confirmation)

### 3.5 Schedule Management Flow
**Handler:** `handlers/schedule.py`  
**FSM States:** `SlotStates`

**View Schedule:**
- Shows slots grouped by date (next 14 days)
- Displays status: free, held, booked
- Shows calendar connection status if connected

**Add Slot:**
1. Select date (next 14 days)
2. Enter start time (HH:MM format)
3. Select duration (30, 60, 90, 120 minutes)
4. Confirm creation
5. Creates via `/api/bot/nutritionists/<id>/slots`
- Validates: future time, no overlaps

**Delete Slot:**
- Shows list of free slots
- Select slot to delete
- Confirms deletion
- Only free slots can be deleted

**View Bookings:**
- Shows upcoming paid/completed bookings
- Displays: date, time, client name, service title, status
- Pagination support

### 3.6 Personal Cabinet Flow
**Handler:** `handlers/cabinet.py`

**Sections:**
1. **Calendar** - Shows connection status, OAuth URL (placeholder)
2. **Reviews** - Lists reviews (currently empty, not implemented)
3. **Statistics** - Shows 30-day stats: income, consultations, rating, clients
4. **Settings** - Shows cancellation policy (read-only)
5. **Support** - Send support message (FSM: `SupportStates.waiting_message`)

---

## 4. Admin Panel Features

**Tech Stack:** React + TypeScript + Vite + Tailwind CSS

### 4.1 Pages

**LoginPage** (`/login`)
- Email/password login
- Calls `/api/admin/auth/login`
- Stores JWT token

**DashboardPage** (`/`)
- Overview statistics
- Calls `/api/admin/stats`
- Shows: total users, nutritionists, pending verifications, bookings, revenue

**NutritionistsPage** (`/nutritionists`)
- Lists nutritionists by verification status
- Filter by status: draft, pending, approved, rejected, needs_update
- Calls `/api/admin/nutritionists?status=<status>`

**NutritionistDetailPage** (`/nutritionists/:id`)
- View nutritionist profile details
- View documents list
- Actions: Approve, Reject, Request Update, Disable
- Calls `/api/admin/nutritionists/<id>`

**UsersPage** (`/users`)
- Lists all users (clients)
- Filter and search capabilities
- (Implementation details not fully visible in routes)

**BookingsPage** (`/bookings`)
- Lists all bookings with filters
- Filter by: status, date range
- Pagination support
- Calls `/api/admin/bookings`
- Actions: View details, Cancel, Complete

**PaymentsPage** (`/payments`)
- Lists payment records
- Filter by status, provider, date
- (Implementation details not fully visible in routes)

**ReviewsPage** (`/reviews`)
- Lists reviews
- (Implementation details not fully visible in routes)

**SupportPage** (`/support`)
- Support ticket management
- (Implementation details not fully visible in routes)

**SettingsPage** (`/settings`)
- Platform settings
- (Implementation details not fully visible in routes)

### 4.2 Authentication
- JWT-based authentication
- Protected routes require admin role
- Token stored in localStorage
- Auto-redirect to login if not authenticated

---

## 5. Client Flows (Telegram Mini App)

**Tech Stack:** React + TypeScript + Vite + Tailwind CSS

### 5.1 Pages

**IntakePage** (`/intake`)
- Client intake questionnaire
- Fields: goals, dietary restrictions, budget, schedule, health conditions, notes
- Submits via `/api/clients/intakes`
- Creates/updates `ClientFilterState`

**ResultsPage** (`/results`)
- Shows matching nutritionists based on filters
- Uses `/api/public/nutritionists/search` with filters
- Displays nutritionist cards with scoring
- Filter drawer for adjusting search criteria
- Click nutritionist → NutritionistPage

**NutritionistPage** (`/nutritionist/:id`)
- View nutritionist profile
- View services list
- View available slots
- Select service and slot → BookingPage

**BookingPage** (`/book/:nutritionistId/:serviceId`)
- Shows selected service details
- Slot picker component
- Creates booking via `/api/bookings`
- Redirects to payment flow
- Payment intent creation via `/api/payments/create`

**PaymentSuccessPage** (`/payment-success`)
- Confirmation page after successful payment
- Shows booking details

**MyBookingsPage** (`/my-bookings`)
- Lists client's bookings
- Calls `/api/clients/me/bookings`
- Shows: date, time, nutritionist, service, status

### 5.2 Authentication
- Telegram Mini App authentication
- Uses `window.Telegram.WebApp.initData`
- Calls `/api/auth/telegram/verify`
- Dev mode: `/api/auth/dev-login` button (test user)
- JWT token stored in auth store

### 5.3 Components

**FilterDrawer**
- Adjustable search filters
- Syncs with `/api/clients/me/filters`
- Updates `ClientFilterState`

**SlotPicker**
- Displays available slots for a nutritionist
- Groups by date
- Shows slot status

**NutritionistCard**
- Displays nutritionist info
- Shows rating, specializations, price range
- Click to view details

**ServiceCard**
- Displays service details
- Price, duration, description

---

## 6. What Does NOT Exist Yet

### 6.1 Database Models
- **Review model** - Reviews/ratings system not implemented
- **SupportTicket model** - Support ticket system not implemented
- **Notification model** - Notification storage not implemented (notifications sent but not persisted)
- **CalendarIntegration model** - Google Calendar integration not implemented

### 6.2 Backend Features
- **Reviews system** - No review creation, storage, or retrieval
- **Support ticket system** - Messages logged but no ticket management
- **File storage** - Photo/document uploads return placeholder URLs
- **Google Calendar integration** - OAuth and sync not implemented
- **Email notifications** - NotificationService methods exist but email sending not implemented
- **SMS notifications** - Not implemented
- **Refund processing** - Refund status exists but no refund logic
- **Meeting link generation** - Field exists but no automatic generation
- **Rating calculation** - Rating field exists but no calculation logic

### 6.3 Payment Providers
- **Telegram Payments** - Provider exists but integration not complete
- **YooKassa** - Provider exists but integration not complete
- **CloudPayments** - Provider exists but integration not complete
- Only **Mock** provider is fully functional

### 6.4 Telegram Bot Features
- **Document upload** - Not implemented (only metadata)
- **Calendar OAuth flow** - Placeholder only
- **Review viewing** - Returns empty list
- **Photo upload** - Returns placeholder URL

### 6.5 Admin Panel Features
- **Document viewing** - No signed URL generation (returns file_path directly)
- **User management** - UsersPage exists but full CRUD not visible
- **Payment management** - PaymentsPage exists but full features not visible
- **Review moderation** - ReviewsPage exists but moderation not visible
- **Support ticket management** - SupportPage exists but ticket system not implemented

### 6.6 Client Features
- **Review submission** - No UI or API for submitting reviews
- **Booking cancellation** - No UI for clients to cancel bookings
- **Meeting link access** - No UI to view/access meeting links
- **Nutritionist messaging** - No direct messaging feature

### 6.7 Infrastructure
- **Cron jobs** - `/api/bookings/release-expired-holds` exists but no scheduled execution configured
- **Background jobs** - No job queue system
- **Caching** - No caching layer
- **CDN** - No CDN for static assets
- **Monitoring** - No monitoring/observability tools configured
- **Logging aggregation** - Basic logging only

---

## 7. Key Services and Abstractions

### 7.1 MatchingService
- `search_nutritionists()` - Basic search with filters
- `search_with_filters()` - Advanced search with scoring
- `find_matches()` - Matches nutritionists to intake

### 7.2 BookingHoldService
- `create_booking_with_hold()` - Atomic booking creation with slot hold
- `cancel_booking()` - Atomic booking cancellation
- `release_expired_holds()` - Releases expired slot holds

### 7.3 PaymentService
- `create_payment_for_booking()` - Creates payment intent
- `process_provider_webhook()` - Handles provider webhooks
- `simulate_payment_success()` - Dev-only payment simulation
- `get_payment_status()` - Gets payment status

### 7.4 NotificationService
- `nutritionist_approved()` - Sends approval notification
- `nutritionist_rejected()` - Sends rejection notification
- `document_reviewed()` - Sends document review notification
- `booking_cancelled()` - Sends cancellation notification
- (Methods exist but actual sending not implemented)

### 7.5 TelegramAuthService
- `verify_init_data()` - Verifies Telegram initData signature
- `get_or_create_profile()` - Gets or creates user profile

### 7.6 Filters Service
- `validate_filters()` - Validates filter structure
- `normalize_filters_from_intake()` - Converts intake answers to filters
- `get_empty_filters()` - Returns empty filter structure
- `FILTER_OPTIONS` - Static filter options for UI

---

## 8. Database Migrations

**Migration History:**
1. `20241225_000001_initial_migration.py` - Initial schema
2. `20241227_000001_add_status_indexes_and_constraints.py` - Status indexes
3. `20241227_000002_add_client_filter_state.py` - ClientFilterState table
4. `20241228_000001_add_currency_to_payments.py` - Currency field
5. `20241229_000001_add_slot_source_and_updated_at.py` - Slot source and updated_at

---

## 9. Technology Stack

### Backend
- **Framework:** Flask
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL
- **Migrations:** Alembic
- **Auth:** Flask-JWT-Extended
- **Validation:** Pydantic
- **API Docs:** Swagger/OpenAPI

### Telegram Bot
- **Framework:** aiogram 3.x
- **FSM Storage:** PostgreSQL (custom PostgresFSMStorage)
- **Language:** Python

### Admin Panel
- **Framework:** React 18
- **Language:** TypeScript
- **Build:** Vite
- **Styling:** Tailwind CSS
- **Routing:** React Router

### Client App
- **Framework:** React 18
- **Language:** TypeScript
- **Build:** Vite
- **Styling:** Tailwind CSS
- **Routing:** React Router
- **Platform:** Telegram Mini App

---

## 10. Environment Configuration

### Backend
- `FLASK_ENV` - Environment mode
- `DATABASE_URL` - PostgreSQL connection string
- `TELEGRAM_BOT_TOKEN` - Bot token for auth verification
- `JWT_SECRET_KEY` - JWT signing key
- `PAYMENT_PROVIDER` - Payment provider (mock/telegram/yookassa/cloudpayments)
- `ADMIN_EMAIL` - Admin login email
- `ADMIN_PASSWORD` - Admin login password
- `BOT_SERVICE_TOKEN` - Token for bot API authentication

### Telegram Bot
- `BOT_TOKEN` - Telegram bot token
- `DATABASE_URL` - PostgreSQL connection string
- `API_BASE_URL` - Backend API URL
- `BOT_SERVICE_TOKEN` - Service token for API calls
- `MODE` - `polling` or `webhook`
- `WEBHOOK_URL` - Webhook URL (production)
- `WEBHOOK_PATH` - Webhook path
- `WEBHOOK_HOST` - Webhook server host
- `WEBHOOK_PORT` - Webhook server port
- `LOG_LEVEL` - Logging level

---

**END OF ARCHITECTURE FREEZE DOCUMENT**
