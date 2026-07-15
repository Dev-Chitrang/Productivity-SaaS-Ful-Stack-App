# Productivity Suite

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.2-DC382D?logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.x-378AFF?logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Tests](https://img.shields.io/badge/Tests-2100+-blue)
![CI](https://github.com/Dev-Chitrang/Productivity-SaaS-Ful-Stack-App/actions/workflows/ci.yml/badge.svg?branch=main)

A modular, full-stack productivity application that combines task management, note-taking, calendar scheduling, audio meetings with WebRTC, collaborative whiteboarding, AI-powered meeting analysis, and cross-entity relations into a single self-hosted platform. Built with a React frontend and a Python FastAPI backend, designed for individuals and small teams who want to replace scattered SaaS tools.

---

## Highlights

- **Repository → Service → Controller** layered architecture with dependency injection
- **Redis-backed Meeting Engine** with session-scoped lifecycle and WebSocket signaling
- **AI-powered Meeting Analysis** via NVIDIA NIM (Llama 3.3 70B) with actionable task suggestions
- **Generic Attachments** infrastructure (local filesystem or AWS S3)
- **Generic Entity Relations** linking tasks, meetings, and sessions
- **Provider Architecture** for storage (local / S3) and email (SMTP / Brevo)
- **Production-ready Docker** with 6-service orchestration, health checks, and persistent volumes
- **Environment Agnostic** configuration (LOCAL / TESTING / PRODUCTION)

---

## Design Principles

- **Modular Architecture** — Each feature is a self-contained module with its own routes, controllers, services, and repositories
- **Separation of Concerns** — Business logic in services, database access in repositories, HTTP handling in controllers
- **Dependency Injection** — All components wired via FastAPI's `Depends` system for testability and decoupling
- **Provider Abstractions** — Storage and email providers are swappable behind abstract interfaces
- **Async-first Design** — Full async/await throughout the backend (SQLAlchemy, Redis, HTTP)
- **Production-ready** — Rate limiting, health checks, structured logging, non-root Docker containers
- **Self-hostable** — No external services required for local development; optional cloud integrations for production

---

## Key Features

### Authentication

- Email/password registration with OTP-based email verification and two-factor auth
- Google OAuth sign-in and account linking
- JWT access/refresh token rotation with Redis-backed whitelist for revocation
- Password reset flow via email
- Sliding-window rate limiting on auth endpoints

### Dashboard

- Analytics widgets for calendar events, notes, and tasks
- Today's agenda and upcoming meetings widgets
- Recent activity feeds for notes, tasks, whiteboards, AI analyses, and attachments

### Calendar

- Four view modes: month, week, day, and agenda
- Event CRUD with recurring events (daily, weekly, monthly)
- Event type categorization (PERSONAL, MEETING, REMINDER) and color coding
- Search and filter by type or color; view state persisted in URL parameters

### Meetings

- Audio-only WebRTC meetings with real-time WebSocket signaling
- Lifecycle: CREATED → ACTIVE → IDLE → ENDED / CANCELLED with reusable rooms
- Instant and scheduled meeting types with timezone and agenda support
- Waiting room with host admission workflow
- Host controls: admit, reject, remove, mute/unmute; end or cancel meetings
- Screen sharing with host approval, rejection, and force-stop
- Guest access via shareable links (no account required)
- Meeting invitations for registered and email-based invitees
- Session history with duration and participant counts
- Recording and transcript upload/download (per session)
- AI transcript analysis via NVIDIA NIM: summary, agenda coverage, and suggested tasks
- Completion emails with recordings, transcripts, and AI analysis attached

### Tasks

- Rich text descriptions via Tiptap with status workflow (TODO → IN PROGRESS → DONE)
- Priority levels, due dates with date-range filtering, labels, and checklists
- Pin, favorite, archive, and soft delete with restore
- Activity timeline tracking all field changes
- Cross-entity linked meetings panel

### Notes

- Rich text editing via Tiptap with categories, tags, pin, and favorite
- Search, filter, archive, and soft delete with restore

### Whiteboards

- Canvas-based drawing with pen, shapes (rectangle, circle, line, arrow), and text tools
- Color picker, adjustable stroke width, undo/redo, and zoom controls
- Export as PNG (2x), autosave with 1-second debounce
- Board management: rename, favorite, archive, soft delete, restore

### Attachments

- Generic file attachment infrastructure for tasks, calendar events, meeting sessions, and notes
- Multipart upload with MIME validation or presigned S3 direct-to-cloud flow
- Download via presigned URL (S3) or local file streaming

### Relations

- Cross-entity linking between meetings, meeting sessions, and tasks
- Origin tracking (USER, SYSTEM, AI) with linked-entity panels on detail pages

### AI Analysis

- Meeting transcript analysis via NVIDIA NIM (Llama 3.3 70B)
- Executive summary, agenda coverage, covered/out-of-agenda points, and suggested tasks
- Suggested tasks can be accepted (created as real tasks) or rejected

### Notifications

- In-app notification center with pagination, search, and type filtering
- Web Push notifications via VAPID with service worker support
- Push subscription management with browser detection

### Security

- JWT with HS256 (15-min access, 7-day refresh) and Redis-backed revocation
- Sliding-window rate limiting, bcrypt hashing, OTP-based 2FA
- File upload validation (size, extension, MIME), CORS, non-root Docker execution

### Provider Architecture

- Abstract `StorageProvider` with Local (aiofiles) and S3 (aioboto3) backends
- Environment-driven provider selection with presigned URL support

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, Vite 8, react-router-dom 7, TanStack React Query 5, Axios, react-hook-form + zod, Tailwind CSS 4, shadcn/ui (Radix), Tiptap 3, Konva, Recharts, Framer Motion, dayjs |
| **Backend** | Python 3.10+, FastAPI, Uvicorn (4 workers), SQLAlchemy (async), Pydantic v2, PyJWT (HS256), pwdlib (bcrypt), Celery (Redis broker), OpenAI SDK (NVIDIA NIM), pywebpush (VAPID) |
| **Database** | PostgreSQL 16 (asyncpg), Alembic (async), Redis 7.2 |
| **Storage** | Local filesystem (aiofiles) or AWS S3 (aioboto3, presigned URLs) |
| **Email** | Brevo API (production) / Mailpit (development) |
| **OAuth** | Google OpenID Connect (server-side token verification) |
| **Docker** | 6-service Compose stack: Frontend (nginx), Backend, Celery, PostgreSQL, Redis, Mailpit |

---

## Project Structure

```
productivity-app/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, database, security, Redis, storage, WebSocket, middleware, rate limiter
│   │   ├── models/         # SQLAlchemy ORM models (12 tables)
│   │   ├── modules/        # 12 feature modules: auth, users, calender, notes, tasks, meetings,
│   │   │                   #   whiteboard, attachments, entity_links, ai_suggestions, notifications, reminders
│   │   ├── workers/        # Celery async tasks
│   │   ├── templates/      # Jinja2 email templates
│   │   └── utils/          # Utility functions
│   ├── alembic/            # Database migrations
│   ├── tests/              # ~100 test files, 2100+ test cases
│   └── Dockerfile          # Multi-stage Python build
│
├── frontend/
│   ├── src/
│   │   ├── features/       # 11 feature modules (auth, dashboard, calendar, notes, tasks,
│   │   │                   #   meetings, whiteboards, notifications, entityLinks, profile, settings)
│   │   ├── components/     # Shared UI (shadcn/ui primitives)
│   │   ├── context/        # Auth, Theme, Sidebar providers
│   │   ├── layouts/        # MainLayout, AuthLayout, Header, Sidebar
│   │   ├── shared/         # Shared rich text editor (Tiptap)
│   │   ├── lib/            # Axios, React Query client, utilities
│   │   ├── routes/         # AppRoutes with ProtectedRoute
│   │   └── pages/          # Landing page
│   └── Dockerfile          # Multi-stage Node + nginx build
│
├── docker-compose.yml      # Full stack orchestration (6 services)
├── .env.example            # Environment variable reference
├── ARCHITECTURE.md         # Detailed architecture documentation
├── CHANGELOG.md            # Version history
└── LICENSE                 # MIT License
```

Each backend module follows a consistent layered pattern: `routes → controller → service → repository`, with Pydantic schemas, dependency injection, enums, exceptions, and constants. Each frontend feature module contains pages, components, hooks, API functions, schemas, and utilities. See [ARCHITECTURE.md](ARCHITECTURE.md) for a complete breakdown.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended)

### Clone Repository

```bash
git clone <repository-url>
cd productivity-app
```

### Environment Configuration

1. Copy the example environment files and fill in your values:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

2. See `.env.example` for the full variable reference (database, JWT secrets, Redis, SMTP, Google OAuth, NVIDIA NIM, VAPID, and optional AWS S3).

### Docker (Recommended)

Start the entire stack with a single command:

```bash
docker compose up -d
```

This starts all 6 services (Frontend, Backend, Celery, PostgreSQL, Redis, Mailpit). The backend entrypoint automatically waits for PostgreSQL and runs migrations. The frontend is served at `http://localhost` with API and WebSocket proxying to the backend.

### Manual Development

Start infrastructure services, then the backend and frontend separately:

```bash
# Infrastructure (Redis + Mailpit)
cd backend
docker-compose up -d

# Database migration
alembic upgrade head

# Backend
uvicorn app.main:app --reload --port 8000

# Celery worker (email tasks, AI analysis)
celery -A app.workers.tasks.celery_app worker --loglevel=info

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

### Testing

```bash
cd backend
pytest
```

The backend has 100+ test files with 2100+ test cases covering services, controllers, routes, models, and workers. See the [Testing](#testing) section for details.

---

## Docker

The root `docker-compose.yml` orchestrates the full stack with 6 services, health checks, and persistent volumes.

| Service | Port | Description |
|---|---|---|
| Frontend | 80 | React SPA served by nginx |
| Backend | 8000 | FastAPI + Uvicorn |
| Celery | -- | Worker + Beat (shared backend image) |
| PostgreSQL | 5432 | Primary data store |
| Redis | 6379 | Cache, sessions, Celery broker |
| Mailpit | 1025 / 8025 | Dev SMTP catcher / Web UI |

The frontend nginx reverse-proxies `/api/` and `/ws/` to the backend. The backend entrypoint waits for PostgreSQL, runs Alembic migrations, then starts Uvicorn. See the [backend Dockerfile](backend/Dockerfile) and [frontend Dockerfile](frontend/Dockerfile) for multi-stage build details.

---

## Testing

The backend has 100+ test files with 2100+ test cases, organized to mirror the application structure. Tests use `pytest-asyncio` in auto mode, `unittest.mock` for isolation, and FastAPI's `TestClient` with dependency overrides for route-level testing.

```bash
cd backend
pytest
```

**Patterns:** service tests (mock repository, test business logic), controller tests (verify HTTP status translation), route tests (TestClient with dependency overrides), model tests (field defaults, constraints), and worker tests (mocked async loops and providers).

---

## Documentation

| Document | Description |
|---|---|
| [README.md](README.md) | Project overview, features, setup, and usage |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Detailed architecture, module breakdown, request lifecycle, coding guidelines |
| [API.md](API.md) | Details regarding the APIs |
| [CHANGELOG.md](CHANGELOG.md) | Version history and release notes |
| [LICENSE](LICENSE) | MIT License |

---

## Screenshots

| | |
|---|---|
| ![](images/Screenshot%202026-07-06%20183347.png) | ![](images/Screenshot%202026-07-12%20173815.png) |
| ![](images/Screenshot%202026-07-12%20173834.png) | ![](images/Screenshot%202026-07-12%20173851.png) |
| ![](images/Screenshot%202026-07-12%20175542.png) | ![](images/Screenshot%202026-07-12%20175749.png) |
| ![](images/Screenshot%202026-07-12%20175804.png) | ![](images/Screenshot%202026-07-12%20175819.png) |
| ![](images/Screenshot%202026-07-12%20175830.png) | ![](images/Screenshot%202026-07-12%20175845.png) |

---

## Current Status

| Aspect | Status |
|---|---|
| **Current Version** | 1.6.1 |
| **Development Status** | Active development |
| **Backend Tests** | 2100+ test cases across 100+ test files |
| **Docker Support** | Full 6-service stack with health checks and persistent volumes |
| **License** | MIT |

---

## License

MIT License. Copyright (c) 2026 Chitrang Potdar. See [LICENSE](LICENSE) for details.
