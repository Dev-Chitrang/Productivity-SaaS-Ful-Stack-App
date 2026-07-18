#!/bin/bash
set -e

# =============================================================================
# Entrypoint: wait for Postgres → configure workers → start FastAPI
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

# --- Configure uvicorn workers ---
# Production: allow UVICORN_WORKERS override, else compute from CPU cores.
# Non-production: leave unset so the Dockerfile CMD defaults to 1 worker.
if [ "${ENVIRONMENT}" = "PRODUCTION" ]; then
    if [ -z "${UVICORN_WORKERS}" ]; then
        export UVICORN_WORKERS=$(python -c "
import os, math
cores = os.cpu_count() or 1
try:
    with open('/sys/fs/cgroup/cpu.max') as f:
        parts = f.read().split()
        if parts[0] != 'max':
            cgroup_cpus = math.ceil(int(parts[0]) / int(parts[1]))
            if cgroup_cpus > 0:
                cores = min(cores, cgroup_cpus)
except (OSError, ValueError, ZeroDivisionError):
    pass
workers = max((cores * 2) + 1, 2)
print(workers)
")
    fi
    echo "==> PRODUCTION — UVICORN_WORKERS=${UVICORN_WORKERS}"
else
    echo "==> ${ENVIRONMENT:-LOCAL} — single-worker mode"
fi

echo "==> Starting FastAPI application..."
exec "$@"
