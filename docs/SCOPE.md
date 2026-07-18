# Product Scope

This document defines the scope of the Productivity Suite application. It is not architecture. It is not a changelog. It is not a roadmap. It answers one question: **What does the application currently support?**

The application is versioned across two release branches:
- **`release/v1` (Scope 1):** Core productivity features.
- **`release/v2` (Scope 2):** V1 plus advanced collaboration, AI, and infrastructure features.

Each section below is tagged with the version(s) that include it.

---

## Product Vision

A modular, full-stack productivity application that combines task management, note-taking, calendar scheduling, audio meetings with WebRTC, collaborative whiteboarding, AI-powered meeting analysis, and cross-entity relations into a single self-hosted platform. Built with a React frontend and a Python FastAPI backend, designed for individuals and small teams who want to replace scattered SaaS tools.

---

## Functional Scope

### Authentication

**Purpose:** User identity, session management, and access control.

**Capabilities:**
- Email/password registration with 6-digit OTP email verification
- User login with email and password
- Google Identity Services (GIS) sign-in with server-side token verification
- Two-factor authentication via login OTP
- JWT-based session management with access tokens (15-minute expiry) and refresh tokens (7-day expiry)
- Token refresh with Redis-backed session whitelist for server-side revocation
- Password reset flow via email (initiate + OTP confirmation)
- Resend OTP endpoints for both signup and login flows
- Sliding-window rate limiting on all auth endpoints (3 requests per 60 seconds)

**Versions:** `release/v1` (core auth), `release/v2` (+ Google Identity Services, 2FA, rate limiting)

**Current Limitations:**
- Only Google Identity Services is supported as an external identity provider
- No social login providers beyond Google
- No account deletion (only soft deactivation via `is_active` flag)
- No email change without current password verification
- OTPs are stored in Redis with a fixed 10-minute TTL, not configurable

---

### Dashboard

**Purpose:** Central landing page after authentication, providing an at-a-glance overview of all modules.

**Capabilities:**
- Welcome section with user greeting
- Overview cards showing aggregate counts for calendar events, notes, and tasks
- Today's agenda widget showing upcoming events and pending tasks for the current day
- Upcoming meetings widget listing the next scheduled meetings
- Recent tasks, notes, and whiteboards activity feeds
- Recent attachments widget
- Recent AI analyses widget showing completed meeting analyses
- Recent notifications widget
- Calendar analytics chart (Recharts)
- Notes analytics chart (Recharts)
- Tasks analytics chart (Recharts)

**Versions:** `release/v1` (basic dashboard), `release/v2` (enhanced with attachments, AI analyses, notifications widgets)

**Current Limitations:**
- No dedicated dashboard API endpoint; composed from multiple module-specific queries
- No real-time updates on the dashboard
- No customizable widget layout or drag-and-drop dashboard configuration

---

### Meetings

**Purpose:** Audio-only meetings with real-time communication, participant management, and session tracking.

**Capabilities:**
- Instant meeting creation and scheduled meeting creation
- Meeting lifecycle management: CREATED → ACTIVE → IDLE → ENDED / CANCELLED
- Audio-only communication via WebRTC mesh networking (peer-to-peer)
- WebSocket signaling for WebRTC offer/answer/ICE candidate relay
- Waiting room with host admission, rejection, and removal controls
- Host controls: admit, reject, remove, mute/unmute participants, end or cancel meeting
- Screen sharing with host approval, rejection, and force-stop
- Guest access via shareable meeting links (no account required, name and email required)
- Meeting invitations for registered users and email-based invitees
- Meeting join via shareable link or meeting code
- Meeting detail pages with metadata, participants, and session history
- Reusable meeting rooms that can be reactivated after ending
- Meeting recording upload, download, and deletion
- Meeting transcript upload, download, and deletion
- Session history with chronological session tracking per meeting
- Session detail pages for individual session recordings, transcripts, and analysis
- Session-level attachment uploads
- Session-level linked tasks (from AI suggestions)
- Meeting-level linked tasks (from entity links)
- Meeting list with search and status filtering

**Versions:** `release/v1` (instant meetings, audio, waiting room, screen share, recordings/transcripts), `release/v2` (+ scheduled meetings, invitations, session history, session-level artifacts)

