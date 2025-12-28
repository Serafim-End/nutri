# NutriMatch - Telegram Nutritionists Marketplace

A production-ready MVP for a Telegram-based nutritionists marketplace. Clients can find and book consultations with verified nutritionists through a Telegram Mini App.

## 🏗️ Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   Telegram Mini App │────▶│    Flask Backend    │────▶│    PostgreSQL       │
│   (React + Vite)    │     │    (REST API)       │     │    (Supabase)       │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
                                      ▲
                                      │
                            ┌─────────────────────┐
                            │      Botpress       │
                            │  (Nutritionist UI)  │
                            └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local client development)
- Python 3.11+ (for local backend development)

### Run with Docker Compose

```bash
# 1. Clone and navigate to the project
cd nutri

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env and set DATABASE_URL to your Supabase connection string
# DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres

# 4. Start all services
docker compose up --build

# 5. In a new terminal, run migrations
make migrate

# 6. Seed the database with test data
make seed
```

**Access:**
- Client: http://localhost:5173
- API: http://localhost:5000
- Health check: http://localhost:5000/health
- Database health: http://localhost:5000/health/db

---

## 🗄️ Database Configuration (Supabase)

This project uses **Supabase PostgreSQL** as the primary database.

### Setting DATABASE_URL

The `DATABASE_URL` environment variable must be set to your Supabase connection string:

```bash
# Format
DATABASE_URL=postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres

# Example (with sslmode - automatically added if missing)
DATABASE_URL=postgresql://postgres:nutri-stage1@db.ghahrdtwdzmwthxyzmpt.supabase.co:5432/postgres?sslmode=require
```

### Connection Configuration

The backend automatically:
1. **Normalizes the URL** to use `postgresql+psycopg2://` driver
2. **Adds SSL** (`sslmode=require`) for Supabase connections
3. **Validates** the URL format on startup
4. **Fails fast** with a clear error if `DATABASE_URL` is missing or invalid

### Local Development with Supabase

```bash
# Set environment variable
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres"

# Verify connection
cd backend
python -c "from app import create_app; app = create_app(); print('Connected!')"
```

### Common Supabase Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `SSL required` | Missing sslmode | Add `?sslmode=require` to URL (auto-added) |
| `Connection refused` | Wrong host/port | Verify Supabase project URL |
| `Connection timed out` | Network/firewall | Check if port 5432 is accessible |
| `Password authentication failed` | Wrong password | Get password from Supabase dashboard |
| `Database does not exist` | Wrong database name | Use `postgres` (default Supabase DB) |

### Checking Database Health

```bash
# Using curl
curl http://localhost:5000/health/db

# Using make
make db-check
```

Response example:
```json
{
  "status": "healthy",
  "database": "postgresql+psycopg2://postgres:***@db.xxx.supabase.co:5432/postgres",
  "provider": "supabase",
  "connection": true,
  "revision": "20241227_000001"
}
```

---

## 📦 Database Migrations

Migrations are managed with **Alembic** via Flask-Migrate.

### Running Migrations

```bash
# With Docker (recommended)
make migrate            # Run all pending migrations
make downgrade          # Rollback last migration
make db-version         # Show current revision
make db-history         # Show migration history

# Local development
make migrate-local
make downgrade-local
```

### Creating New Migrations

```bash
# Auto-generate migration from model changes
make migrate-new msg="add user preferences"

# Manual migration
docker compose exec backend flask db revision -m "custom migration"
```

### Migration Files

Located in `backend/migrations/versions/`:

| Migration | Description |
|-----------|-------------|
| `20241225_000001_initial_migration.py` | Base schema with all tables |
| `20241227_000001_add_status_indexes_and_constraints.py` | Performance indexes and CHECK constraints |
| `20241227_000002_add_client_filter_state.py` | Client filter state for persistent search filters |

### Resetting Database (DANGER!)

```bash
# This will DELETE all data!
make db-reset
```

---

## 🌱 Seeding Test Data

The seed script is **idempotent** - safe to run multiple times.

