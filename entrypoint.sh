#!/bin/bash
set -e

# Function to handle SIGTERM and SIGINT
function handle_signal {
  echo "Received signal. Shutting down gracefully..."
  # Add any cleanup code here
  exit 0
}

# Register the signal handler
trap handle_signal SIGTERM SIGINT

# Start the application
echo "Starting the application..."
exec python main.py 