**Current Limitations:**
- Audio-only; no video support
- No in-meeting text chat (chat component exists but is not fully integrated)
- WebRTC signaling only; no SFU or MCU server for large-scale meetings
- STUN-only for NAT traversal; no TURN server support configured
- Recordings and transcripts are uploaded after the fact, not captured in real-time by the server
- Guest participants cannot upload recordings or transcripts
- No meeting password or passcode protection
- No meeting time limits or auto-end functionality
- No recurring meeting scheduling

---

### Meeting Sessions

**Purpose:** Track individual sessions within a meeting, each with its own recordings, transcripts, participants, and AI analysis.

**Capabilities:**
- Session creation when a participant joins a meeting
- Session tracking with start time, end time, and participant counts
- Per-session recording upload, listing, and download
- Per-session transcript upload, listing, and download
- Per-session AI analysis with status tracking (PENDING → PROCESSING → COMPLETED / FAILED)
- Per-session attachment uploads
- Per-session linked tasks
- Session detail page with all session-specific data

**Versions:** `release/v2` only

**Current Limitations:**
- Session state is stored in Redis for low latency, but not persisted to the database as a full record
- No session-level chat history
- No session-level screen recording capture
- Sessions are automatically ended when all participants leave

---

### Tasks

**Purpose:** Task management with status workflow, priorities, due dates, and change tracking.

**Capabilities:**
- Task creation, editing, and deletion
- Rich text descriptions via TipTap editor
- Task status workflow: TODO → IN PROGRESS → DONE
- Priority levels: LOW, MEDIUM, HIGH
- Due date assignment and date-range filtering
- Label management for task categorization
- Interactive checklists within tasks
- Pin and favorite for quick access
- Archive and soft delete with restore capability
- Full-text search on title and description
- Activity timeline tracking all field changes (TaskHistory audit trail)
- Task analytics widget
- Linked meetings panel showing associated meetings (via entity links)
- Attachment uploads (documents, images, audio, video, archives)

**Versions:** `release/v1` (core task CRUD, checklists, labels, search), `release/v2` (+ attachments, linked meetings)

**Current Limitations:**
- No task assignee or multi-user task assignment
- No task dependencies or blocking relationships
- No recurring task generation
- No task time tracking or time estimation
- No task priority auto-sorting
- No drag-and-drop task reordering in the list
- Checklists are flat (no nested sub-tasks)
- Rich text content stored as JSONB; no collaborative editing

---

### Calendar

**Purpose:** Calendar event scheduling with multiple view modes and recurrence support.

**Capabilities:**
- Four view modes: month grid, week grid, day timeline, and agenda list
- Event CRUD with form validation
- Event types: PERSONAL, MEETING, REMINDER
- 7 color-coded event categories
- Recurring events with daily, weekly, and monthly frequency
- Recurrence interval control and end date configuration
- Recurrence engine that expands recurring events into individual occurrences within a date range
- Search and filter by event type and color
- URL-persisted view state and anchor date for browser navigation
- Calendar analytics widget
- Timezone-aware scheduling
- Attachment uploads for calendar events
- Merges calendar events with task due dates into unified timeline view

**Versions:** `release/v1` (core calendar, views, recurrence), `release/v2` (+ attachments)

**Current Limitations:**
- No drag-and-drop event rescheduling
- No calendar sharing between users
- No external calendar integration (Google Calendar, Outlook, iCal)
- No calendar event notifications or alerts in real-time
- No all-day event support
- Recurrence does not support exceptions (e.g., skip a specific date)
- No calendar export/import

---

### Notes

**Purpose:** Rich text note-taking with categorization and tagging.

**Capabilities:**
- Note creation, editing, and deletion
- Rich text editing via TipTap (bold, italic, headings, lists, links, code blocks, tables, task lists, underlines, placeholders)
- Categories and tags for note organization
- Pin and favorite for quick access
- Archive and soft delete with restore capability
- Full-text search on title and content
- Auto-save on editor changes
- Resizable split-pane layout with collapsible list panel
- Notes analytics widget

**Versions:** `release/v1`

**Current Limitations:**
- No real-time collaborative editing
- No note sharing between users
- No note versioning or revision history
- No note templates
- Categories and tags are freeform strings, not predefined enums
- No note export to PDF or other formats
- No note-level attachments (notes are text-only)

---

### Whiteboard

**Purpose:** Digital whiteboard for freehand drawing, shapes, and visual ideation.