```bash
# With Docker
make seed

# Local
make seed-local
```

### Seeded Accounts

| Role | Telegram User ID | Name |
|------|-----------------|------|
| Admin | 100000001 | Admin User |
| Client | 300000001 | Test Client |
| Nutritionist | 200000001 | Dr. Elena Petrova |
| Nutritionist | 200000002 | Michael Chen, RD |

For development auth, use initData like: `test_200000001_Elena`

---

## 🏃 Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres"
export FLASK_DEBUG=1

# Run migrations
flask db upgrade

# Seed database
python seed.py

# Start server
flask run --debug
```

**Client:**
```bash
cd client
npm install
npm run dev
```

---

## 📁 Project Structure

```
nutri/
├── backend/                    # Flask API
│   ├── app/
│   │   ├── __init__.py        # App factory with health endpoints
│   │   ├── config.py          # Configuration with Supabase SSL handling
│   │   ├── extensions.py      # Flask extensions
│   │   ├── models/            # SQLAlchemy models
│   │   ├── routes/            # API blueprints
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── migrations/            # Alembic migrations
│   │   ├── alembic.ini        # Alembic config (reads DATABASE_URL)
│   │   ├── env.py             # Migration environment
│   │   └── versions/          # Migration files
│   ├── tests/                 # Pytest tests
│   ├── Dockerfile
│   ├── requirements.txt
│   └── seed.py                # Idempotent test data seeder
├── client/                     # React Mini App
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── lib/               # API client
│   │   ├── pages/             # Page components
│   │   ├── store/             # Zustand stores
│   │   └── types/             # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── Makefile                    # Developer commands
├── .env.example
└── README.md
```

---

## 🔌 API Endpoints

### Health Checks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/db` | Database connectivity + migration revision |

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/telegram/verify` | Verify Telegram initData, return JWT |

### Clients
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/clients/intakes` | Submit intake questionnaire (creates filter state) |
| GET | `/api/clients/matches?intake_id=...` | Get matched nutritionists |
| GET | `/api/clients/bookings` | List client's bookings |
| GET | `/api/clients/me/filters` | Get current filters and defaults |
| PUT | `/api/clients/me/filters` | Update current filters |

### Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/public/nutritionists` | List approved nutritionists |
| GET | `/api/public/nutritionists/{id}` | Get nutritionist details |
| GET | `/api/public/nutritionists/{id}/services` | List services |
| GET | `/api/public/nutritionists/{id}/slots` | List available slots |
| POST | `/api/public/nutritionists/search` | Search with filters and scoring |
| GET | `/api/public/filters/options` | Get available filter options |

### Bookings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bookings` | Create booking (holds slot 10 min) |
| GET | `/api/bookings/{id}` | Get booking details |
| POST | `/api/bookings/{id}/cancel` | Cancel booking |
| POST | `/api/bookings/{id}/mark-paid` | DEV: simulate payment (routes through abstraction) |
| POST | `/api/bookings/release-expired-holds` | Cron: release expired holds |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/create` | Create payment intent for booking |
| POST | `/api/payments/webhook/{provider}` | Provider-specific webhook handler |
| POST | `/api/payments/mock-pay/{booking_id}` | Dev: simulate payment success |
| GET | `/api/payments/{booking_id}/status` | Get payment status |

### Nutritionists (Botpress)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/nutritionists/upsert` | Create/update profile |
| POST | `/api/nutritionists/{id}/documents` | Add document metadata |
| POST | `/api/nutritionists/{id}/services` | Create service |
| POST | `/api/nutritionists/{id}/slots` | Bulk create slots |
| GET | `/api/nutritionists/{id}/dashboard` | Get dashboard data |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/nutritionists?status=pending` | List pending reviews |
| POST | `/api/admin/nutritionists/{id}/approve` | Approve nutritionist |
| POST | `/api/admin/nutritionists/{id}/reject` | Reject nutritionist |

---

## 🔐 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (Supabase) | **Required** |
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `JWT_SECRET_KEY` | JWT signing key | Same as SECRET_KEY |
| `JWT_EXPIRY_HOURS` | Token expiration | `24` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | `` |
| `CORS_ORIGINS` | Allowed origins | `http://localhost:5173` |
| `SLOT_HOLD_MINUTES` | Slot hold duration | `10` |
| `PAYMENT_PROVIDER` | Payment provider (mock, telegram, yookassa) | `mock` |
| `PAYMENT_WEBHOOK_SECRET` | Webhook signature key | `webhook-secret` |

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest -v

