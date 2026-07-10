#!/bin/bash
set -e

# =============================================================================
# Entrypoint: wait for Postgres → run migrations → start FastAPI
# =============================================================================

PG_HOST="${POSTGRES_SERVER:-localhost}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_USER="${POSTGRES_USER:-postgres}"
WAIT_TIMEOUT="${POSTGRES_WAIT_TIMEOUT:-30}"

echo "==> Waiting for PostgreSQL at ${PG_HOST}:${PG_PORT}..."

start_time=$(date +%s)
while true; do
    # Use a lightweight Python one-liner instead of pg_isready
    # so we don't need to install postgresql-client in the runtime image.
    if python -c "
import socket, sys
try:
    s = socket.create_connection(('$PG_HOST', int('$PG_PORT')), timeout=2)
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
        echo "==> PostgreSQL is accepting connections."
        break
    fi

    elapsed=$(( $(date +%s) - start_time ))
    if [ "$elapsed" -ge "$WAIT_TIMEOUT" ]; then
        echo "ERROR: PostgreSQL not ready after ${WAIT_TIMEOUT}s — aborting."
        exit 1
    fi

    echo "    ...not ready yet (${elapsed}s elapsed). Retrying in 1s."
    sleep 1
done

echo "==> Running database migrations (alembic upgrade head)..."
alembic upgrade head

echo "==> Starting FastAPI application..."
exec "$@"
