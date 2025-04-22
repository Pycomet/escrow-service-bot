#!/bin/bash
set -e

# Function to handle SIGTERM and SIGINT
function handle_signal {
  echo "Received signal. Shutting down gracefully..."
  # Add any cleanup code here
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

if [ "$WEBHOOK_MODE" = "True" ] && [ -z "$WEBHOOK_URL" ]; then
  echo "ERROR: WEBHOOK_MODE is True but WEBHOOK_URL is not set. Exiting."
  exit 1
fi

# Start the application
echo "Starting the application..."
exec python main.py 