#!/bin/bash
# =============================================================================
# Production Deployment Script
# =============================================================================
# Usage: ./deploy.sh
# This script will:
#   1. Check if .env.prod exists, create from example if not
#   2. Build and start all containers
#   3. Run database migrations
# =============================================================================

set -e  # Exit on error

echo "🚀 Starting deployment..."

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "⚠️  .env.prod not found!"
    if [ -f .env.prod.example ]; then
        echo "📋 Creating .env.prod from .env.prod.example..."
        cp .env.prod.example .env.prod
        echo "✅ Created .env.prod"
        echo ""
        echo "⚠️  IMPORTANT: Please edit .env.prod and fill in all values!"
        echo "   Then run this script again: ./deploy.sh"
        exit 1
    else
        echo "❌ Error: .env.prod.example not found!"
        exit 1
    fi
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    exit 1
fi

# Build and start containers
echo "🔨 Building and starting containers..."
docker compose -f docker-compose.prod.yml up -d --build

# Wait for backend to be healthy
echo "⏳ Waiting for backend to be ready..."
sleep 15

# Check if backend is healthy
echo "🔍 Checking backend health..."
if ! docker compose -f docker-compose.prod.yml exec -T backend curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Backend health check failed, but continuing..."
fi

# Test database connection
echo "🔍 Testing database connection..."
if ! docker compose -f docker-compose.prod.yml exec -T backend curl -f http://localhost:8000/health/db > /dev/null 2>&1; then
    echo "❌ Database connection failed!"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check DATABASE_URL in .env.prod is correct"
    echo "2. Verify Supabase allows connections from your server IP:"
    echo "   - Go to Supabase Dashboard → Settings → Database"
    echo "   - Add your server IP to 'Connection Pooling' or 'Direct Connection' allowlist"
    echo "3. Try using Connection Pooling URL (port 6543) instead of Direct (port 5432)"
    echo "4. Check server firewall allows outbound connections to Supabase"
    echo ""
    echo "View backend logs: docker compose -f docker-compose.prod.yml logs backend"
    exit 1
fi

# Run migrations
echo "🗄️  Running database migrations..."
if ! docker compose -f docker-compose.prod.yml exec -T backend flask db upgrade; then
    echo "❌ Migration failed!"
    echo "View logs: docker compose -f docker-compose.prod.yml logs backend"
    exit 1
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Check status: docker compose -f docker-compose.prod.yml ps"
echo "📋 View logs: docker compose -f docker-compose.prod.yml logs -f"
echo ""

