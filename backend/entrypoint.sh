#!/bin/bash
# =============================================================================
# Backend Entrypoint Script
# =============================================================================
# Waits for PostgreSQL to be ready, runs migrations, then starts the app
# =============================================================================

set -e

echo "================================================"
echo "NutriMatch Backend Starting..."
echo "================================================"

# Function to check if postgres is ready
wait_for_postgres() {
    echo "Waiting for PostgreSQL to be ready..."
    
    # Extract host and port from DATABASE_URL
    # Format: postgresql://user:pass@host:port/dbname
    DB_HOST=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:/]*\).*|\1|p')
    DB_PORT=$(echo "$DATABASE_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
    
    # Default port if not specified
    DB_PORT=${DB_PORT:-5432}
    
    echo "Database host: $DB_HOST, port: $DB_PORT"
    
    # Wait for postgres to accept connections
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if python -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('$DB_HOST', $DB_PORT))
    sock.close()
    sys.exit(0 if result == 0 else 1)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; then
            echo "PostgreSQL is accepting connections!"
            break
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "Waiting for PostgreSQL... (attempt $RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "ERROR: PostgreSQL did not become ready in time!"
        exit 1
    fi
    
    # Additional wait for postgres to be fully initialized
    sleep 3
}

# Function to run migrations
run_migrations() {
    echo "================================================"
    echo "Running database migrations..."
    echo "================================================"
    
    MAX_RETRIES=5
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if flask db upgrade 2>&1; then
            echo "Migrations completed successfully!"
            return 0
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "Migration attempt $RETRY_COUNT failed, retrying in 5 seconds..."
        sleep 5
    done
    
    echo "WARNING: Migrations failed after $MAX_RETRIES attempts"
    echo "The application will start anyway - migrations might already be applied"
    return 0
}

# Main execution
echo "DATABASE_URL is set: $(echo $DATABASE_URL | sed 's/:.*@/:***@/')"

# Wait for PostgreSQL
wait_for_postgres

# Run migrations
run_migrations

echo "================================================"
echo "Starting Gunicorn server..."
echo "================================================"

# Start the application
exec gunicorn -w 2 -k gthread --threads 4 -b 0.0.0.0:8000 --access-logfile - --error-logfile - "app:create_app()"

