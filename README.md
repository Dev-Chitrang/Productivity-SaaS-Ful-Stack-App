# Unified Workspace

A modular productivity suite that combines task management, note-taking, calendar scheduling, audio meetings with WebRTC, and collaborative whiteboarding into a single application. Designed for individuals and small teams who need a self-hosted alternative to scattered productivity tools.

## Features

### Authentication
- Email/password registration with email verification (OTP)
- Login with optional two-factor authentication (OTP-based)
- Google OAuth sign-in and account linking
- JWT access/refresh token rotation with Redis-backed whitelist
- Password reset flow

### Dashboard
- Central landing page after authentication

### Calendar
- Month, week, day, and agenda views
- Event creation, editing, deletion
- Recurring events (daily, weekly, monthly)
- Event type and color categorization
- Search and filter events by type or color

### Notes
- Rich text editing via Tiptap (ProseMirror-based)
- Create, edit, delete, archive, restore notes
- Pin and favorite notes
- Categorization with tags and categories
- Search and filter notes
- Soft delete with restore

### Tasks
- Rich text task descriptions via Tiptap
- Status tracking: TODO, IN PROGRESS, DONE
- Priority levels: LOW, MEDIUM, HIGH
- Due dates with indexing
- Labels and checklists (with `{id, text, completed}` items)
- Pin, favorite, archive, and soft delete
- Task history/activity timeline tracking all field changes

### Meetings
- Audio-only WebRTC meetings with real-time signaling
- Guest access via shareable meeting links
- Waiting room with host admission workflow
- Host controls: admit, reject, remove, mute/unmute participants
- Self-mute/unmute
- Screen sharing with host approval workflow
- Meeting recording upload and download
- Transcript upload and download
- Meeting lifecycle: created, active, idle, ended, cancelled
- Reusable meeting rooms (reactivates after idle/ended)
- WebSocket-based real-time signaling for WebRTC

### Whiteboards
- Drawing with pen tool (freehand)
- Shape tools: rectangle, circle, line, arrow
- Text tool
- Color picker with preset palette and custom color
- Adjustable stroke width
- Undo/redo with full history
- Zoom in/out/reset
- Export board as PNG
- Autosave with debounce (1-second delay)
- Board management: rename, favorite, archive, soft delete, restore
- Resizable sidebar with board list and search

### User Profile
- View and update profile (name, timezone)
- Change password and email
- Toggle two-factor authentication
- Profile image URL
- Account deactivation

## Tech Stack

### Frontend
- **Framework:** React 19
- **Build Tool:** Vite 8
- **Routing:** react-router-dom 7
- **Server State:** TanStack React Query 5
- **HTTP Client:** Axios
- **Forms:** react-hook-form with zod
- **CSS:** Tailwind CSS 4
- **UI Components:** shadcn/ui (Radix UI primitives)
- **Icons:** Lucide, Phosphor
- **Rich Text:** Tiptap 3 (ProseMirror-based)
- **Canvas:** Konva + react-konva
- **Animation:** Framer Motion
- **Notifications:** react-hot-toast
- **Date/Time:** dayjs

### Backend
- **Language:** Python 3.10+
- **Framework:** FastAPI
- **ASGI Server:** Uvicorn
- **ORM:** SQLAlchemy (async)
- **Validation:** Pydantic v2
- **Auth:** PyJWT (HS256), bcrypt via pwdlib
- **Task Queue:** Celery (Redis broker)
- **OAuth:** google-auth (server-side token verification)
- **File Storage:** Local filesystem via aiofiles

### Database
- **Primary:** PostgreSQL with asyncpg driver
- **Migrations:** Alembic (async)
- **Cache/Session:** Redis

### Real-time
- **WebSocket:** FastAPI native WebSocket with room-based connection manager

### Developer Tools
- **Linting:** ESLint (frontend)
- **Containerization:** Docker Compose (Redis, Mailpit)

## Project Architecture

