#!/bin/bash
set -e

# =============================================================================
# Celery Entrypoint: wait for Postgres → start Celery Worker
# Database migrations are owned exclusively by the CI/CD pipeline (alembic
# upgrade head) and are intentionally NOT executed here.
# =============================================================================

PG_HOST="${POSTGRES_SERVER:-localhost}"
PG_PORT="${POSTGRES_PORT:-5432}"
WAIT_TIMEOUT="${POSTGRES_WAIT_TIMEOUT:-30}"

echo "==> [Celery] Waiting for PostgreSQL at ${PG_HOST}:${PG_PORT}..."

start_time=$(date +%s)
while true; do
    if python -c "
import socket, sys
try:
    s = socket.create_connection(('$PG_HOST', int('$PG_PORT')), timeout=2)
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
        echo "==> [Celery] PostgreSQL is accepting connections."
        break
    fi

    elapsed=$(( $(date +%s) - start_time ))
    if [ "$elapsed" -ge "$WAIT_TIMEOUT" ]; then
        echo "ERROR: [Celery] PostgreSQL not ready after ${WAIT_TIMEOUT}s — aborting."
        exit 1
    fi

    echo "    ...not ready yet (${elapsed}s elapsed). Retrying in 1s."
    sleep 1
done

echo "==> [Celery] Starting Celery Worker with Beat..."
exec python start_celery.py
