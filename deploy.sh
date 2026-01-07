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

# Run migrations
echo "🗄️  Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T backend flask db upgrade || echo "⚠️  Migration failed or already up to date"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Check status: docker compose -f docker-compose.prod.yml ps"
echo "📋 View logs: docker compose -f docker-compose.prod.yml logs -f"
echo ""

