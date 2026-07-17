#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# deploy.sh — Deploy application to production server
#
# Expects environment variables:
#   APP_ENV         — JSON string of environment variables (set by GitHub Actions)
#   BACKEND_IMAGE   — Full DockerHub image name for backend
#   FRONTEND_IMAGE  — Full DockerHub image name for frontend
#   IMAGE_TAG       — Image tag to deploy (default: latest)
#
# Usage: deploy.sh <workspace_path> <deploy_path>
# =============================================================================

WORKSPACE_PATH="${1:?Usage: deploy.sh <workspace_path> <deploy_path>}"
DEPLOY_PATH="${2:?Usage: deploy.sh <workspace_path> <deploy_path>}"

APP_ENV="${APP_ENV:?APP_ENV environment variable is required}"
BACKEND_IMAGE="${BACKEND_IMAGE:?BACKEND_IMAGE environment variable is required}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:?FRONTEND_IMAGE environment variable is required}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

export BACKEND_IMAGE FRONTEND_IMAGE IMAGE_TAG

cd "${DEPLOY_PATH}"

# --- Step 1: Pull latest code ---
echo "==> Fetching latest code..."
git fetch origin
git reset --hard origin/main
git clean -fd
echo "==> Code updated to latest main."

# --- Step 2: Generate .env from APP_ENV (read directly from environment) ---
echo "==> Generating .env from APP_ENV..."
jq -r 'to_entries[] | "\(.key)=\(.value)"' <<<"${APP_ENV}" > "${DEPLOY_PATH}/.env"
echo "==> .env generated successfully."

# --- Step 3: Pull pre-built images (never build on the production server) ---
echo "==> Pulling pre-built images from DockerHub..."
docker compose pull

# --- Step 4: Start infrastructure first (postgres + redis) and wait for healthy ---
echo "==> Starting infrastructure services..."
docker compose up -d --pull always --no-build --no-deps postgres redis

echo "==> Waiting for PostgreSQL to become healthy..."
for i in $(seq 1 30); do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' saas_postgres 2>/dev/null || echo "unknown")
    if [ "${STATUS}" = "healthy" ]; then
        echo "    PostgreSQL is healthy."
        break
    fi
    if [ "${i}" -eq 30 ]; then
        echo "ERROR: PostgreSQL did not become healthy within 5 minutes."
        docker compose logs --tail=50 postgres
        exit 1
    fi
    echo "    ...waiting (${i}/30)"
    sleep 10
done

# --- Step 5: Start all services (pull only, never build) ---
echo "==> Starting all services..."
docker compose up -d --pull always --no-build --remove-orphans

echo "==> Deployment complete. Containers starting..."