**Capabilities:**
- Canvas-based drawing built on Konva/react-konva
- Freehand pen drawing with configurable stroke color and width
- Shape tools: rectangle, circle, line, arrow
- Text tool with customizable font size
- Image placement on the canvas
- Zoom (0.1x to 5x) and pan via scroll
- Element selection via click
- Element deletion via keyboard (Delete/Backspace)
- Client-side undo/redo with Ctrl+Z and Ctrl+Y/Ctrl+Shift+Z
- History management with element snapshot array
- Export to PNG at 2x resolution
- Autosave with 1-second debounce after element changes
- Board management: rename, favorite, archive, soft delete, restore
- Board list with search and filter (all, archived, deleted, favorited)

**Versions:** `release/v1`

**Current Limitations:**
- No real-time collaborative editing or live cursors
- No sharing of whiteboards between users
- Board data stored as a single JSONB blob; no incremental/delta updates
- No version history or board snapshots
- No text wrapping or rich text on canvas
- No layer management
- No snapping or alignment guides
- No board templates
- Limited to a single user per board at a time

---

### Attachments

**Purpose:** Generic file attachment infrastructure for tasks, calendar events, meeting sessions, and notes.

**Capabilities:**
- File upload via multipart form data
- Presigned S3 direct-to-cloud upload flow
- MIME type validation via python-magic
- Extension whitelisting with configurable allowed types
- File size limits (50MB maximum)
- Supported file types: documents (pdf, docx, xlsx, pptx, csv), images (jpg, png, gif, webp, svg), audio (mp3, wav, ogg, m4a), video (mp4, mov, avi, mkv), archives (zip, tar, gz, 7z), code/misc (json, xml, md, yaml)
- Attachment CRUD per entity type (task, calendar event, meeting session, note)
- Download via presigned URL (S3) or local file streaming
- Recent attachments widget on dashboard
- Attachment metadata: filename, content type, size, storage path

**Versions:** `release/v2` only

**Current Limitations:**
- No inline file preview in the UI
- No image thumbnail generation
- No file versioning
- No attachment search across all entity types
- No drag-and-drop upload
- No folder/directory organization within attachments
- 50MB file size limit is fixed, not configurable per entity type

---

### Relations

**Purpose:** Cross-entity linking between meetings, meeting sessions, and tasks.

**Capabilities:**
- Create links between any two entities (meetings, meeting sessions, tasks)
- Polymorphic entity linking via source_type/source_id to target_type/target_id
- Origin tracking: USER (manual), SYSTEM (automatic), AI (suggestion-based)
- Linked Tasks panel on meeting and session detail pages
- Linked Meetings panel on task detail pages
- List and filter links by source or target entity
- Delete entity links

**Versions:** `release/v2` only

**Current Limitations:**
- Only supports linking meetings, meeting sessions, and tasks
- No linking for notes, calendar events, or whiteboards
- No bidirectional link traversal (must query from both source and target)
- No link labels or descriptions
- No bulk link creation
- No link visualization or graph view

---

### AI Analysis

**Purpose:** Automated meeting transcript analysis using LLM to generate insights and actionable task suggestions.

**Capabilities:**
- Meeting transcript analysis via NVIDIA NIM (Llama 3.3 70B Instruct)
- Generates executive summary, agenda coverage percentage, covered points, out-of-agenda points, and suggested tasks
- Transcript preprocessing that normalizes raw dialogue into continuous text
- Async analysis pipeline via Celery background task
- Analysis status tracking (PENDING → PROCESSING → COMPLETED / FAILED)
- Completion email with analysis results, recordings, and transcripts attached
- AI Suggestions module for managing suggested tasks
- Accept suggestion: converts AI-suggested task into a real task entity with entity link
- Reject suggestion: dismisses the suggestion
- Recent analyses widget on dashboard

**Versions:** `release/v2` only

**Current Limitations:**
- Only analyzes meeting transcripts; no analysis for notes, tasks, or other content
- Requires NVIDIA NIM API key and internet connectivity
- No custom analysis prompts or configurable analysis parameters
- No analysis history beyond the most recent per session
- No analysis comparison across sessions
- AI model is fixed (Llama 3.3 70B); no model selection
- No analysis of audio recordings directly (requires transcript first)

---

### Reminders

**Purpose:** Scheduled email and push notifications for upcoming meetings, calendar events, and tasks.

**Capabilities:**
- Email reminders for scheduled meetings, calendar events, and tasks
- Browser push notifications for scheduled meetings starting within 10 minutes
- Per-user reminder preferences (enable/disable per module, frequency, time)
- Global reminder schedule settings
- Celery Beat sweeps every 30 minutes for email reminders
- Celery Beat sweeps every 60 seconds for meeting push reminders

