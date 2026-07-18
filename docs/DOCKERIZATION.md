# Dockerization

## Overview

The application is fully containerized using Docker Compose. The architecture follows a microservice-inspired layout with six containers: a React SPA served by nginx, a FastAPI backend, a Celery worker+beat process, PostgreSQL, Redis, and Mailpit. Containers communicate over two isolated bridge networks. Persistent data is stored in named Docker volumes.

```
                    ┌─────────────┐
                    │   Browser   │
                    └──────┬──────┘
                           │ :80
                    ┌──────▼──────┐
                    │   Frontend  │  nginx (React SPA)
                    │  (alpine)   │
                    └──────┬──────┘
                           │ :8000
         ┌─────────────────▼─────────────────┐
         │            Backend Net             │
         │                                    │
         │  ┌──────────┐    ┌──────────┐     │
         │  │ Backend  │◄──►│ Celery   │     │
         │  │ FastAPI  │    │ Worker+  │     │
         │  │ :8000    │    │ Beat     │     │
         │  └────┬─────┘    └────┬─────┘     │
         │       │               │            │
         │  ┌────▼─────┐  ┌─────▼──────┐    │
         │  │PostgreSQL│  │   Redis    │    │
         │  │ :5432    │  │   :6379    │    │
         │  └──────────┘  └────────────┘    │
         │                                    │
         │  ┌──────────────┐                 │
         │  │   Mailpit    │                 │
         │  │  SMTP :1025  │                 │
         │  │  WebUI :8025 │                 │
         │  └──────────────┘                 │
         └────────────────────────────────────┘
```

---

## Docker Images

### Backend

**`backend/Dockerfile`** — Multi-stage build using Python 3.11-slim.

**Stage 1 — Builder:**
- Installs `uv` (Astral package manager) and `build-essential` for compiling native extensions.
- Creates a virtualenv at `/opt/venv` and installs all packages from `requirements.txt` via pip.

**Stage 2 — Runtime:**
- Copies the virtualenv from the builder stage (compilers are discarded).
- Installs only `libmagic1` (required by `python-magic`).
- Creates a non-root `appuser` (UID 1000) for security.
- Copies application code: `app/`, `alembic/`, `alembic.ini`, `entrypoint.sh`, `celery_entrypoint.sh`.
- Creates `/app/downloads` and `/app/logs` directories owned by `appuser`.
- Runs `entrypoint.sh` as the ENTRYPOINT (waits for Postgres, starts Uvicorn with dynamic workers on port 8000).

### Frontend

**`frontend/Dockerfile`** — Multi-stage build using Node 22-alpine and nginx stable-alpine.

**Stage 1 — Builder:**
- Installs dependencies via `npm ci --ignore-scripts`.
- Accepts a build arg `VITE_API_URL` for compile-time API URL injection.
- Builds the production bundle with `npm run build`.

**Stage 2 — Runtime:**
- Uses `nginx:stable-alpine` as the base (no Node.js in the final image).
- Replaces the default nginx config with a custom `nginx.conf` that serves the SPA, proxies `/api/` to `backend:8000`, and proxies `/ws/` for WebSocket connections.
- Copies the built `dist/` output into `/usr/share/nginx/html`.
- Exposes port 80.

### Image Reuse for Celery

The Celery container reuses the backend image directly:

```yaml
celery:
  image: ${BACKEND_IMAGE}:${IMAGE_TAG}  # same image used by the backend service
  entrypoint: ["/app/celery_entrypoint.sh"]
```

The `celery_entrypoint.sh` script waits for PostgreSQL then executes `start_celery.py` — which spawns both a Celery worker process and a Celery beat scheduler process. This avoids maintaining a separate Dockerfile for the background task runner.

---

## Containers

### Frontend (`saas_frontend`)

- **Image:** Custom-built from `frontend/Dockerfile`.
- **Port:** `80` (HTTP).
- **Responsibility:** Serves the compiled React single-page application via nginx. Acts as a reverse proxy for API calls (`/api/`) and WebSocket connections (`/ws/`), forwarding them to the backend container on port 8000. Implements gzip compression, aggressive caching for hashed Vite assets, and SPA client-side routing fallback.
- **Health check:** `wget -qO- http://localhost/nginx-health` every 15s.

