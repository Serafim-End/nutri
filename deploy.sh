#!/bin/bash
# Production Deployment Script
# Usage: ./deploy.sh

set -e

# Enable BuildKit for faster builds with cache mounts
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

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

# 2.5. Check if BuildKit is available
if ! docker buildx version &> /dev/null; then
    echo "⚠️  Warning: docker buildx not found. BuildKit cache mounts may not work."
    echo "   Install buildx: docker buildx install"
    echo "   Or enable BuildKit in Docker daemon config: /etc/docker/daemon.json"
    echo ""
fi

# 3. Detect which docker compose command is available
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Neither 'docker compose' nor 'docker-compose' found!"
    exit 1
fi

# 4. Build and start all containers
echo "🔨 Building and starting containers..."
$COMPOSE_CMD -f docker-compose.prod.yml up -d --build

# 4. Wait for services to be ready
echo "⏳ Waiting for services..."
sleep 20

# 5. Show status
echo ""
$COMPOSE_CMD -f docker-compose.prod.yml ps
echo ""
echo "✅ Deployment complete!"
echo ""
echo "Useful commands:"
echo "  Logs:    $COMPOSE_CMD -f docker-compose.prod.yml logs -f"
echo "  Status:  $COMPOSE_CMD -f docker-compose.prod.yml ps"
echo "  Stop:    $COMPOSE_CMD -f docker-compose.prod.yml down"
