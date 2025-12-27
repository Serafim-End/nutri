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
| POST | `/api/clients/intakes` | Submit intake questionnaire |
| GET | `/api/clients/matches?intake_id=...` | Get matched nutritionists |
| GET | `/api/clients/bookings` | List client's bookings |

### Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/public/nutritionists` | List approved nutritionists |
| GET | `/api/public/nutritionists/{id}` | Get nutritionist details |
| GET | `/api/public/nutritionists/{id}/services` | List services |
| GET | `/api/public/nutritionists/{id}/slots` | List available slots |

### Bookings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bookings` | Create booking (holds slot 10 min) |
| GET | `/api/bookings/{id}` | Get booking details |
| POST | `/api/bookings/{id}/cancel` | Cancel booking |
| POST | `/api/bookings/release-expired-holds` | Cron: release expired holds |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/webhook` | Payment provider webhook |
| POST | `/api/payments/test-success/{booking_id}` | Dev: simulate payment |

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

## 📄 License

MIT License