### Backend (`saas_backend`)

- **Image:** Pulled from DockerHub (`chitrangpotdar/productivity-backend`).
- **Port:** `8000` (FastAPI/Uvicorn).
- **Responsibility:** Serves the FastAPI application with Uvicorn. On startup, the entrypoint waits for PostgreSQL then launches the application. Handles all REST API endpoints, authentication (JWT, Google OAuth), file uploads/downloads, WebSocket signaling for meetings, and email sending (via Mailpit in local, or Brevo in production).
- **Health check:** HTTP request to `/health` via Python `urllib` every 15s.
- **Volumes:** Mounts `logs_data` at `/app/logs` and `uploads_data` at `/app/downloads`.
- **Environment:** Reads all configuration from `.env` via `env_file`.

### Celery (`saas_celery`)

- **Image:** Reuses the backend image from DockerHub (`chitrangpotdar/productivity-backend`).
- **Responsibility:** Runs background tasks and scheduled jobs. The entrypoint spawns two processes via `start_celery.py`:
  - **Celery Worker** — executes queued tasks (email sending, meeting transcript analysis, notification delivery, etc.).
  - **Celery Beat** — schedules periodic tasks (e.g., recurring reminders, cleanup jobs).
  Both processes are supervised: if one crashes, the other is terminated and the container exits, triggering a Docker restart.
- **Health check:** `celery inspect ping` every 30s.
- **Volumes:** Same as backend (`logs_data`, `uploads_data`) so task output is accessible.

### PostgreSQL (`saas_postgres`)