# With coverage
pytest --cov=app --cov-report=html
```

---

## 🔧 Development Commands

```bash
# View all commands
make help

# Database commands
make migrate        # Run migrations
make downgrade      # Rollback
make seed           # Seed test data
make db-check       # Check connection

# Docker commands
make up             # Start containers
make down           # Stop containers
make logs           # View logs

# Code quality
make lint           # Run linters
make format         # Format code
```

---

## 🚢 Production Deployment

1. Set up Supabase PostgreSQL
2. Configure environment variables (especially `DATABASE_URL`)
3. Build and deploy:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

4. Run migrations:
```bash
docker compose exec backend flask db upgrade
```

5. Set up cron job for expired holds:
```bash
# Every 5 minutes
*/5 * * * * curl -X POST http://localhost:5000/api/bookings/release-expired-holds
```

---

## 📝 Test Accounts

After running `make seed`:

| Role | Telegram User ID |
|------|-----------------|
| Admin | 100000001 |
| Client | 300000001 |
| Nutritionist (Elena) | 200000001 |
| Nutritionist (Michael) | 200000002 |

For development auth, use initData: `test_200000001_Elena`

---

## 🛡️ Security Notes

- JWT tokens expire after 24 hours
- All nutritionist endpoints verify ownership or admin role
- Telegram initData signature is verified
- Payment webhooks require valid signatures
- CORS is configured for allowed origins only
- SSL is enforced for Supabase connections

---

## 🎯 Stage 6: Atomic Booking & Slot Hold

Stage 6 implements the complete booking flow with race-condition safe slot holds.

### Key Features

- **Atomic Booking**: Uses PostgreSQL row-level locks (`SELECT FOR UPDATE`) to prevent double-booking
- **Slot Hold System**: 10-minute hold window for payment (configurable via `BOOKING_HOLD_MINUTES`)
- **State Machines**: Enforced valid transitions for slots and bookings
- **Dev Login**: Development-only endpoint for testing without Telegram

### Slot States & Transitions

```
free → held → booked → cancelled (admin only)
     ↓
    free (hold expired or cancelled)
```

### Booking States & Transitions

```
pending_payment → paid → completed
       ↓           ↓
   cancelled    refunded
```

### Running the Stage 6 Flow Locally

```bash
# 1. Start services
docker compose up --build

# 2. Run migrations
make migrate

# 3. Seed database with test data
make seed

# 4. Open client in browser
open http://localhost:5173

# 5. Use the "Dev Login" button (bottom-right) to authenticate
#    This calls POST /api/auth/dev-login with the seeded client user
```

### Testing the Booking Flow

1. **Browse nutritionists**: Go to `/results` to see available nutritionists
2. **Select a service**: Click on a nutritionist, then select a service
3. **Choose a slot**: Pick an available time slot
4. **Create booking**: Click "Confirm Booking" to hold the slot
5. **View hold timer**: See countdown timer (10 min default)
6. **Simulate payment**: Click "Simulate Payment Success" to confirm
7. **View bookings**: Go to `/my-bookings` to see all bookings

### API Examples (curl)

```bash
# Dev login (development only)
curl -X POST http://localhost:5000/api/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{"telegram_user_id": 300000001}'

# List nutritionists
curl http://localhost:5000/api/public/nutritionists

# Get nutritionist services
curl http://localhost:5000/api/public/nutritionists/{nutritionist_id}/services

# Get available slots
curl "http://localhost:5000/api/public/nutritionists/{nutritionist_id}/slots?service_id={service_id}"

