#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# health-check.sh — Verify backend and frontend are responding
#
# The backend is NOT exposed to the EC2 host (internal Docker networking only).
# Backend health is verified through the nginx reverse proxy at /api/health,
# which validates the full chain: nginx → docker networking → backend.
#
# Usage: health-check.sh <deploy_path>
# =============================================================================

DEPLOY_PATH="${1:?Usage: health-check.sh <deploy_path>}"
COMPOSE_FILE="${DEPLOY_PATH}/docker-compose.yml"
HEALTH_URL="https://localhost/api/health"
FRONTEND_URL="https://localhost/nginx-health"
MAX_RETRIES=30
RETRY_INTERVAL=5

echo "==> Running health checks..."

# --- Backend health check (through nginx reverse proxy) ---
echo "    Checking backend at ${HEALTH_URL} ..."
for i in $(seq 1 ${MAX_RETRIES}); do
    HTTP_STATUS=$(curl -sk -o /dev/null -w "%{http_code}" "${HEALTH_URL}" 2>/dev/null || echo "000")
    if [ "${HTTP_STATUS}" = "200" ]; then
        echo "    [OK] Backend is healthy (HTTP ${HTTP_STATUS})"
        break
    fi
    if [ "${i}" -eq "${MAX_RETRIES}" ]; then
        echo "    [FAIL] Backend did not become healthy after $((MAX_RETRIES * RETRY_INTERVAL))s"
        echo "==> Collecting backend logs..."
        docker compose -f "${COMPOSE_FILE}" logs --tail=100 backend
        exit 1
    fi
    echo "    ...retrying (${i}/${MAX_RETRIES})"
    sleep ${RETRY_INTERVAL}
done

# --- Frontend health check ---
echo "    Checking frontend at ${FRONTEND_URL} ..."
for i in $(seq 1 ${MAX_RETRIES}); do
    HTTP_STATUS=$(curl -sk -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" 2>/dev/null || echo "000")
    if [ "${HTTP_STATUS}" = "200" ]; then
        echo "    [OK] Frontend is healthy (HTTP ${HTTP_STATUS})"
        break
    fi
    if [ "${i}" -eq "${MAX_RETRIES}" ]; then
        echo "    [FAIL] Frontend did not become healthy after $((MAX_RETRIES * RETRY_INTERVAL))s"
        echo "==> Collecting frontend logs..."
        docker compose -f "${COMPOSE_FILE}" logs --tail=100 frontend
        exit 1
    fi
    echo "    ...retrying (${i}/${MAX_RETRIES})"
    sleep ${RETRY_INTERVAL}
done

echo "==> All health checks passed."
