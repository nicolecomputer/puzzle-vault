#!/bin/bash
set -e

echo "=== Starting puz-feed ==="

# Validate required environment variables
if [ -z "$DATA_PATH" ]; then
    echo "ERROR: DATA_PATH environment variable is not set"
    exit 1
fi

if [ -z "$TZ" ]; then
    echo "ERROR: TZ environment variable is not set"
    exit 1
fi

echo "✓ DATA_PATH: $DATA_PATH"
echo "✓ TZ: $TZ"

# Run database migrations
echo ""
echo "Running database migrations..."
uv run python -m scripts.migrate

if [ $? -ne 0 ]; then
    echo "ERROR: Database migrations failed"
    exit 1
fi

echo ""
echo "✓ Migrations completed successfully"

# Start services using honcho
echo ""
echo "Starting services..."
exec uv run honcho start
