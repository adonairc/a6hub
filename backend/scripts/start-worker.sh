#!/bin/bash
# Start Celery worker for local development

echo "Starting Celery worker for a6hub..."
echo "Make sure Redis is running on localhost:6379"
echo ""

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "ERROR: Redis is not running!"
    echo "Start Redis with: docker run -d -p 6379:6379 redis:7-alpine"
    exit 1
fi

echo "✓ Redis is running"
echo ""

# Set environment variables
export REDIS_HOST=localhost
export REDIS_PORT=6379
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432

# Start Celery worker
cd "$(dirname "$0")/.."
celery -A app.workers.celery_app worker \
    --loglevel=info \
    --queues=build,simulation \
    --concurrency=2 \
    --max-tasks-per-child=50