**Versions:** `release/v2` only

**Current Limitations:**
- Email reminders only; no in-app notification delivery for reminders
- No custom reminder times per event/task/meeting
- No SMS or other notification channels
- Reminder logic is batch-sweep based; no event-driven triggers

---

### Notifications

**Purpose:** In-app notification system for meeting reminders and system events.

**Capabilities:**
- In-app notification list with unread indicators
- Browser push notifications via VAPID and Web Push API
- Notification subscription management
- Meeting reminder notifications via push

**Versions:** `release/v2` only

**Current Limitations:**
- No notification preferences or mute controls
- No notification grouping or categorization beyond type
- No email digests for notifications

---

## Non-Functional Scope

### Architecture

- **Backend:** Python FastAPI with async/await throughout, layered architecture (routes → controller → service → repository), dependency injection via FastAPI's `Depends` system
- **Frontend:** React with Vite, feature-based module organization, React Query for server state, context-based local state management
- **Communication:** REST (JSON) for CRUD operations, WebSocket for real-time meeting signaling
- **Database:** PostgreSQL 16 with async SQLAlchemy and Alembic migrations
- **Cache/Broker:** Redis 7.2 for session management, OTP storage, rate limiting, and Celery task queue
- **Task Queue:** Celery with Redis broker for async email delivery, AI analysis, and scheduled reminders

**Versions:** `release/v1` (core architecture), `release/v2` (+ Redis session engine, Celery Beat)

---

### Performance

- Uvicorn runs with dynamic workers in production (computed from CPU cores)
- Async database access via asyncpg connection pool
- Async Redis connections via aioredis
- React Query caches API responses with automatic stale detection and background refetching
- WebSocket connection manager uses room-based isolation for meeting signaling
- Celery handles all long-running operations (email, AI analysis) off the main request thread
- Autosave uses debounce timers to prevent excessive writes

**Versions:** `release/v1` (core performance), `release/v2` (+ Redis session caching)

---

### Security

- JWT tokens signed with HS256 algorithm
- Access tokens expire after 15 minutes; refresh tokens expire after 7 days
- Refresh tokens stored in Redis for server-side revocation
- Bcrypt password hashing via pwdlib
- OTP-based two-factor authentication with Redis-stored codes (10-minute TTL)
- Google Identity Services with server-side ID token verification
- Sliding-window rate limiting per user (identified by JWT) or per IP (for unauthenticated requests)
- File upload validation: extension whitelisting, MIME detection via python-magic, 50MB size limit
- CORS configured to allow all origins
- Meeting access controlled via JWT or guest session
- Host-only privileges for meeting management operations
- WebRTC signaling blocked for muted participants
- Non-root Docker container execution
- Secrets managed via environment variables, never hardcoded

**Versions:** `release/v1` (core security), `release/v2` (+ Google Identity Services, rate limiting, 2FA)

---

### Testing

- 2100+ test cases across 100+ test files
- pytest-asyncio in auto mode for async test support
- unittest.mock for dependency isolation
- FastAPI TestClient with dependency overrides for route-level testing
- Test coverage organized by module layer: routes, controllers, services, repositories, schemas, dependencies, enums, exceptions, constants
- Model unit tests for all database models
- Core infrastructure tests: config, database, email, providers, Redis, security, storage, WebSocket manager
- Worker task tests covering Celery configuration, retry logic, and execution flows
- Utility tests (TipTap converter)

**Versions:** `release/v2` only

---

### Provider Architecture

- **Storage Provider:** Abstract `StorageProvider` base class with two implementations
  - `LocalStorageProvider` — aiofiles-based local filesystem (LOCAL environment)
  - `S3StorageProvider` — aioboto3-based AWS S3 with presigned URLs (PRODUCTION environment)
- **Email Provider:** Abstract `EmailProvider` base class with two implementations
  - `SMTPEmailProvider` — SMTP with Mailpit for local development (LOCAL environment)
  - `BrevoEmailProvider` — Brevo/SendinBlue API for production (PRODUCTION environment)
- **Provider Factory:** `get_storage_provider()` and `get_email_provider()` select implementations based on `ENVIRONMENT` variable
- **Storage Service:** Facade wrapping provider with validation (MIME check, size check, extension check), presigned URL support, and path management

**Versions:** `release/v2` only

---

### Docker

