#!/bin/bash
set -e

# Function to handle SIGTERM and SIGINT
function handle_signal {
  echo "Received signal. Shutting down gracefully..."
  # Add any cleanup code here
  kill -TERM "$child" 2>/dev/null
  exit 0
}

# Register the signal handlers
trap handle_signal SIGTERM SIGINT

# Check for required environment variables
if [ -z "$TOKEN" ]; then
  echo "ERROR: Telegram Bot TOKEN is not set. Exiting."
  exit 1
fi

if [ -z "$DATABASE_URL" ]; then
  echo "ERROR: DATABASE_URL is not set. Exiting."
  exit 1
fi

if [ -z "$WEBHOOK_URL" ]; then
  echo "ERROR: WEBHOOK_URL is not set. Exiting."
  exit 1
fi

# Setup Hypercorn environment variables if not already set
export HYPERCORN_WORKERS=${HYPERCORN_WORKERS:-1}
export HYPERCORN_ACCESSLOG=${HYPERCORN_ACCESSLOG:--}
export HYPERCORN_ERRORLOG=${HYPERCORN_ERRORLOG:--}

# Start the application with Hypercorn
echo "Starting the application with Hypercorn..."
echo "Using PORT: ${PORT:-8080}"
echo "Using WORKERS: ${HYPERCORN_WORKERS}"

# Start Hypercorn with simpler configuration
hypercorn main:app \
  --bind 0.0.0.0:${PORT:-8080} \
  --workers ${HYPERCORN_WORKERS} \
  --access-logfile "${HYPERCORN_ACCESSLOG}" \
  --error-logfile "${HYPERCORN_ERRORLOG}" \
  --worker-class asyncio &

child=$!
wait "$child" 