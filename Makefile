# NutriMatch Makefile
# Database: Supabase PostgreSQL

.PHONY: help install dev build up down logs seed test lint clean migrate downgrade db-reset db-check

# Default target
help:
	@echo "NutriMatch Development Commands"
	@echo "================================"
	@echo ""
	@echo "Setup & Development:"
	@echo "  make install      - Install dependencies (local dev)"
	@echo "  make dev          - Start development servers locally"
	@echo "  make up           - Start Docker containers"
	@echo "  make down         - Stop Docker containers"
	@echo "  make build        - Build Docker images"
	@echo "  make logs         - View container logs"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      - Run all pending migrations"
	@echo "  make downgrade    - Rollback last migration"
	@echo "  make seed         - Seed database with test data (idempotent)"
	@echo "  make db-check     - Verify database connectivity"
	@echo "  make db-reset     - Drop all tables and re-run migrations (DANGEROUS)"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make clean        - Clean up containers and volumes"
	@echo ""
	@echo "Shells:"
	@echo "  make shell-backend - Open shell in backend container"
	@echo "  make shell-db      - Open PostgreSQL shell"

# ============================================
# LOCAL DEVELOPMENT
# ============================================

install:
	cd backend && pip install -r requirements.txt
	cd client && npm install

dev:
	@echo "Starting backend..."
	cd backend && flask run --debug &
	@echo "Starting client..."
	cd client && npm run dev

# ============================================
# DOCKER COMMANDS
# ============================================

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-client:
	docker compose logs -f client

# ============================================
# DATABASE COMMANDS
# ============================================

# Run all pending migrations
migrate:
	@echo "Running database migrations..."
	docker compose exec backend flask db upgrade
	@echo "✓ Migrations complete"

# Run migrations locally (without Docker)
migrate-local:
	@echo "Running database migrations (local)..."
	cd backend && flask db upgrade
	@echo "✓ Migrations complete"

# Rollback last migration
downgrade:
	@echo "Rolling back last migration..."
	docker compose exec backend flask db downgrade
	@echo "✓ Rollback complete"

# Rollback last migration locally
downgrade-local:
	@echo "Rolling back last migration (local)..."
	cd backend && flask db downgrade
	@echo "✓ Rollback complete"

# Create a new migration
migrate-new:
	@echo "Creating new migration: $(msg)"
	docker compose exec backend flask db migrate -m "$(msg)"

# Seed database with test data (idempotent - safe to run multiple times)
seed:
	@echo "Seeding database..."
	docker compose exec backend python seed.py
	@echo "✓ Seed complete"

# Seed database locally
seed-local:
	@echo "Seeding database (local)..."
	cd backend && python seed.py
	@echo "✓ Seed complete"

# Check database connectivity
db-check:
	@echo "Checking database connectivity..."
	@curl -s http://localhost:5000/health/db | python3 -m json.tool || echo "Failed to connect. Is the backend running?"

# DANGEROUS: Reset database (drop all, re-migrate, re-seed)
db-reset:
	@echo "⚠️  WARNING: This will DELETE all data!"
	@read -p "Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || exit 1
	@echo "Dropping all tables..."
	docker compose exec backend flask db downgrade base
	@echo "Running migrations..."
	docker compose exec backend flask db upgrade
	@echo "Seeding database..."
	docker compose exec backend python seed.py
	@echo "✓ Database reset complete"

# Show current migration version
db-version:
	docker compose exec backend flask db current

# Show migration history
db-history:
	docker compose exec backend flask db history

# ============================================
# SHELL ACCESS
# ============================================

shell-backend:
	docker compose exec backend /bin/sh

shell-db:
	docker compose exec postgres psql -U postgres -d nutrimatch

# ============================================
# TESTING
# ============================================

test:
	cd backend && pytest -v

test-cov:
	cd backend && pytest --cov=app --cov-report=html

# ============================================
# LINTING & FORMATTING
# ============================================

lint:
	cd backend && black . && ruff check . && mypy app/
	cd client && npm run lint

format:
	cd backend && black .

# ============================================
# CLEANUP
# ============================================

clean:
	docker compose down -v --remove-orphans
	docker system prune -f

# ============================================
# PRODUCTION
# ============================================

prod-up:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down