- 6-service Docker Compose stack:
  - **Frontend:** React SPA served by nginx (port 80), reverse-proxies `/api/` and `/ws/` to backend
  - **Backend:** FastAPI + Uvicorn with dynamic workers (port 8000)
  - **Celery:** Worker + Beat sharing the backend image
  - **PostgreSQL:** 16-alpine with persistent named volume
  - **Redis:** 7.2-alpine with AOF persistence and named volume
  - **Mailpit:** SMTP catcher (ports 1025/8025) with persistent named volume
- Multi-stage Dockerfiles for both frontend (Node 22-alpine build → nginx stable-alpine) and backend (Python 3.11-slim + uv → slim runtime)
- Non-root `appuser` in backend container
- Health checks on all 6 services
- 5 named Docker volumes for persistent data
- Backend entrypoint waits for PostgreSQL health check and runs Alembic migrations on startup
- Two Docker networks: `saas_backend_net` (backend, database, Redis, Celery) and `saas_frontend_net` (frontend)

**Versions:** `release/v2` only

---

### Scalability

- Stateless backend (all state in PostgreSQL, Redis, or filesystem)
- Horizontal scaling possible by adding Uvicorn worker instances
- Celery workers can scale independently
- S3 storage provider eliminates local filesystem bottleneck in production
- WebSocket connection manager supports room-based isolation (one room per meeting)
- Database queries indexed on foreign keys and commonly filtered columns

**Versions:** `release/v1` (core scalability), `release/v2` (+ S3, Celery Beat)

---

### Maintainability

- Feature-based module isolation on both frontend and backend
- Consistent layered architecture (routes → controller → service → repository) across all backend modules
- Consistent feature module structure (pages, components, hooks, api, schemas, constants, utils) on frontend
- Repository pattern isolates all database access
- Service layer isolates all business logic
- Dependency injection for testability and decoupling
- Domain-specific exception classes per module
- Pydantic schemas for request/response validation
- SQLAlchemy ORM with Alembic for schema versioning
- Environment-driven configuration via pydantic-settings

**Versions:** `release/v1` (core maintainability), `release/v2` (+ comprehensive test suite)

---

## Supported Platforms

### Browser

- Modern browsers supporting ES2020+, WebRTC, Web Push API, and WebSocket
- Desktop and mobile responsive layout
- Dark and light theme support

**Versions:** `release/v1` (core browser support), `release/v2` (+ Web Push API)

---

### Docker

The application is fully containerized and supports deployment via Docker Compose with 6 services.

**Versions:** `release/v2` only

---

### LOCAL