# Create booking (requires JWT)
curl -X POST http://localhost:5000/api/bookings \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"service_id": "<uuid>", "slot_id": "<uuid>"}'

# Mark booking as paid (simulate payment)
curl -X POST http://localhost:5000/api/bookings/{booking_id}/mark-paid \
  -H "Authorization: Bearer <token>"

# Cancel booking
curl -X POST http://localhost:5000/api/bookings/{booking_id}/cancel \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Changed my mind"}'

# Get my bookings
curl http://localhost:5000/api/clients/me/bookings \
  -H "Authorization: Bearer <token>"

# Release expired holds (cron job)
curl -X POST http://localhost:5000/api/bookings/release-expired-holds
```

### Running Release Expired Holds (Cron)

The expired holds release endpoint should be called periodically:

```bash
# Manual call
curl -X POST http://localhost:5000/api/bookings/release-expired-holds

# Cron job (every 5 minutes)
*/5 * * * * curl -X POST http://localhost:5000/api/bookings/release-expired-holds

# With Docker
docker compose exec backend python -c "
from app import create_app
from app.services.booking_hold import BookingHoldService
app = create_app()
with app.app_context():
    count = BookingHoldService.release_expired_holds()
    print(f'Released {count} expired holds')
"
```

### Development Login

In development mode (`FLASK_ENV=development`), you can bypass Telegram auth:

```bash
# Using curl
curl -X POST http://localhost:5000/api/auth/dev-login \
  -H "Content-Type: application/json" \
  -d '{"telegram_user_id": 300000001}'

