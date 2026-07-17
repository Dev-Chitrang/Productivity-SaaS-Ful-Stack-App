#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# db-init.sh — Ensure the application database exists (idempotent)
#
# Safe to run on every deployment. If the database already exists this is a
# no-op. If it does not exist (first deploy on a fresh EC2) it is created.
#
# Usage: db-init.sh <deploy_path>
# =============================================================================

DEPLOY_PATH="${1:?Usage: db-init.sh <deploy_path>}"
COMPOSE_FILE="${DEPLOY_PATH}/docker-compose.yml"

# Read credentials from the .env that deploy.sh just generated
# shellcheck disable=SC1091
source "${DEPLOY_PATH}/.env"

PG_USER="${POSTGRES_USER:?POSTGRES_USER not set}"
PG_DB="${POSTGRES_DB:?POSTGRES_DB not set}"

echo "==> Ensuring database '${PG_DB}' exists..."

# Idempotent: CREATE DATABASE IF NOT EXISTS runs inside the postgres container.
docker compose -f "${COMPOSE_FILE}" exec -T postgres \
    psql -U "${PG_USER}" -d postgres -tc \
    "SELECT 1 FROM pg_database WHERE datname = '${PG_DB}'" \
    | grep -q 1 \
  && echo "    Database '${PG_DB}' already exists." \
  || {
        echo "    Creating database '${PG_DB}'..."
        docker compose -f "${COMPOSE_FILE}" exec -T postgres \
            psql -U "${PG_USER}" -d postgres -c "CREATE DATABASE \"${PG_DB}\";"
        echo "    Database '${PG_DB}' created."
     }

echo "==> Database initialization complete."
