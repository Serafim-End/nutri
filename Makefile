# =============================================================================
# NutriMatch Makefile
# =============================================================================
# Database: PostgreSQL (Local Container)
# Deployment: Docker + Cloudflare (HTTPS)
# =============================================================================

.PHONY: help install dev build up down logs seed test lint clean migrate downgrade db-reset db-check
.PHONY: prod-up prod-down prod-logs prod-migrate prod-seed prod-shell prod-status prod-restart

# Default target
help:
	@echo ""
	@echo "NutriMatch Commands"
	@echo "==================="
	@echo ""
	@echo "🚀 Production (Recommended):"
	@echo "  make up              - Build and start all production containers"
	@echo "  make down            - Stop production containers"
	@echo "  make logs            - View production logs (all services)"
	@echo "  make migrate         - Run database migrations"
	@echo "  make seed            - Seed database with initial data"
	@echo ""
	@echo "📋 Production Logs:"
	@echo "  make logs-backend    - View backend logs only"
	@echo "  make logs-client     - View client logs only"
	@echo "  make logs-admin      - View admin panel logs only"
	@echo "  make logs-bot        - View telegram bot logs only"
	@echo ""
	@echo "🔧 Production Management:"
	@echo "  make status          - Show container status"
	@echo "  make restart         - Restart all containers"
	@echo "  make shell           - Open shell in backend container"
	@echo ""
	@echo "💻 Local Development:"
	@echo "  make dev-install     - Install dependencies locally"
	@echo "  make dev-up          - Start development containers"
	@echo "  make dev-down        - Stop development containers"
	@echo "  make dev-logs        - View development logs"
	@echo ""
	@echo "🗄️ Database:"
	@echo "  make migrate         - Run pending migrations"
	@echo "  make downgrade       - Rollback last migration"
	@echo "  make seed            - Seed test data (idempotent)"
	@echo "  make db-check        - Verify database connectivity"
	@echo "  make db-version      - Show current migration version"
	@echo "  make db-reset        - Reset database (DANGEROUS)"
	@echo ""
	@echo "🤖 Telegram Bot:"
	@echo "  make bot-dev         - Run bot locally (polling mode)"
	@echo "  make bot-install     - Install bot dependencies"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test            - Run backend tests"
	@echo "  make lint            - Run linters"
	@echo "  make clean           - Clean up containers and volumes"
	@echo ""

# =============================================================================
# PRODUCTION COMMANDS (Primary - using docker-compose.prod.yml)
# =============================================================================

# Build and start all production containers
up:
	docker compose -f docker-compose.prod.yml up -d --build

# Stop production containers
down:
	docker compose -f docker-compose.prod.yml down

# View all production logs
logs:
	docker compose -f docker-compose.prod.yml logs -f

# View specific service logs
logs-backend:
	docker compose -f docker-compose.prod.yml logs -f backend

logs-client:
	docker compose -f docker-compose.prod.yml logs -f client

logs-admin:
	docker compose -f docker-compose.prod.yml logs -f admin_panel

logs-bot:
	docker compose -f docker-compose.prod.yml logs -f telegram_bot

# Run database migrations
migrate:
	docker compose -f docker-compose.prod.yml exec backend flask db upgrade

# Seed database with initial data
seed:
	docker compose -f docker-compose.prod.yml exec backend python seed.py

# Show container status
status:
	docker compose -f docker-compose.prod.yml ps

# Restart all containers
restart:
	docker compose -f docker-compose.prod.yml restart

# Restart specific service
restart-backend:
	docker compose -f docker-compose.prod.yml restart backend

restart-bot:
	docker compose -f docker-compose.prod.yml restart telegram_bot

# Open shell in backend container
shell:
	docker compose -f docker-compose.prod.yml exec backend /bin/sh

# =============================================================================
# DEVELOPMENT COMMANDS (using docker-compose.yml)
# =============================================================================

# Install dependencies locally
dev-install:
	cd backend && pip install -r requirements.txt
	cd client && npm install
	cd apps/admin_panel && npm install
	cd apps/telegram_bot && pip install -r requirements.txt

# Start development environment
dev-up:
	docker compose up --build

# Stop development environment
dev-down:
	docker compose down

# View development logs
dev-logs:
	docker compose logs -f

# Build development images
dev-build:
	docker compose build

# =============================================================================
# DATABASE COMMANDS
# =============================================================================

# Run all pending migrations (production)
prod-migrate:
	docker compose -f docker-compose.prod.yml exec backend flask db upgrade

# Rollback last migration
downgrade:
	docker compose -f docker-compose.prod.yml exec backend flask db downgrade

# Create a new migration (development)
migrate-new:
	@echo "Creating new migration: $(msg)"
	docker compose exec backend flask db migrate -m "$(msg)"

# Seed database (development)
dev-seed:
	docker compose exec backend python seed.py

# Check database connectivity
db-check:
	@echo "Checking database connectivity..."
	@curl -s http://localhost:8000/health/db | python3 -m json.tool || echo "Failed. Is the backend running?"

# Show current migration version
db-version:
	docker compose -f docker-compose.prod.yml exec backend flask db current

# Show migration history
db-history:
	docker compose -f docker-compose.prod.yml exec backend flask db history

# DANGEROUS: Reset database (drop all, re-migrate, re-seed)
db-reset:
	@echo "⚠️  WARNING: This will DELETE all data!"
	@read -p "Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || exit 1
	@echo "Dropping all tables..."
	docker compose -f docker-compose.prod.yml exec backend flask db downgrade base
	@echo "Running migrations..."
	docker compose -f docker-compose.prod.yml exec backend flask db upgrade
	@echo "Seeding database..."
	docker compose -f docker-compose.prod.yml exec backend python seed.py
	@echo "✓ Database reset complete"

# =============================================================================
# TELEGRAM BOT
# =============================================================================

# Run bot locally in polling mode
bot-dev:
	@echo "Starting bot in polling mode (local)..."
	cd apps/telegram_bot && python bot.py

# Install bot dependencies
bot-install:
	@echo "Installing bot dependencies..."
	cd apps/telegram_bot && pip install -r requirements.txt

# =============================================================================
# TESTING & QUALITY
# =============================================================================

# Run backend tests
test:
	cd backend && pytest -v

# Run tests with coverage
test-cov:
	cd backend && pytest --cov=app --cov-report=html

# Run linters
lint:
	cd backend && black . && ruff check . && mypy app/
	cd client && npm run lint

# Format code
format:
	cd backend && black .

# =============================================================================
# CLEANUP
# =============================================================================

# Clean up production containers and volumes
clean:
	docker compose -f docker-compose.prod.yml down -v --remove-orphans
	docker system prune -f

# Clean up development containers and volumes
dev-clean:
	docker compose down -v --remove-orphans
	docker system prune -f

# =============================================================================
# LEGACY ALIASES (for backward compatibility)
# =============================================================================

# Legacy production commands (now primary)
prod-up: up
prod-down: down
prod-logs: logs
prod-seed: seed
prod-shell: shell
prod-status: status
prod-logs-backend: logs-backend
prod-logs-client: logs-client
prod-logs-admin: logs-admin
prod-logs-bot: logs-bot
prod-restart-backend: restart-backend
prod-restart-bot: restart-bot
clean-prod: clean
