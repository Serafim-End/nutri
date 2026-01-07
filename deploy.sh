#!/bin/bash
# Production Deployment Script
# Usage: ./deploy.sh

set -e

echo "🚀 Starting deployment..."

# 1. Check .env.prod exists
if [ ! -f .env.prod ]; then
    echo "❌ .env.prod not found!"
    echo ""
    echo "Create it from example:"
    echo "  cp .env.prod.example .env.prod"
    echo "  nano .env.prod  # edit and fill in your values"
    exit 1
fi

# 2. Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    exit 1
fi

# 3. Build and start all containers
echo "🔨 Building and starting containers..."
docker-compose -f docker-compose.prod.yml up -d --build

# 4. Wait for services to be ready
echo "⏳ Waiting for services..."
sleep 20

# 5. Show status
echo ""
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "✅ Deployment complete!"
echo ""
echo "Useful commands:"
echo "  Logs:    docker-compose -f docker-compose.prod.yml logs -f"
echo "  Status:  docker-compose -f docker-compose.prod.yml ps"
echo "  Stop:    docker-compose -f docker-compose.prod.yml down"
