# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-06-25

Initial project setup and application scaffold.

### Added

- MIT License.
- Backend API scaffolded with FastAPI and Uvicorn.
- Frontend scaffolded with Vite, React 19, and shadcn/ui.
- PostgreSQL database with async SQLAlchemy and Alembic migrations.
- Redis integration for caching and session management.
- Celery worker for async task processing.
- Axios HTTP client with request/response interceptors and automatic token refresh.
- TanStack React Query for server state management and caching.
- Protected routing with authentication guards.
- Light and dark theme toggle with ThemeContext.
- Collapsible sidebar navigation.
- WebSocket manager for real-time communication.
- Landing page.

---

## [1.1.0] - 2026-06-25

Authentication system and user management.

### Added

- User registration with email verification via 6-digit OTP.
- User login with email and password.
- Forgot password flow with OTP-based verification and password reset.
- Google OAuth sign-in with server-side token verification.
- JWT-based authentication with access tokens (15-minute expiry) and refresh tokens (7-day expiry).
- Token refresh endpoint with Redis-backed session whitelist for revocation.
- Two-factor authentication support via login OTP.
- Resend signup and login OTP endpoints.
- User profile page with profile image, name, and email update.
- Application settings page.
- Auth layout with centered card UI for login, signup, and password flows.

### Security

- Password hashing with bcrypt via pwdlib.
- JWT tokens signed with HS256 algorithm.
- Refresh tokens stored in Redis for server-side revocation.
- OTPs stored in Redis with 10-minute TTL.

### Infrastructure

- Docker Compose with Redis 7.2 and Mailpit for local SMTP catching.

---

## [1.2.0] - 2026-06-27

Calendar module with event management and recurrence.

### Added

- Calendar with month grid, week grid, day timeline, and agenda list views.
- Event creation, editing, and deletion with form validation.
- Event detail dialog for viewing full event information.
- Event recurrence configuration (daily, weekly, monthly) with interval control and end date.
- Recurrence engine that expands recurring events into individual occurrences within a date range.
- Calendar search and filter by event type (Personal, Meeting, Reminder).
- Color-coded events with 7 color options.
- Calendar API with date-range queries and query filters.
- Backend calendar module with full CRUD API (routes, controller, service, repository).
- Backend recurrence utility engine.

### Changed

- Sidebar navigation expanded with Calendar link.
- Main layout updated to include Header with search and user menu.

### Improved

- UI component library expanded with shadcn/ui calendar components (Popover, Select, RadioGroup).
- View state and anchor date persisted in URL search parameters for browser navigation.

---

## [1.3.0] - 2026-06-27

Notes module with rich text editing.

### Added

- Rich text note editor with formatting toolbar (bold, italic, headings, lists, links, code blocks).
- Note creation, editing, and deletion.
- Note list with search and filter by status.
- Pin and favorite support for notes.
- Archive and soft delete with restore capability.
- Confirmation dialogs for destructive actions (delete, archive, unarchive).
- Backend notes module with full CRUD API and category/tag support.

---

## [1.4.0] - 2026-06-28

Tasks module with status workflow and activity tracking.

### Added

- Task creation, editing, and deletion.
- Rich text editor for task descriptions using TipTap.
- Task filtering by status (Todo, In Progress, Done) and priority (Low, Medium, High).
- Task search with full-text query.
- Interactive checklists within tasks.
- Label management for task categorization.
- Due date assignment and tracking.
- Activity timeline showing chronological field change history for each task.
- Backend tasks module with full CRUD API and TaskHistory audit trail.
- TipTap editor utility for converting rich text to plain text.

### Changed

- Extracted shared Rich Text Editor component into `src/shared/editor/` for use by both Notes and Tasks modules.

### Improved

- Note editor refactored to use the shared editor component.
- Editor toolbar updated with table, task list, underline, and placeholder extensions.

---

## [1.5.0] - 2026-06-30

Audio meetings with real-time communication.

### Added

- Audio meetings with WebRTC-based real-time communication.
- Meeting room with participant management and status tracking.
- Meeting creation, editing, and deletion.
- Join meeting via shareable link or meeting code.
- Guest session support without authentication (name and email required).
- Screen sharing with host approval workflow.
- Meeting recording with upload, download, and deletion.
- Live transcription panel with transcript upload.
- In-meeting chat via WebSocket.
- Waiting room with host approval for participant admission.
- Host controls: admit, reject, remove, mute, and unmute participants.
- WebSocket signaling for WebRTC (offer, answer, ICE candidate relay).
- ConnectionManager for room isolation and connection tracking.
- Backend meetings module with full CRUD API, WebSocket handler, and local file storage.
- Meeting lifecycle state machine (CREATED, ACTIVE, IDLE, ENDED, CANCELLED).

### Security

- Meeting access controlled via JWT token or guest session.
- Host-only privileges for admission, removal, mute, and screen share approval.
- WebRTC signaling blocked for muted participants.

---

## [1.6.0] - 2026-07-01

Whiteboard module with collaborative drawing tools.

### Added

