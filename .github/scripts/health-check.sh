#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# health-check.sh — Verify backend and frontend are responding
#
# Usage: health-check.sh <deploy_path>
# =============================================================================

DEPLOY_PATH="${1:?Usage: health-check.sh <deploy_path>}"
COMPOSE_FILE="${DEPLOY_PATH}/docker-compose.yml"
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:80"
MAX_RETRIES=30
RETRY_INTERVAL=5

echo "==> Running health checks..."

# --- Backend health check ---
echo "    Checking backend at ${BACKEND_URL}/health ..."
for i in $(seq 1 ${MAX_RETRIES}); do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/health" 2>/dev/null || echo "000")
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
echo "    Checking frontend at ${FRONTEND_URL}/nginx-health ..."
for i in $(seq 1 ${MAX_RETRIES}); do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}/nginx-health" 2>/dev/null || echo "000")
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