### Frontend

React single-page application using Vite for development and production builds. Routes are protected by an authentication wrapper that checks for a valid JWT in local storage. Guest users can join meetings via shareable links without authentication. The application uses TanStack React Query for server state management with automatic caching and refetching. Axios is configured with an interceptor that attaches the JWT access token to every request and attempts automatic token refresh on 401 responses.

### Backend

FastAPI application following a layered architecture: routes receive HTTP requests and delegate to controllers, which orchestrate business logic through services, which interact with the database via repositories. Each module (auth, users, calendar, notes, tasks, meetings, whiteboards) is self-contained with its own routes, schemas, service, repository, controller, and dependencies. Cross-cutting concerns like authentication, database sessions, and logging are handled by dependency injection.

### Database

PostgreSQL is the primary data store accessed through SQLAlchemy's async session interface. Alembic manages schema migrations. Redis serves as a session cache for JWT refresh token whitelists, OTP storage, and the Celery message broker.

### API Flow

Clients interact with REST endpoints under `/api/v1` for CRUD operations. Authentication endpoints handle signup, login, OAuth, token refresh, and password reset. WebSocket connections at `/ws/meetings/{meeting_id}` handle real-time signaling for meetings.

### Real-time Communication

The WebSocket manager maintains a room-based connection registry. Each meeting room maps connection IDs to WebSocket instances. Messages are broadcast to all participants in a room or sent to individual connections. The signaling protocol relays WebRTC offers, answers, and ICE candidates between peers.

### Module Communication

Modules are isolated and do not directly depend on each other. The whiteboard and meetings modules share the authentication dependency from the users module. Calendar events reference meetings by ID but are otherwise independent.

## Folder Structure

```
backend/                  # Python FastAPI backend
  app/
    core/                 # Config, database, security, middleware, redis, storage, websocket manager, logger
    models/               # SQLAlchemy ORM models
    modules/              # Feature modules (auth, users, calendar, notes, tasks, meetings, whiteboard)
    workers/              # Celery async task workers
    utils/                # Utility functions
  migrations/             # Alembic migration scripts

frontend/                 # React + Vite frontend
  src/
    components/           # Shared UI components (shadcn/ui)
    context/              # Auth, Theme, Sidebar context providers
    features/             # Feature modules (auth, dashboard, calendar, notes, tasks, meetings, whiteboards, profile, settings)
    hooks/                # Shared hooks
    layouts/              # Main layout, auth layout, sidebar, header
    lib/                  # Axios instance, query client, utility functions
    pages/                # Top-level page components (landing)
    routes/               # Application route definitions
    shared/               # Shared rich text editor (Tiptap)
```

See `ARCHITECTURE.md` for a complete breakdown of every file and module.

## Installation

### Prerequisites
- Python 3.10+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### Clone

```bash
git clone <repository-url>
cd productivity-app
```

### Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Database Migration

```bash
cd backend
alembic upgrade head
```

### Environment Variables

Copy the example environment files and update values:

```bash
cp backend/.env backend/.env      # Edit with your values
cp frontend/.env frontend/.env     # Edit with your values
```

### Run Backend

```bash
cd backend
uvicorn run:app --reload
# Or using the run script
python run.py
```

Celery worker (for email tasks):

```bash
celery -A app.workers.tasks.celery_app worker --loglevel=info
```

### Run Frontend

```bash
cd frontend
npm run dev
```

### Infrastructure (Optional)

```bash
docker-compose up -d
```

