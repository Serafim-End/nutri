# NutriMatch - Telegram Nutritionists Marketplace

A production-ready MVP for a Telegram-based nutritionists marketplace. Clients can find and book consultations with verified nutritionists through a Telegram Mini App.

## 🏗️ Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   Telegram Mini App │────▶│    Flask Backend    │────▶│    PostgreSQL       │
│   (React + Vite)    │     │    (REST API)       │     │    (Supabase)       │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
         ▲                           ▲
         │                           │
┌─────────────────────┐     ┌─────────────────────┐
│    Admin Panel      │     │    Telegram Bot     │
│  (React + Vite)     │     │    (aiogram v3)     │
└─────────────────────┘     └─────────────────────┘
```

## 🚀 Quick Start (Production)

### One-Command Deployment

```bash
# 1. Clone repository
git clone <repo-url> nutri
cd nutri

# 2. Configure environment (first time only)
cp .env.prod.example .env.prod
nano .env.prod  # Fill in all values

# 3. Deploy
./deploy.sh
```

That's it! Your services are now running and accessible via:
- Backend API: `https://api.nutrutioncoach.com`
- Client Mini App: `https://tma.nutrutioncoach.com`
- Admin Panel: `https://web.nutrutioncoach.com`
- Telegram Bot: `https://bot.nutrutioncoach.com` (webhook mode)

---

## 🌐 Production Deployment with Cloudflare

This project is designed for deployment with **Cloudflare** handling HTTPS and DNS. All services run on plain HTTP internally.

### Prerequisites

- A server with Docker and Docker Compose installed
- A domain managed by Cloudflare
- Supabase account (for PostgreSQL database)
- Telegram Bot token (from @BotFather)

### Step 1: DNS Configuration (Cloudflare)

Add the following DNS records in your Cloudflare dashboard:

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | api | YOUR_SERVER_IP | ✅ Proxied |
| A | web | YOUR_SERVER_IP | ✅ Proxied |
| A | tma | YOUR_SERVER_IP | ✅ Proxied |
| A | bot | YOUR_SERVER_IP | ✅ Proxied |

This creates:
- `api.nutrutioncoach.com` → Backend API (port 8000)
- `web.nutrutioncoach.com` → Admin Panel (port 3001)
- `tma.nutrutioncoach.com` → Client Mini App (port 3000)
- `bot.nutrutioncoach.com` → Telegram Bot webhook (port 8081)

### Step 2: Cloudflare SSL Configuration

In Cloudflare Dashboard → SSL/TLS:

1. **SSL Mode**: Set to **Full** (or **Full (Strict)** if you add origin certificates)
2. **Edge Certificates**: Enable "Always Use HTTPS"
3. **Minimum TLS Version**: TLS 1.2 (recommended)

> **Note**: Cloudflare provides free SSL certificates. Your services run on plain HTTP, and Cloudflare handles HTTPS termination.

### Step 3: Server Setup

```bash
# 1. SSH into your server
ssh user@your-server-ip

# 2. Install Docker (if not installed)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect

# 3. Clone the repository
git clone <repo-url> nutri
cd nutri

# 4. Create .env.prod from template
cp .env.prod.example .env.prod
nano .env.prod  # Fill in all required values (see Step 4)
```

### Step 4: Configure Environment Variables

Edit `.env.prod` with your production values. See `.env.prod.example` for detailed comments on where to get each value:

**Required values:**
- `DATABASE_URL` - From Supabase Dashboard → Database → Connection string
- `TELEGRAM_BOT_TOKEN` - From @BotFather on Telegram
- `SECRET_KEY`, `JWT_SECRET_KEY`, `BOT_SERVICE_TOKEN`, `PAYMENT_WEBHOOK_SECRET` - Generate with `openssl rand -hex 32` or use online generator

**Pre-filled values (already correct):**
- `VITE_API_BASE_URL=https://api.nutrutioncoach.com`
- `WEBHOOK_URL=https://bot.nutrutioncoach.com/webhook`
- `WEBAPP_URL=https://tma.nutrutioncoach.com`
- `CORS_ORIGINS` - Already includes all required domains

### Step 5: Deploy

```bash
# Run deployment script (builds, starts containers, runs migrations)
./deploy.sh

# Or manually:
# make up
# make migrate
# make seed  # optional: adds test data
```

**Check status:**
```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

### Step 6: Configure Telegram

1. **Set Mini App URL** in @BotFather:
   ```
   /setmenubutton
   → Select your bot
   → https://tma.nutrutioncoach.com
   ```

2. **Set Webhook** (if using webhook mode):
   ```
   /setwebhook
   → Select your bot
   → https://bot.nutrutioncoach.com/webhook
   ```

   Or use the API:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://bot.nutrutioncoach.com/webhook"
   ```

### Domain Mapping Summary

| Service | Internal Port | External URL |
|---------|---------------|--------------|
| Backend | 8000 | https://api.nutrutioncoach.com |
| Client Mini App | 3000 | https://tma.nutrutioncoach.com |
| Admin Panel | 3001 | https://web.nutrutioncoach.com |
| Telegram Bot | 8081 | https://bot.nutrutioncoach.com |

---

## 🔧 Available Commands

```bash
# Production
make up              # Start all services
make down            # Stop all services
make logs            # View logs (all)
make logs-backend    # View backend logs
make logs-bot        # View bot logs
make status          # Container status
make restart         # Restart all
make shell           # Shell into backend

# Database
make migrate         # Run migrations
make seed            # Seed data
make downgrade       # Rollback migration
make db-check        # Check connectivity

# Development
make dev-up          # Start dev environment
make dev-logs        # View dev logs
make test            # Run tests
make lint            # Run linters
```

