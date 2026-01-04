#!/bin/bash
set -euo pipefail

# IMAGE_TAG is passed from GitHub Actions
IMAGE_TAG=${IMAGE_TAG:-latest}
IMAGE="gopiganeprak/task-tarcker:$IMAGE_TAG"

APP_PORT=8000
HEALTH_ENDPOINT="/health"
PORT_A=8001
PORT_B=8002
NGINX_CONF="/etc/nginx/sites-available/task_api"
NEW_CONTAINER="app_candidate"
ACTIVE_CONTAINER="app_active"

echo "Starting deployment of $IMAGE..."

# Detect active port
ACTIVE_PORT=$(grep -oE '127.0.0.1:[0-9]+' "$NGINX_CONF" | cut -d: -f2)
NEW_PORT=$([ "$ACTIVE_PORT" == "$PORT_A" ] && echo $PORT_B || echo $PORT_A)

echo "Active port: $ACTIVE_PORT, New port: $NEW_PORT"

# Cleanup leftover candidate
docker rm -f $NEW_CONTAINER 2>/dev/null || true

# Run new container
docker run -d --name $NEW_CONTAINER -p 127.0.0.1:$NEW_PORT:$APP_PORT $IMAGE

# Wait for app startup
sleep 10

# Health check
if curl -sf http://127.0.0.1:$NEW_PORT$HEALTH_ENDPOINT > /dev/null; then
  echo "✅ New container healthy"
  sed -i "s/127.0.0.1:$ACTIVE_PORT/127.0.0.1:$NEW_PORT/" "$NGINX_CONF"
  nginx -s reload
  docker rm -f $ACTIVE_CONTAINER 2>/dev/null || true
  docker rename $NEW_CONTAINER $ACTIVE_CONTAINER
  echo "🎉 Deployment successful"
else
  echo "❌ Health check failed"
  docker rm -f $NEW_CONTAINER
  echo "♻️ Old version still running"
  exit 1
fi