Starts Redis (port 6379) and Mailpit (SMTP port 1025, web UI port 8025).

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `ENVIRONMENT` | Runtime environment: development, testing, or production |
| `POSTGRES_SERVER` | PostgreSQL host address |
| `POSTGRES_PORT` | PostgreSQL port (default 5432) |
| `POSTGRES_USER` | PostgreSQL user |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_DB` | PostgreSQL database name |
| `JWT_SECRET_KEY` | Secret key for signing access tokens |
| `JWT_REFRESH_SECRET_KEY` | Secret key for signing refresh tokens |
| `REDIS_HOST` | Redis host address |
| `REDIS_PORT` | Redis port (default 6379) |
| `REDIS_CELERY_BROKER_URL` | Redis URL for Celery broker (e.g., redis://localhost:6379/0) |
| `SMTP_HOST` | SMTP server host |
| `SMTP_PORT` | SMTP server port (1025 for Mailpit) |
| `SMTP_USE_TLS` | Enable TLS for SMTP (True/False) |
| `SMTP_USER` | SMTP username (leave empty if not required) |
| `SMTP_PASSWORD` | SMTP password (leave empty if not required) |
| `SMTP_FROM_EMAIL` | From address for outgoing emails |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `STORAGE_BASE_DIR` | Base directory for file storage (recordings, transcripts) |
| `MEETING_SESSION_TOKEN_EXPIRE_MINUTES` | Meeting session token expiry in minutes (default 60) |

### Frontend (`frontend/.env`)

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend API base URL (e.g., http://localhost:8000) |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth client ID (must match backend) |

## Available Modules

### Authentication

Handles user registration, login, OAuth, email verification, two-factor authentication, password reset, and token refresh. Supports both email/password and Google OAuth. OTPs are stored in Redis with configurable TTLs and sent via Celery async email tasks.

### Dashboard

A landing page displayed after authentication. Serves as the central hub for navigating to other modules.

### Calendar

Full-featured calendar with month, week, day, and agenda views. Supports event CRUD, recurrence (daily, weekly, monthly), event type and color categorization, and search/filter. View state is persisted in URL search parameters.

### Notes

Rich text notes editor using Tiptap (ProseMirror-based). Supports categories, tags, pinning, favoriting, archiving, and soft delete with restore. Notes are searchable and filterable.

### Tasks

Task management with rich text descriptions, status workflow (TODO, IN PROGRESS, DONE), priority levels, due dates, labels, and checklists. Supports pinning, favoriting, archiving, and soft delete. All field changes are tracked in a task history timeline.

### Meetings

See the Meetings Module section below.

### Whiteboards

See the Whiteboard Module section below.

### Profile

User profile management: view and update name, timezone, profile image URL. Change password, change email, toggle 2FA, deactivate account.

## Meetings Module

Audio-only meeting rooms built on WebRTC with a FastAPI WebSocket signaling server.

Key capabilities:
- **Waiting Room:** Participants join a waiting state and must be admitted by the host
- **Audio:** WebRTC audio streaming between participants
- **Recording:** Upload and download meeting recording files
- **Transcript:** Upload and download meeting transcript files
- **Screen Sharing:** Participants can request screen share permission; host can approve, reject, or force-stop
- **Host Controls:** Admit, reject, remove, mute/unmute participants; end or cancel meetings
- **Reusable Meeting Links:** Meetings return to an active state when rejoined after idle/ended
- **Guest Access:** Unauthenticated users can join via meeting code with a guest name and email

## Whiteboard Module

Canvas-based whiteboard built on Konva (react-konva).

Key capabilities:
- **Drawing:** Freehand pen tool with adjustable stroke width and color
- **Text:** Add text elements to the canvas
- **Shapes:** Rectangle, circle, line, and arrow tools
- **Autosave:** Board data is automatically saved to the server with a 1-second debounce
- **Export PNG:** Export the current canvas as a PNG image with 2x pixel ratio
- **Board Organization:** Boards can be renamed, favorited, archived, soft-deleted, and restored; boards are searchable and filterable by status

## API

### Organization

All REST endpoints are prefixed with `/api/v1`. Each module has its own prefix:

| Module | Prefix |
|---|---|
| Authentication | `/api/v1/auth` |
| Users | `/api/v1/users` |
| Calendar | `/api/v1/calendar` |
| Notes | `/api/v1/notes` |
| Tasks | `/api/v1/tasks` |
| Meetings | `/api/v1/meetings` |
| Whiteboards | `/api/v1/whiteboards` |

WebSocket endpoints:
| Module | Path |
|---|---|
| Meetings Signaling | `/ws/meetings/{meeting_id}` |

Authentication is handled via HTTP Bearer token for most endpoints. Meeting endpoints use a dependency that extracts the user ID from the JWT and optionally allows unauthenticated access for guest flows.

A health check endpoint is available at `/health`.

## Database

### Overview

PostgreSQL stores all persistent data. The schema uses UUIDv7 primary keys, timestamps with timezone on all tables, and soft delete via `deleted_at` columns.

### Key Entities

- **User:** Core identity with email, password hash, OAuth provider linking, 2FA status, and profile fields.
- **Task:** User-owned tasks with rich text description (JSONB), status, priority, due date, labels (JSONB string array), and checklist (JSONB array of `{id, text, completed}`). Supports soft delete and maintains a `TaskHistory` table tracking all field changes.
- **Note:** User-owned notes with rich text content (JSONB), category, and tags (JSONB string array). Supports soft delete.
- **CalendarEvent:** Events with start/end times, timezone, event type, color, location, and recurrence configuration (frequency, interval, end date). Supports soft delete.
- **Meeting:** Meeting rooms with a unique 10-character meeting code, host assignment, status lifecycle, and screen sharing state.
- **MeetingParticipant:** Tracks registered and guest participants with waiting/admitted/left/removed/rejected status, mute state, and screen share permissions.
- **MeetingRecording / MeetingTranscript:** File metadata for uploaded recordings and transcripts linked to meetings.
- **Whiteboard:** User-owned boards with canvas state stored as JSONB (`{version, elements}`). Supports soft delete.

## Development

### How to Contribute

1. Fork the repository
2. Create a feature branch from `main`
3. Make changes following the coding standards below
4. Run linting and verify the application starts correctly
5. Submit a pull request

### Coding Standards

- **Python:** Follow PEP 8. Use type hints for all function signatures. Async/await throughout the backend.
- **JavaScript/React:** Use functional components with hooks. Prefer named exports. Use JSX for UI.
- **CSS:** Use Tailwind CSS utility classes. Avoid custom CSS unless necessary.
- **API Design:** RESTful endpoints with consistent naming. Use Pydantic schemas for request/response validation.
- **Database:** All models use UUID primary keys and timestamps. Use Alembic for schema changes.

### Architecture Principles

- Modules are self-contained with their own routes, schemas, services, repositories, and controllers
- Business logic lives in services, not controllers or routes
- Database access lives in repositories, not services
- Dependencies are injected via FastAPI's `Depends` system
- Cross-cutting concerns (auth, logging, CORS) are handled at the framework level

## Roadmap

### Current Version (V1)

- Email/password authentication with email verification
- Google OAuth sign-in
- Two-factor authentication
- Calendar with month, week, day, and agenda views
- Rich text notes with categories and tags
- Task management with status, priority, due dates, checklists, and history
- Audio-only WebRTC meetings with waiting room and host controls
- Screen sharing with host approval
- Meeting recording and transcript file management
- Canvas-based whiteboard with drawing, shapes, text, and export
- Autosave on whiteboards
- Guest access for meetings
- Reusable meeting rooms
- User profile and settings

### Upcoming Version (V2)

- **Redis:** Full integration for caching, rate limiting, and session management across all modules
- **Module Relationships:** Calendar events linking to meetings, tasks linked to notes, whiteboard embeds in meetings
- **Collaboration:** Real-time collaborative editing on notes and whiteboards
- Push notifications for meetings and task due dates
- File attachments on tasks and notes
- Meeting recording playback in the browser
- Dark mode refinements
- Mobile-responsive optimizations
- Docker Compose for full stack (backend, frontend, database)

## License

MIT License. See `LICENSE` for details.