- Digital whiteboard with canvas built on Konva and react-konva.
- Freehand pen drawing tool with configurable stroke.
- Shape tools: rectangle, circle, line, and arrow.
- Text tool with customizable font size.
- Image placement on the canvas.
- Zoom (0.1x to 5x) and pan via scroll.
- Whiteboard creation, editing, and deletion.
- Whiteboard list with search and filter by status (all, archived, deleted, favorited).
- Favorite and archive support with soft delete and restore.
- Autosave with 1-second debounce after element changes.
- Client-side undo/redo with Ctrl+Z and Ctrl+Shift+Z keyboard shortcuts.
- History management with element snapshot array.
- Export to PNG at 2x resolution.
- Backend whiteboard module with full CRUD API and JSONB board data storage.
- Sidebar collapse state managed via SidebarContext.

### Infrastructure

- Project architecture documented in ARCHITECTURE.md (853 lines).
- Project README with setup instructions, tech stack, and feature overview.

---

## [1.6.1] - 2026-07-01

Dashboard analytics and bug fixes across Notes, Tasks, and Whiteboard modules.

### Added

- Dashboard page with analytics overview for calendar, notes, and tasks.
- Today overview widget showing upcoming events and pending tasks.
- Analytics cards for calendar events, notes, and tasks with Recharts.
- Shared TableDialog component for rich text editor table insertion.
- Module sidebar collapse on page navigation via useModuleSidebarCollapse hook.

### Fixed

- Notes page pagination, filtering, and error handling.
- Tasks page pagination, filtering, and error handling.
- Whiteboard page loading states and error handling.
- Rich text editor toolbar responsiveness on smaller screens.
- Axios interceptor token refresh logic race condition.

### Changed

- Dashboard layout restructured to display module-specific analytics cards.
- EditorToolbar refactored for improved table dialog integration.

---

## [2.0.0] - 2026-07-06

Major platform extensions: meeting scheduling, reminders, AI analysis, Redis sessions, attachments, and cross-module relations.

### Added

- Meeting scheduling with calendar integration, allowing meetings to be created with specific dates and times.
- Reminder engine powered by Celery Beat that sweeps every 30 minutes for meeting, calendar, and task reminders.
- Meeting push reminder task running every minute for meetings starting within 10 minutes.
- Reminder settings per user with granular controls for email notifications, meeting reminders, calendar reminders, and task due/overdue reminders.
- Reminder notification service with HTML and plain text email templates (reminder created, reminder updated).
- AI meeting analysis powered by NVIDIA NIM (Llama 3.3 70B) that generates summary, coverage percentage, covered/out-of-agenda points, and suggested tasks from transcripts.
- Transcript preprocessor that normalizes raw transcript text for AI consumption.
- Async AI analysis pipeline via Celery task with completion email delivery.
- Redis session engine for meetings using Redis db index 1 for session state management.
- Session history panel with chronological session tracking per meeting.
- Session detail page for viewing individual session recordings, transcripts, and participant data.
- File attachments for tasks, calendar events, and meeting sessions.
- Full attachments module with CRUD API, MIME type validation, and extension whitelisting.
- Attachment panel component for uploading, viewing, and managing attachments.
- Cross-module entity links connecting meetings to tasks and tasks to meetings.
- Entity links module with full CRUD API.
- AI suggestions module for generating suggested tasks from meeting transcripts.
- Linked Tasks panel on meeting detail pages showing AI-suggested tasks.
- Linked Meetings panel on task detail pages showing associated meetings.
- Meeting schedule integration with Celery Beat for background processing.

### Changed

- Meeting model extended with scheduled date/time fields and participant session tracking.
- Meeting service refactored to support scheduled meetings with Redis-backed session state.
- Meeting controller updated with schedule, session history, and analysis endpoints.
- Meeting schemas updated to support scheduling, session history, and analysis request/response shapes.
- Task service updated to support entity link creation from AI suggestions.
- Calendar service updated with reminder integration.

### Improved

- Meeting session management moved from database-only to Redis for lower latency.
- Meeting authorization logic extracted into dedicated authorization module.
- Meeting completion service updated to trigger AI analysis after transcript upload.

### Security

- Meeting participant authorization enforced via dedicated authorization checks.
- Attachment upload validated with python-magic MIME detection against extension-to-MIME mapping.
- File size limits enforced on all attachment uploads.

### Infrastructure

- Celery Beat scheduled tasks for reminder engine sweeps and push notification checks.
- Reminder email templates in HTML and plain text formats (Jinja2).
- Storage abstraction layer supporting local filesystem and cloud storage providers.

---

## [2.1.0] - 2026-07-06

Dashboard overhaul and security hardening.

### Added

- Complete dashboard rebuild with 16 new components: WelcomeSection, OverviewCards, TodaysAgenda, UpcomingMeetings, RecentActivity, RecentTasks, RecentNotes, RecentWhiteboards, RecentAttachments, RecentAnalyses, CalendarAnalytics, NotesAnalytics, TasksAnalytics, DashboardHeader.
- Per-user API rate limiting with sliding window algorithm using Redis sorted sets.
- Rate limiter applied to all 10 route modules: auth, users, calendar, notes, tasks, meetings, whiteboard, attachments, AI suggestions, notifications.
- Rate limiter identifies users by JWT subject claim with fallback to client IP.
- Rate limiter returns 429 Too Many Requests with Retry-After header.
- Dashboard API endpoint serving aggregated data for all dashboard widgets.