---

## 🗄️ Database Configuration (Supabase)

This project uses **Supabase PostgreSQL** as the primary database.

### Setting DATABASE_URL

Get your connection string from Supabase Dashboard → Settings → Database:

```bash
DATABASE_URL=postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
```

The backend automatically:
- Normalizes the URL to use `postgresql+psycopg2://` driver
- Adds SSL (`sslmode=require`) for Supabase connections
- Validates the URL format on startup

### Checking Database Health

```bash
curl http://localhost:8000/health/db
```

---

## 📦 Database Migrations

Migrations are managed with **Alembic** via Flask-Migrate.

```bash
# Run all pending migrations
make migrate

# Rollback last migration
make downgrade

# Show current version
make db-version

# Show migration history
make db-history
```

### Creating New Migrations

```bash
make migrate-new msg="add user preferences"
```

---

## 🌱 Seeding Test Data

The seed script is **idempotent** - safe to run multiple times.

```bash
make seed
```

### Seeded Test Accounts

| Role | Telegram User ID | Name |
|------|-----------------|------|
| Admin | 100000001 | Admin User |
| Client | 300000001 | Test Client |
| Nutritionist | 200000001 | Dr. Elena Petrova |
| Nutritionist | 200000002 | Michael Chen, RD |

---

## 📁 Project Structure

```
nutri/
├── backend/                    # Flask API
│   ├── app/
│   │   ├── __init__.py        # App factory
│   │   ├── config.py          # Configuration
│   │   ├── models/            # SQLAlchemy models
│   │   ├── routes/            # API blueprints
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── migrations/            # Alembic migrations
│   └── Dockerfile
├── client/                     # React Mini App
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── design-system/     # Design tokens & primitives
│   │   ├── hooks/             # React hooks
│   │   ├── pages/             # Page components
│   │   └── store/             # Zustand stores
│   └── Dockerfile
├── apps/
│   ├── admin_panel/           # Admin Panel (React)
│   │   └── Dockerfile
│   └── telegram_bot/          # Telegram Bot (aiogram v3)
│       └── Dockerfile
├── docker-compose.yml         # Development
├── docker-compose.prod.yml    # Production
├── .env.prod.example          # Environment template
├── deploy.sh                  # Deployment script
├── nginx/                     # Nginx reverse proxy config
│   └── nginx.conf
├── Makefile                   # Commands
└── README.md
```

---

## 🔌 API Endpoints

### Health Checks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/db` | Database connectivity |

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/telegram/verify` | Verify Telegram initData |

### Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/public/nutritionists` | List nutritionists |
| GET | `/api/public/nutritionists/{id}` | Get details |
| POST | `/api/public/nutritionists/search` | Search with filters |

### Bookings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bookings` | Create booking |
| POST | `/api/bookings/{id}/cancel` | Cancel booking |

See [docs/API.md](docs/API.md) for complete API documentation.

---

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `SECRET_KEY` | Flask secret key | ✅ |
| `JWT_SECRET_KEY` | JWT signing key | ✅ |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | ✅ |
| `BOT_SERVICE_TOKEN` | Bot-backend auth token | ✅ |
| `VITE_API_BASE_URL` | API URL for frontend | ✅ |
| `CORS_ORIGINS` | Allowed CORS origins | ✅ |
| `TELEGRAM_MODE` | `polling` or `webhook` | |
| `WEBHOOK_URL` | Webhook URL (if webhook mode) | |
| `PAYMENT_PROVIDER` | `mock`, `telegram`, etc. | |

---

## 🧪 Testing

```bash
# Run backend tests
make test

# With coverage
make test-cov
```

---

## 🛡️ Security Notes

- JWT tokens expire after 24 hours (configurable)
- All nutritionist endpoints verify ownership
- Telegram initData signature is verified
- SSL is enforced for Supabase connections
- CORS is configured for allowed origins only

---

## 💳 Payment Integration

The project includes a payment abstraction layer. Default is `mock` provider for development.

Available providers:
- `mock` - Development/testing
- `telegram` - Telegram Payments (Stars)
- `yookassa` - Russian payment gateway
- `cloudpayments` - Alternative gateway

See [docs/API.md](docs/API.md) for payment integration details.

---

## 🐛 Troubleshooting

### Container won't start
```bash
# Check logs
make logs-backend

# Check status
make status
```

### Database connection failed

**Error: "Network is unreachable" or "connection refused"**

This usually means Supabase is blocking connections from your server IP.

**Solution:**
1. Get your server's public IP:
   ```bash
   curl ifconfig.me
   ```

2. Add IP to Supabase allowlist:
   - Go to Supabase Dashboard → Settings → Database
   - Find "Connection Pooling" or "Network Restrictions"  
   - Add your server's public IP address
   - Save changes

3. Use Connection Pooling URL (recommended):
   - In Supabase Dashboard → Database → Connection string
   - Select "Connection pooling" mode (port 6543)
   - Use this URL instead of direct connection (port 5432)

4. Verify connection:
   ```bash
   make db-check
   # or
   docker compose -f docker-compose.prod.yml exec backend curl http://localhost:8000/health/db
   ```

### Telegram webhook not working
```bash
# Check webhook status
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Set webhook manually
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://bot.nutrutioncoach.com/webhook"
```

### CORS errors
Ensure `CORS_ORIGINS` includes your frontend domains with `https://` prefix.

---

## 📄 License

MIT License
