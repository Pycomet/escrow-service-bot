#!/bin/bash
set -e

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "🚀 Deploying Escrow Service Bot..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
  echo "🛑 Error: Docker is not running. Please start Docker and try again."
  exit 1
fi

# Build and deploy using docker-compose
echo "🔨 Building Docker image..."
docker compose build

echo "🏃 Starting Docker container..."
docker compose up -d

echo "✅ Deployment complete!"
echo "ℹ️ To check container status: docker-compose ps"
echo "ℹ️ To view logs: docker-compose logs -f"
echo "ℹ️ To stop the container: docker-compose down" 