- **Image:** `postgres:16-alpine`.
- **Port:** `5432`.
- **Responsibility:** Primary relational data store. Hosts the `productivity_db` database. Credentials are passed via environment variables from `.env` (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`). Data persists in the `postgres_data` named volume at `/var/lib/postgresql/data`.
- **Health check:** `pg_isready` every 10s.
- **Note:** `POSTGRES_PASSWORD` is required (uses `:?` syntax in Compose to fail fast if missing).

### Redis (`saas_redis`)

- **Image:** `redis:7.2-alpine`.
- **Port:** `6379`.
- **Responsibility:** Serves three roles — caching layer, JWT session whitelisting, and Celery message broker. Runs with `--appendonly yes` for AOF persistence. Data persists in the `redis_data` named volume at `/data`.
- **Health check:** `redis-cli ping` every 10s.

### Mailpit (`saas_mailpit`)

- **Image:** `axllent/mailpit:v1.15`.
- **Ports:** `1025` (SMTP), `8025` (Web UI).
- **Responsibility:** Local development SMTP server that intercepts all outgoing email. The backend connects to port 1025 as its SMTP server. Caught emails can be viewed in a browser at `http://localhost:8025`. Data persists in the `mailpit_data` named volume at `/data`. This is a development-only service and should not be included in production deployments.
- **Health check:** HTTP request to `http://localhost:8025/` every 15s.

---

## Networks

Two bridge networks isolate traffic:

| Network | Name | Containers |
|---|---|---|
| `backend_net` | `saas_backend_net` | backend, celery, postgres, redis, mailpit, frontend |
| `frontend_net` | `saas_frontend_net` | frontend only |

- **`backend_net`** connects all backend-tier containers. This is where API requests, database connections, Redis communication, Celery broker traffic, and SMTP traffic flow.
- **`frontend_net`** is attached only to the frontend container, reserving it for direct external connectivity.

The frontend container joins **both** networks so it can reach the backend container by its service name (`backend`) on `backend_net`, while remaining the sole entry point for browser traffic. PostgreSQL, Redis, and Mailpit are not exposed to the frontend network, enforcing a clean network boundary.

---

## Volumes

| Volume | Name | Mount Point | Purpose |
|---|---|---|---|
| `postgres_data` | `saas_postgres_data` | `/var/lib/postgresql/data` | PostgreSQL database files. Ensures data survives container restarts and rebuilds. |
| `redis_data` | `saas_redis_data` | `/data` | Redis AOF persistence file. Maintains cache, session data, and Celery broker state across restarts. |
| `mailpit_data` | `saas_mailpit_data` | `/data` | Mailpit message store. Preserves captured emails across container restarts. |
| `logs_data` | `saas_logs_data` | `/app/logs` | Application logs written by both the backend and celery containers. Shared between the two so logs are centrally accessible. |
| `uploads_data` | `saas_uploads_data` | `/app/downloads` | User-uploaded files and download artifacts. Shared between backend and celery so background tasks can access uploaded files. |

All volumes are named volumes (managed by Docker), ensuring data persists independently of container lifecycle.

---

## Startup Order

The startup sequence is enforced through `depends_on` with `condition: service_healthy`:

```
PostgreSQL + Redis  (start in parallel)
       │
       ▼
    Backend  (waits for both Postgres AND Redis to be healthy)
       │
       ▼
    Celery  (waits for Backend, Postgres, AND Redis to be healthy)
    Frontend (waits for Backend to be healthy)
       │
       ▼
  Ready to serve traffic
```

**1. PostgreSQL and Redis** — Start first and in parallel. Docker health checks confirm they are accepting connections before any dependent service begins its startup sequence.

**2. Backend** — Waits for both Postgres and Redis to report healthy. The `entrypoint.sh` script then performs a socket-level connection check (retrying up to 30 seconds) as a second layer of protection. Once confirmed, Alembic runs `upgrade head` to apply any pending migrations, then Uvicorn starts serving the FastAPI application.

**3. Celery** — Waits for the backend, Postgres, and Redis. Its own `celery_entrypoint.sh` independently verifies Postgres connectivity, then starts the Celery worker and beat processes via `start_celery.py`. Migrations are intentionally NOT run here — they are handled by the CI/CD pipeline and the backend entrypoint.

**4. Frontend** — Waits for the backend to be healthy. Once the backend is ready, nginx starts and begins serving the React SPA and proxying requests to the backend.

This layered approach ensures no service attempts to connect to a dependency that is not yet ready.

---

## Environment Variables

All configuration is centralized in a single `.env` file at the project root. The `.env.example` file serves as a documented template.

**How `.env` is consumed:**

- **Backend and Celery containers** — loaded via `env_file: .env` in `docker-compose.yml`. This injects all variables (`POSTGRES_*`, `REDIS_*`, `JWT_*`, `SMTP_*`, `GOOGLE_*`, `AWS_*`, etc.) into the container environment.
- **Frontend build** — the `VITE_API_URL` variable is passed as a Docker build argument (`args: VITE_API_URL: ${VITE_API_URL:-}`), making it available at compile time via Vite's `import.meta.env`. When running through Docker Compose, this is typically left empty because nginx proxies `/api/` requests.
- **PostgreSQL** — `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` are passed directly as environment variables to the Postgres container. The compose file uses `${VAR:-default}` for optional values and `${VAR:?error}` for required values (Postgres password fails fast if unset).

**Key variable groups:**

| Group | Variables | Purpose |
|---|---|---|
| Application | `ENVIRONMENT` | Runtime environment (LOCAL / STAGING / PRODUCTION) |
| Frontend | `VITE_API_URL`, `VITE_GOOGLE_CLIENT_ID`, `VITE_VAPID_PUBLIC_KEY` | Build-time config injected into the React bundle |
| PostgreSQL | `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Database connection parameters |
| Redis | `REDIS_HOST`, `REDIS_PORT`, `REDIS_CELERY_BROKER_URL` | Cache and message broker connection |
| JWT | `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET_KEY` | Token signing secrets |
| SMTP | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USE_TLS`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL` | Email delivery configuration |
| OAuth | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | Google OAuth integration |
| Storage | `STORAGE_BASE_DIR`, `AWS_*` | Local or S3 file storage |
| Frontend URL | `FRONTEND_URL` | Used by backend to build links in emails |
| AI | `NVIDIA_NIM_API_KEY` | Meeting transcript analysis |
| Web Push | `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY` | Push notification keys |

---

## Running Locally

### Start all services

```bash
docker compose up -d
```

Builds images (if not already built) and starts all six containers in detached mode. First run takes longer due to image builds and dependency installation.

### Stop all services

```bash
docker compose down
```

Stops and removes all containers, networks. Volumes are **preserved** (data is not lost).

To remove volumes as well (full reset):

```bash
docker compose down -v
```

### View logs

```bash
# All services
docker compose logs

# Specific service (follow mode)
docker compose logs -f backend

# Tail last 100 lines
docker compose logs --tail 100 celery
```

### Check container status

```bash
docker compose ps
```

Displays running container names, status, and port mappings.

---

## Production Notes

The Docker images built for local development are the same images used in production. No separate Dockerfiles are needed.

**Backend image (`saas_backend`):**
- The multi-stage build already produces a minimal, production-ready image (no compilers, non-root user, only runtime dependencies).
- In production, the same image is deployed with a production `.env` that switches `SMTP_HOST` to an actual mail provider (e.g., Brevo), configures `AWS_*` variables for S3 storage, and sets `ENVIRONMENT=PRODUCTION`.
- Uvicorn runs with `--workers 4` and `--proxy-headers` for reverse proxy deployments.

**Frontend image:**
- The nginx-based production image serves pre-built static assets with no runtime dependencies on Node.js.
- The `VITE_API_URL` build arg should point to the production API endpoint if nginx is not used as the reverse proxy (e.g., when behind a CDN or load balancer).
- In production, the custom `nginx.conf` may be replaced with one that includes TLS termination, rate limiting, and security headers.

**Celery container:**
- Runs the same `saas_backend` image with the celery entrypoint. Scales horizontally by running multiple Celery worker replicas behind the same Redis broker.

**Mailpit:**
- Excluded from production deployments entirely. It is a development-only tool.

**Shared volumes (`logs_data`, `uploads_data`):**
- In production, these should be replaced with centralized logging (e.g., stdout/journald aggregation) and object storage (e.g., AWS S3 via the `AWS_*` environment variables) respectively.

---

## Troubleshooting

### Container fails to start — "Set POSTGRES_PASSWORD in .env"

The `.env` file is missing or does not contain `POSTGRES_PASSWORD`. Create a `.env` from `.env.example` and set a strong password:

```bash
cp .env.example .env
# Edit .env and set POSTGRES_PASSWORD
```

### Backend exits with "PostgreSQL not ready after 30s"

PostgreSQL health check is passing but the application-level socket check in `entrypoint.sh` cannot connect. Verify:
- `POSTGRES_SERVER` in `.env` is set to `postgres` (the Docker service name, not `localhost`).
- The postgres container is healthy: `docker compose ps`

### Frontend shows "Cannot connect to API" or blank page

- Verify the backend container is running: `docker compose ps`.
- The nginx config proxies `/api/` to `http://backend:8000`. Ensure the backend service name is `backend` in your compose file.
- If `VITE_API_URL` was set to a non-empty value during build, rebuild the frontend: `docker compose build frontend`.

### Celery tasks not executing

- Check Celery health: `docker compose logs celery`.
- Verify Redis is running: `docker compose exec redis redis-cli ping` (should return `PONG`).
- Inspect registered tasks: `docker compose exec celery celery -A app.workers.tasks.celery_app inspect registered`.

### Port conflicts

If ports 80, 8000, 5432, 6379, 1025, or 8025 are already in use, either stop the conflicting service or remap ports in `docker-compose.yml`:

```yaml
ports:
  - "8080:80"   # Map host 8080 → container 80
```

### Volumes not persisting after `docker compose down`

By default, named volumes are preserved. If data is lost, check that you did not run `docker compose down -v` (which removes volumes). Rebuild is safe: `docker compose up -d --build`.

### Permission errors on logs or downloads

The backend runs as `appuser` (UID 1000). If host-mounted volumes have incorrect ownership:

```bash
docker compose exec backend chown -R appuser:appuser /app/logs /app/downloads
```

With named Docker volumes this is rarely an issue, as the volume is created and owned by the container.
