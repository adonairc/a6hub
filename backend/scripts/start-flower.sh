#!/bin/bash
# Start Flower monitoring dashboard for local development

echo "Starting Flower monitoring dashboard..."
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
echo "Flower dashboard will be available at: http://localhost:5555"
echo ""

# Set environment variables
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Start Flower
cd "$(dirname "$0")/.."
celery -A app.workers.celery_app flower --port=5555