Development environment configuration:
- Backend runs via Uvicorn with `--reload` on port 8000
- Frontend runs via Vite dev server on port 5173
- Infrastructure via Docker Compose (Redis + Mailpit)
- Database managed via Alembic migrations
- Celery worker and Beat run as separate processes
- Local filesystem for file storage
- Mailpit for email catching (viewable at http://localhost:8025)

**Versions:** `release/v2` only

---

### PRODUCTION

Production environment configuration:
- Full Docker Compose stack with all 6 services
- Backend served by Uvicorn with dynamic workers behind nginx
- Frontend served as static build by nginx
- PostgreSQL with persistent named volume
- Redis with AOF persistence
- S3 storage for file uploads (presigned URL flow)
- Brevo API for transactional email delivery
- VAPID keys for Web Push notifications
- NVIDIA NIM API for AI analysis
- Health checks on all services
- Non-root container execution

**Versions:** `release/v2` only

---

### TESTING

- Backend tests run via pytest with pytest-asyncio
- 2100+ test cases across 100+ test files
- FastAPI TestClient with dependency overrides
- unittest.mock for isolation
- Celery task tests with mocked async loops

**Versions:** `release/v2` only

---

## Version Summary

### release/v1 — Scope 1 (Core Productivity)

| Feature | Description |
|---------|-------------|
| **Authentication** | Email/password signup/login, JWT, password reset, OTP verification |
| **Dashboard** | Basic overview with calendar, notes, tasks, meetings widgets |
| **Calendar** | Month/week/day/agenda views, recurring events, timezone support |
| **Notes** | TipTap rich text editor, categories, tags, search |
| **Tasks** | Status workflow, priorities, due dates, checklists, labels, search |
| **Whiteboard** | Canvas drawing, shapes, undo/redo, export to PNG |
| **Meetings** | Instant meetings, WebRTC audio, waiting room, screen share, recordings/transcripts |

### release/v2 — Scope 2 (Advanced Collaboration & AI)

Everything in Scope 1, plus:

| Feature | Description |
|---------|-------------|
| **Scheduled Meetings** | Calendar-based meeting scheduling with invitations and email invites |
| **Reminders** | Email and push reminders for meetings, events, and tasks |
| **AI Analysis** | NVIDIA NIM transcript analysis, summaries, suggested tasks |
| **Session History** | Redis-backed session engine, per-session recordings/transcripts/analysis |
| **Attachments** | Generic file uploads with S3/local providers for tasks, events, sessions |
| **Relations** | Cross-entity linking between meetings, sessions, and tasks |
| **Security & Rate Limiting** | Per-user API rate limiting, Google Identity Services, 2FA |
| **External Providers** | Brevo email, AWS S3 storage, environment-based provider switching |
| **Testing & Docker** | 2100+ tests, Docker Compose with 6 services, health checks |
| **Push Notifications** | Browser push notifications for scheduled meetings via VAPID |

---

## Current Product Boundaries

The application currently supports the following and **only** the following:

1. **Single-user productivity** — All data is scoped to individual users. There is no multi-user collaboration, no shared workspaces, and no team features.

2. **Audio meetings only** — Meetings are audio-only with WebRTC peer-to-peer. There is no video, no screen recording by the server, and no in-meeting text chat.

3. **Manual file uploads** — Attachments are uploaded after the fact. There is no automatic capture, no live file sharing during meetings, and no file preview.

4. **Post-meeting AI analysis** — AI analysis requires a transcript to be uploaded manually after a meeting. There is no real-time transcription or live analysis.

5. **One-way entity linking** — Relations connect meetings, sessions, and tasks. There is no linking for notes, calendar events, or whiteboards.

6. **Provider-switchable storage and email** — Storage and email can be switched between local and production providers via a single environment variable.

7. **Self-hosted deployment** — The application is designed for self-hosting via Docker Compose. There is no SaaS deployment, no multi-tenancy, and no managed hosting.

8. **No offline support** — The application requires an active network connection to the backend API.

9. **No data export or import** — There is no mechanism to export or import data between instances.

10. **No internationalization** — The application is English-only with no i18n or l10n support.

---

## Assumptions

1. **PostgreSQL is the primary data store.** All persistent application data is stored in PostgreSQL. Redis is used exclusively for caching, session management, OTP storage, and Celery task brokering.

2. **UUID7 is used for all primary keys.** Time-ordered UUIDs provide unique identifiers across all entities without sequential ID exposure.

3. **Soft delete is the default deletion strategy.** Calendar events, notes, tasks, meetings, and whiteboards use nullable `deleted_at` columns rather than hard deletes. The `users` table uses a boolean `is_active` flag instead.

4. **All mutations are single-tenant.** Every data operation is scoped to a single authenticated user. There is no cross-user data access or sharing.

5. **The frontend is a single-page application.** React Router handles client-side routing. The nginx reverse proxy forwards all `/api/` and `/ws/` requests to the backend.

6. **WebSocket is used only for meeting signaling.** Real-time WebSocket connections are established exclusively for meeting room communication. There is no WebSocket usage for notifications, chat, or collaborative editing.

7. **Celery handles all async operations.** Email delivery, AI analysis, and scheduled reminder sweeps are processed by Celery workers, not in the main request thread.

8. **File storage is environment-dependent.** LOCAL uses the local filesystem; PRODUCTION uses AWS S3. The selection is made via the `ENVIRONMENT` variable and the provider factory.

9. **Email delivery is environment-dependent.** LOCAL uses SMTP with Mailpit; PRODUCTION uses the Brevo API. The selection is made via the `ENVIRONMENT` variable and the provider factory.

10. **AI analysis requires external API access.** Meeting transcript analysis depends on the NVIDIA NIM API (Llama 3.3 70B). Without API access, the AI analysis feature is unavailable.

11. **The backend is the single source of truth.** All business logic, validation, and data persistence happens on the backend. The frontend is a consumer of the API.

12. **Redis session state for meetings is ephemeral.** Meeting session state in Redis is not backed up or persisted to the database. If Redis is restarted during an active meeting, session state is lost.

13. **Rate limiting is fail-open.** If Redis is unavailable, rate limiting is bypassed rather than blocking requests.

14. **The application is versioned as `release/v1` (scope 1) and `release/v2` (scope 2).** This document clearly separates features by version.