# Available test users (after make seed):
# - Client: telegram_user_id = 300000001
# - Nutritionist (Elena): telegram_user_id = 200000001
# - Nutritionist (Michael): telegram_user_id = 200000002
# - Admin: telegram_user_id = 100000001
```

The frontend also shows a "Dev Login" button in development mode when not running inside Telegram.

### Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `BOOKING_HOLD_MINUTES` | How long a slot is held pending payment | `10` |
| `FLASK_ENV` | Set to `development` to enable dev login | `production` |

---

## 🔍 Stage 7: Results with Filters

Stage 7 implements a filterable results page that persists client search preferences.

### Key Features

- **Persistent Filters**: Client filter preferences are saved to the database
- **Onboarding Integration**: After completing onboarding, filters are auto-populated from intake answers
- **Scored Results**: Nutritionists are scored based on filter matches
- **Match Reasons**: UI shows why each nutritionist matched (e.g., "Specializes in weight loss")
- **Real-time Updates**: Filters update search results on apply

### Data Model

```sql
-- New table: client_filter_states
CREATE TABLE client_filter_states (
    client_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    intake_id UUID REFERENCES intakes(id) ON DELETE SET NULL,
    filters JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Filter Fields

| Field | Type | Description |
|-------|------|-------------|
| `goals` | string[] | Health goals (weight_loss, muscle_gain, etc.) |
| `topics` | string[] | Topics of interest (meal_planning, supplements, etc.) |
| `budget_max_rub` | number \| null | Maximum budget per session |
| `dietary` | string[] | Dietary preferences (vegetarian, vegan, etc.) |
| `help_mode` | string \| null | Type of help needed (one_time, plan, long_term) |
| `specializations` | string[] | Additional specializations |
| `tags` | string[] | Additional tags |

### Scoring Algorithm

The search endpoint scores nutritionists based on filter matches:

| Match Type | Points |
|------------|--------|
| Goal matches specialization | +3 per match |
| Topic/dietary matches tags | +1 per match |
| Has service within budget | +2 |
| Help mode matches service type | +1 |
| Rating bonus | +0.5 per rating point |

### API Examples

```bash
# Get current filters and defaults
curl http://localhost:5000/api/clients/me/filters \
  -H "Authorization: Bearer <token>"

# Response:
# {
#   "intake_id": "...",
#   "filters": {"goals": ["weight_loss"], "budget_max_rub": 5000, ...},
#   "defaults": {"goals": ["weight_loss"], ...}
# }

# Update filters
curl -X PUT http://localhost:5000/api/clients/me/filters \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "goals": ["weight_loss", "muscle_gain"],
      "budget_max_rub": 3000,
      "dietary": ["vegetarian"],
      "help_mode": "plan"
    }
  }'

# Search nutritionists with filters
curl -X POST http://localhost:5000/api/public/nutritionists/search \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "goals": ["weight_loss"],
      "budget_max_rub": 5000,
      "dietary": ["vegetarian"],
      "help_mode": "one_time"
    }
  }'

# Response:
# {
#   "nutritionists": [
#     {
#       "nutritionist_id": "...",
#       "profile": {...},
#       "score": 8.5,
#       "matched_reasons": ["Specializes in weight loss", "Within budget"]
#     }
#   ],
#   "total": 2
# }

# Get available filter options
curl http://localhost:5000/api/public/filters/options

# Response:
# {
#   "goals": [{"id": "weight_loss", "label": "Weight Loss"}, ...],
#   "topics": [...],
#   "dietary": [...],
#   "help_modes": [...],
#   "budget_ranges": [{"id": "up_to_2000", "max": 2000, "label": "Up to 2,000 ₽"}, ...]
# }
```

### Frontend Usage

1. **After Onboarding**: IntakePage submits answers → backend creates filter_state → redirects to /results
2. **On Results Page**: Load filters from `/api/clients/me/filters` → search with filters → display results
3. **Filter Drawer**: User can modify filters → Apply saves to backend → re-search

### Testing the Filter Flow

```bash
# 1. Start services
docker compose up --build

# 2. Run migrations (including new filter state table)
make migrate

# 3. Seed database
make seed

# 4. Open client
open http://localhost:5173

# 5. Complete onboarding (or skip to /results)
# 6. Click "Filters" button to open drawer
# 7. Modify filters and click "Apply"
# 8. See filtered results with match reasons
```

---

## 💳 Payment Integration

The project includes a clean payment abstraction layer that makes adding new payment providers trivial.

### Current State

- **Mock Provider**: Used by default in development. Simulates payment success without real money.
- **Payment Abstraction**: Provider interface in `app/payments/` allows plugging in real providers.
- **Unified Lifecycle**: All payments follow the same flow regardless of provider.

### Payment Flow

```
Booking (pending_payment)
    ↓
PaymentIntent created (payment record with status=created)
    ↓
Client redirected to payment URL (or mock button shown)
    ↓
Provider processes payment
    ↓
Webhook received → finalize_payment()
    ↓
Booking → paid, Slot → booked, Payment → succeeded
```

### Payment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/create` | Create payment intent for booking |
| POST | `/api/payments/webhook/{provider}` | Provider webhook handler |
| POST | `/api/payments/mock-pay/{booking_id}` | DEV: Simulate payment success |
| GET | `/api/payments/{booking_id}/status` | Get payment status |
| POST | `/api/bookings/{id}/mark-paid` | DEV shortcut (routes through abstraction) |

### Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `PAYMENT_PROVIDER` | Active provider (mock, telegram, yookassa, cloudpayments) | `mock` |
| `PAYMENT_WEBHOOK_SECRET` | Webhook signature verification key | `webhook-secret` |

### How to Plug a Real Payment Provider

Adding a new payment provider requires **one file** and **one registration**:

#### 1. Create Provider Implementation

Create a new file `backend/app/payments/telegram.py` (or your provider name):

```python
"""
Telegram Payments Provider

Implements payment via Telegram Payments (Stars).
"""

from typing import Any
from flask import current_app
import httpx  # or your HTTP library

from app.payments.base import (
    PaymentProvider,
    PaymentIntent,
    PaymentResult,
    PaymentStatus,
    PaymentWebhookError,
)


class TelegramPaymentProvider(PaymentProvider):
    """Telegram Payments (Stars) provider."""
    
    @property
    def name(self) -> str:
        return "telegram"
    
    def create_payment_intent(self, booking: Any) -> PaymentIntent:
        """Create Telegram payment invoice."""
        bot_token = current_app.config["TELEGRAM_BOT_TOKEN"]
        payment = booking.payment
        
        # Call Telegram Bot API to create invoice link
        response = httpx.post(
            f"https://api.telegram.org/bot{bot_token}/createInvoiceLink",
            json={
                "title": f"Booking #{str(booking.id)[:8]}",
                "description": booking.service.title if booking.service else "Consultation",
                "payload": str(booking.id),  # Our booking ID
                "currency": "XTR",  # Telegram Stars
                "prices": [{"label": "Consultation", "amount": booking.price_rub}],
            }
        )
        data = response.json()
        
        if not data.get("ok"):
            raise Exception(f"Telegram API error: {data.get('description')}")
        
        payment_url = data["result"]
        
        expires_at = None
        if booking.slot and booking.slot.hold_expires_at:
            expires_at = booking.slot.hold_expires_at.isoformat()
        
        return PaymentIntent(
            payment_id=str(payment.id),
            provider=self.name,
            payment_url=payment_url,
            amount_rub=booking.price_rub,
            currency=booking.currency,
            expires_at=expires_at,
        )
    
    def handle_webhook(self, payload: dict, headers: dict) -> PaymentResult:
        """Process Telegram successful_payment update."""
        # Telegram sends updates via the bot webhook
        # Extract successful_payment from the update
        
        update = payload
        message = update.get("message", {})
        successful_payment = message.get("successful_payment")
        
        if not successful_payment:
            raise PaymentWebhookError("No successful_payment in update")
        
        booking_id = successful_payment.get("invoice_payload")
        telegram_payment_id = successful_payment.get("telegram_payment_charge_id")
        
        return PaymentResult(
            booking_id=booking_id,
            provider_payment_id=telegram_payment_id,
            status=PaymentStatus.SUCCEEDED,
            raw_payload=payload,
        )
    
    def verify_signature(self, payload: dict, headers: dict) -> bool:
        """Verify Telegram webhook signature."""
        # Telegram uses a different verification method
        # Usually you verify the update came from Telegram by checking
        # the secret_token you set when registering the webhook
        secret_token = headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        expected = current_app.config.get("TELEGRAM_WEBHOOK_SECRET", "")
        
        if not expected:
            return True  # Skip verification if not configured
        
        return secret_token == expected
```

#### 2. Register the Provider

In `backend/app/payments/__init__.py`, add:

```python
from app.payments.telegram import TelegramPaymentProvider

# Add to the _PROVIDERS dict:
_PROVIDERS: dict[str, type[PaymentProvider]] = {
    "mock": MockPaymentProvider,
    "telegram": TelegramPaymentProvider,  # Add this line
}
```

#### 3. Configure Environment

```bash
# .env
PAYMENT_PROVIDER=telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret  # Optional
```

#### 4. Set Up Webhook URL

Configure your payment provider to send webhooks to:
```
https://your-domain.com/api/payments/webhook/telegram
```

### That's It!

No changes needed to:
- Booking logic
- Frontend code (it adapts to provider automatically)
- Database schema
- Existing tests

The abstraction layer handles everything else.

### Provider Implementation Checklist

When implementing a new provider, ensure you:

- [ ] Implement `name` property (unique identifier)
- [ ] Implement `create_payment_intent()` (returns PaymentIntent with payment_url)
- [ ] Implement `handle_webhook()` (returns PaymentResult with booking_id and status)
- [ ] Implement `verify_signature()` if provider requires signature verification
- [ ] Register provider in `__init__.py`
- [ ] Add provider-specific config variables to `config.py` comments
- [ ] Test the full flow: create intent → process webhook → booking confirmed

### Available Providers

| Provider | Status | Notes |
|----------|--------|-------|
| `mock` | ✅ Ready | Development/testing only |
| `telegram` | 📋 Template | Telegram Payments (Stars) |
| `yookassa` | 📋 Planned | Popular Russian payment gateway |
| `cloudpayments` | 📋 Planned | Alternative payment gateway |

---

## 📄 License

MIT License