### Security

- Sliding-window rate limiting per user on all API endpoints.
- Fail-open design on Redis errors to prevent service disruption.
- Attachment security validation with extension whitelist and MIME type detection via python-magic.
- Upload file validation checking file size, extension, and MIME type against allowed mappings.

### Changed

- Dashboard completely rebuilt from analytics-only to full activity feed with module-specific widgets.
- Dashboard page now consumes a unified dashboard API instead of separate module queries.

---

## [2.2.0] - 2026-07-07

External integrations: expanded OAuth, transactional email, and cloud storage.

### Added

- OAuth provider integration architecture supporting multiple identity providers beyond Google.
- Brevo email provider for transactional email delivery in production environments.
- SMTP email provider for local development with Mailpit.
- AWS S3 storage provider for file storage in production environments.
- Local storage provider for local development.
- Provider factory with environment-based selection (LOCAL vs PRODUCTION).
- Centralized environment configuration system with pydantic-settings.

### Changed

- Email sending switched to Brevo provider in production, SMTP in development.
- File storage switched to S3 provider in production, local filesystem in development.
- Storage service facade supporting save, delete, presigned URL upload/download, and path-based operations.
- Environment configuration centralized in `backend/app/core/config.py` with typed fields for PostgreSQL, JWT, Redis, SMTP, OAuth, AI, VAPID, Brevo, and AWS S3.

### Improved

- Provider abstraction allows switching between local and production services via a single environment variable.

### Infrastructure

- Environment configuration files (`.env.example`) for root, backend, and frontend.
- S3 presigned URL support for direct-to-cloud uploads and downloads.

---

## [2.3.0] - 2026-07-12

Browser push notifications for scheduled meetings.

### Added

- Browser push notifications for meetings starting within 10 minutes.
- Notifications module with full CRUD API (routes, controller, service, repository, schemas, enums, exceptions, constants).
- Web Push provider using VAPID keys for encrypted push delivery.
- Service Worker (`sw.js`) for receiving and displaying push notifications in the background.
- Push subscription manager component for requesting notification permission and managing subscriptions.
- Notification bell component in the header with unread count badge.
- Notification dropdown showing recent notifications inline.
- Notifications page with full notification history, filtering, and mark-as-read.
- Recent notifications widget on the dashboard.
- Notification preference settings for enabling/disabling push notifications.
- Timezone support on user profile and settings pages for accurate meeting reminder scheduling.
- TimezoneField component for timezone selection.

### Changed

- Meeting scheduling integrated with push notification delivery pipeline.
- Calendar event creation updated to support timezone-aware scheduling.
- User profile and settings pages updated with timezone configuration.
- Meeting create/edit dialogs updated with scheduled time and timezone fields.

### Improved

- Reminder engine extended to send push notifications in addition to email reminders.
- Celery Beat push reminder task checks for upcoming meetings every minute.

### Infrastructure

- VAPID key pair generation and configuration for Web Push protocol.
- Push notification database model with subscription and delivery tracking.
- Alembic migration for push notification table schema.

---

## [2.4.0] - 2026-07-10

Comprehensive test suite and production-ready Dockerization.

### Added

- 2100+ test cases across all backend modules.
- Test coverage for every module layer: routes, controllers, services, repositories, schemas, dependencies, enums, exceptions, and constants.
- Integration tests for AI suggestions and meeting workflows.
- Model unit tests for all 8 database models.
- Core infrastructure tests: config, database, email, providers, Redis, security, storage, WebSocket manager.
- Worker task tests covering Celery task configuration, retry logic, and execution flows.
- TipTap converter utility tests.
- Alembic database migration framework with initial schema migration.
- User timezone nullable migration for timezone support.
- Push notification model migration.
- Backend entrypoint script with database and Redis health checks.
- Celery entrypoint script for worker and beat startup.
- Pytest configuration with pytest.ini.
- pytest-cov for test coverage reporting.

### Infrastructure

- Backend Dockerfile: multi-stage build with Python 3.11-slim, uv package manager, non-root `appuser`, libmagic1 for MIME detection, dynamic Uvicorn workers (computed from CPU cores in production).
- Frontend Dockerfile: multi-stage build with Node 22-alpine, npm ci, Vite production build, nginx stable-alpine for static serving.
- Docker Compose with 6 services: frontend (nginx:80), backend (FastAPI:8000), Celery worker+beat, PostgreSQL 16-alpine, Redis 7.2-alpine, Mailpit (SMTP catcher on ports 1025/8025).
- Nginx configuration for SPA routing with proxy pass to backend API.
- `.dockerignore` files for root, backend, and frontend to exclude unnecessary files from builds.
- 5 named Docker volumes for PostgreSQL data, Redis data, Mailpit data, logs, and uploads.
