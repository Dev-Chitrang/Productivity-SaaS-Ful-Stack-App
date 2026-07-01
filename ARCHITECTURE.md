# Architecture Overview

Unified Workspace is a modular, full-stack productivity application built with a React frontend and a Python FastAPI backend. The architecture follows feature-based isolation on the frontend and domain-driven layering on the backend. Communication between the two halves happens over REST (for CRUD operations) and WebSocket (for real-time meeting signaling).

---

## High Level Architecture

```
Frontend (React + Vite)
    |
    | HTTP/JSON (REST)
    | WebSocket (signaling)
    v
Backend (FastAPI + Uvicorn)
    |
    | SQLAlchemy (async)
    | Redis (async)
    v
PostgreSQL + Redis
```

### Request Lifecycle

A typical request flows through these layers:

1. Browser issues an HTTP request to the Vite dev server or built frontend
2. Axios instance attaches the JWT access token from localStorage
3. FastAPI receives the request, runs CORS middleware, then routes it to the appropriate endpoint
4. The route function calls into the controller with the request payload and authenticated user context
5. The controller validates inputs, calls the service layer
6. The service executes business logic, calls the repository layer
7. The repository executes database queries via SQLAlchemy async sessions
8. The response bubbles back up: repository -> service -> controller -> route -> HTTP response
9. React Query on the frontend caches the response and updates the UI

---

## Project Structure

```
productivity-app/
├── backend/               # Python FastAPI application
├── frontend/              # React + Vite application
├── docker-compose.yml     # Infrastructure services (Redis, Mailpit)
├── .gitignore
├── LICENSE                # MIT License
└── README.md
```

### backend/

**Purpose:** Server-side API, business logic, database access, real-time signaling, background task processing.

**Responsibility:** Handle all HTTP and WebSocket requests, authenticate users, enforce permissions, persist data, send async emails.

**What belongs here:**
- FastAPI application entry point and configuration
- SQLAlchemy ORM models and Alembic migrations
- Feature modules (auth, users, calendar, notes, tasks, meetings, whiteboards)
- Core infrastructure (config, database session, security, middleware, Redis, storage abstraction, logger)
- Celery worker tasks for async operations

**What does not belong here:**
- Frontend code, HTML, CSS, client-side JavaScript
- Static assets served to browsers

### frontend/

**Purpose:** Client-side user interface, state management, API integration, routing, UI components.

**Responsibility:** Render pages, manage authentication state, communicate with the backend API, handle real-time WebSocket events for meetings.

**What belongs here:**
- React components, pages, layouts, hooks, context providers
- Feature modules (auth, dashboard, calendar, notes, tasks, meetings, whiteboards, profile, settings)
- Shared UI components (shadcn/ui primitives)
- Axios instance with JWT interceptor
- TanStack React Query client configuration
- Routing definitions

**What does not belong here:**
- Server-side code, database logic, API implementations

### database/

Not a separate directory. Database schema is managed through:
- `backend/app/models/` -- SQLAlchemy ORM model definitions
- `backend/migrations/` -- Alembic migration scripts
- The actual database is PostgreSQL, managed externally

### docs/

No dedicated docs directory exists. Architecture is documented in this file. Setup and usage are in `README.md`.

---

## Frontend Architecture

### Feature-Based Architecture

Every feature module in `src/features/` is self-contained:

```
features/
├── auth/        # Login, signup, OAuth, password reset pages
├── dashboard/   # Landing page after authentication
├── calendar/    # Calendar views and event management
├── notes/       # Rich text notes CRUD
├── tasks/       # Task management with status/priority/checklists
├── meetings/    # Meeting rooms, WebRTC, guest access
├── whiteboards/ # Canvas-based drawing boards
├── profile/     # User profile management
└── settings/    # Application settings
```

Each feature module typically contains:

| Directory | Purpose |
|---|---|
| `pages/` | Top-level page components for routes |
| `components/` | Feature-specific UI components |
| `hooks/` | React Query hooks wrapping API calls |
| `api/` | Axios API functions and type definitions |
| `schemas/` | Zod validation schemas |
| `utils/` | Feature-specific utility functions |
| `constants/` | Feature-specific constants |

### API Layer

The API layer is centralized through `src/lib/axios.js`, which creates a pre-configured Axios instance:

- Base URL points to `VITE_API_URL/api/v1`
- Request interceptor attaches `Bearer {access_token}` from localStorage
- Response interceptor detects 401 responses and attempts automatic token refresh via `POST /auth/refresh` before retrying the original request
- On refresh failure, tokens are cleared and the user is redirected to `/auth`

Feature-specific API functions are defined in each module's `api/` directory and import the shared Axios instance.

### Hooks

Custom hooks (primarily React Query hooks in each module's `hooks/` directory) wrap API calls with caching, background refetching, loading states, and error handling. Examples:

- `useNotes(filter)` -- fetches notes list with query filters
- `useTask(id)` -- fetches a single task by ID
- `useCreateMeeting()` -- mutation hook for creating meetings

Mutation hooks accept `onSuccess` callbacks for optimistic UI updates.

### Pages

Pages are components that map to routes. They compose feature-specific components and manage local UI state (selection, dialogs, filters). Pages do not directly call the API -- they use hooks.

### Components

Components are split into three categories:

1. **Shared UI components** (`src/components/ui/`): shadcn/ui primitives built on Radix UI (button, card, dialog, form, input, popover, sheet, tooltip, etc.)
2. **Feature components** (`src/features/*/components/`): Feature-specific UI like `NoteEditor`, `CalendarGrid`, `TaskList`, `MeetingRoom`, `WhiteboardCanvas`
3. **Layout components** (`src/layouts/`): MainLayout (sidebar + header + outlet), AuthLayout (centered card), Sidebar, Header

### Shared Components

- **Rich Text Editor** (`src/shared/editor/`): Tiptap-based editor used by both Notes and Tasks modules. Includes extensions for tables, task lists, underlines, placeholders. Configured via `extensions.js` and styled through `EditorToolbar.jsx`.
- **Theme Toggle**: Light/dark mode switcher used in both MainLayout and AuthLayout.

### Layout

Two layout shells:
- **AuthLayout**: Minimal layout with a centered card, back-to-home link, and theme toggle. Used for forgot/reset password pages.
- **MainLayout**: Full application layout with Sidebar (collapsible, desktop), MobileSidebar (slide-over, mobile), Header (search, notifications placeholder, user menu), and an `<Outlet />` for page content. Wraps children in `SidebarProvider` and `TooltipProvider`.

### React Query

A single `QueryClient` instance is created in `src/lib/queryClient.js` with default settings. It is provided at the app root (implicitly, through component mounting). Features define their own query and mutation hooks using `useQuery` and `useMutation` from `@tanstack/react-query`.

React Query handles:
- Caching API responses with automatic stale detection
- Background refetching on window focus
- Mutation state management (loading, error, success)
- Cache invalidation after mutations

### State Management

There is no global state store. State is managed through:
- **React Query**: Server state (API data) with automatic caching and refetching
- **React Context**: Auth state (`AuthContext`), theme preference (`ThemeContext`), sidebar collapse state (`SidebarContext`)
- **Component state**: Local `useState` for UI state like dialog visibility, selected items, filters, search terms

### Routing

Routes are defined in `src/routes/AppRoutes.jsx` using `react-router-dom` v7:

- Public routes: `/` (landing), `/auth`, `/m/:meetingCode` (guest meeting join)
- Auth routes (AuthLayout): `/forgot-password`, `/reset-password`
- Protected routes (MainLayout): `/dashboard`, `/calendar`, `/notes`, `/tasks`, `/meetings`, `/meetings/:id`, `/meetings/:id/room`, `/whiteboards`, `/profile`, `/settings`

A `ProtectedRoute` wrapper checks for authentication via `AuthContext`. Unauthenticated users are redirected to `/auth`. The exception is meeting guest access, which is detected via URL pattern and checked against a guest session in localStorage.

---

## Backend Architecture

### Modules

The backend is organized into feature modules under `backend/app/modules/`. Each module follows a consistent structure:

```
modules/{module}/
├── __init__.py
├── routes.py        # FastAPI router with endpoint definitions
├── controller.py    # Orchestration, HTTP exception handling
├── service.py       # Business logic
├── repository.py    # Database access (SQLAlchemy queries)
├── schemas.py       # Pydantic request/response models
├── dependencies.py  # FastAPI dependency injection
├── exceptions.py    # Custom exception classes
├── enums.py         # Enum definitions
├── constants.py     # Constant values
└── utils.py         # Module-specific utilities
```

### Routes

Routes define HTTP endpoints using FastAPI `APIRouter`. Each route function:
- Accepts request payloads and dependency-injected dependencies
- Instantiates the controller with service dependencies
- Delegates to the controller
- Has a `tags` parameter for OpenAPI documentation grouping

Routes never contain business logic or database calls.

### Controllers

Controllers orchestrate the flow between HTTP and business logic:
- Extract parameters from the request
- Call the service layer
- Catch domain exceptions and convert them to HTTP exceptions
- Return Pydantic response models

Controllers never contain business logic or database access.

### Services

Services contain all business logic:
- Input validation beyond schema constraints
- Authorization checks
- Multi-step operations (e.g., meeting join flow, password reset)
- Email sending orchestration
- Token generation and validation

Services never access the database directly -- they delegate to repositories.

### Repositories

Repositories encapsulate all database access:
- SQLAlchemy queries using `select()`, `and_()`, `or_()`, etc.
- CRUD operations on ORM models
- Complex queries with filtering, sorting, pagination
- Transaction management (flush, rollback)

Repositories never contain business logic. They only translate between application data and database storage.

### Models

SQLAlchemy ORM models are defined in `backend/app/models/`. Each model corresponds to a database table. Models use:
- UUID primary keys generated via uuid7
- DateTime with timezone for all timestamps
- JSONB for flexible data storage (rich text content, board elements, checklists)
- Soft delete via nullable `deleted_at` columns
- Indexed foreign keys for query performance

### Schemas

Pydantic v2 models define:
- Request validation (type coercion, string length, regex patterns, field validators)
- Response serialization (using `from_attributes = True` for ORM mode)
- Domain-specific validation via `@field_validator` and `@model_validator` decorators

### Dependencies

FastAPI dependency injection is used for:
- Database session: `get_db()` yields an async SQLAlchemy session with commit/rollback handling
- Redis client: `get_redis_client()` provides async Redis connection
- Authentication: `get_current_user` decodes JWT and fetches the user; `get_current_user_id` decodes JWT and returns only the UUID
- Service construction: Each module defines a dependency function that builds the service with its repository

### Constants

Each module defines constants for:
- Maximum string lengths (title, description, location)
- Validation limits (minimum recurrence interval, etc.)
- WSEvent string constants for WebSocket message types

### Utils

Module-specific utility functions. Currently only the calendar module has a `utils.py` with a `RecurrenceEngine` that generates recurring event occurrences.

### Exceptions

Domain-specific exception classes are defined per module. They are caught by controllers and translated to HTTP error responses with appropriate status codes.

### Database Layer

The database layer in `backend/app/core/database.py` provides:
- An async SQLAlchemy engine configured from `POSTGRES_*` environment variables
- An `AsyncSessionLocal` session factory with `autocommit=False`, `autoflush=False`
- A `get_db()` async generator that yields sessions, commits on success, rolls back on exception, and always closes
- A `check_database_health()` function that runs `SELECT 1` on startup

### Authentication

Authentication is handled through:
- **JWT tokens** (HS256): Access tokens expire after 15 minutes, refresh tokens after 7 days
- **Redis whitelist**: Refresh tokens are stored in Redis under `session:{user_id}` for revocation capability
- **HTTP Bearer scheme**: The `security_agent = HTTPBearer()` is used in dependencies
- **OTP-based verification**: Signup email verification and login 2FA use 6-digit OTPs stored in Redis
- **Google OAuth**: Server-side token verification using `google.oauth2.id_token`
- **Password hashing**: bcrypt via `pwdlib` library

---

## Architecture Principles

### Repository Pattern

All database access must go through repository classes. Services and controllers never execute SQLAlchemy queries directly. Repositories accept ORM model instances and return ORM model instances or simple data structures.

**Why:** Isolates database implementation details. Queries, joins, and filtering logic are centralized. If the ORM or database changes, only repositories are affected.

### Service Layer

All business logic must live in service classes. Controllers only orchestrate, routes only route. Services are responsible for:
- Validating business rules
- Enforcing authorization
- Coordinating multi-step operations
- Interacting with external systems (Redis, email)

**Why:** Business logic is testable without HTTP. Controllers remain thin and focused on HTTP concerns. Features can be composed by calling multiple services.

### Dependency Injection

Dependencies are injected via FastAPI's `Depends` system. Services receive their repositories through constructors. Controllers receive their services through constructors. Database sessions, Redis clients, and authenticated users are all injected.

**Why:** Components are decoupled and testable in isolation. Dependencies can be swapped without changing consumers. The DI container manages lifecycle and cleanup.

### Single Responsibility

Every file has one clear responsibility:
- Routes define endpoints and nothing else
- Controllers handle HTTP concerns and nothing else
- Services handle business logic and nothing else
- Repositories handle database access and nothing else
- Schemas define data shapes and validation and nothing else

**Why:** Files are small, focused, and easy to reason about. Changes to one concern do not ripple across the codebase.

### Feature Isolation

Modules are self-contained and do not import from each other's internal modules. The auth module's dependencies are reused by other modules (for authentication), but business logic modules (calendar, notes, tasks, meetings, whiteboards) are independent.

**Why:** Features can be developed, tested, and deployed independently. Cross-module coupling is explicit and minimized.

### Reusable Components

UI components follow a layered hierarchy:
- shadcn/ui primitives are generic and reusable across the entire application
- Feature components are specific to their module but may compose primitives
- Shared components (rich text editor) are extracted when multiple modules need them

**Why:** Reduces duplication. Ensures visual consistency. Makes it easy to build new features with existing building blocks.

### No Business Logic Inside Routes

Route functions must only:
1. Extract request parameters
2. Call the controller
3. Return the response

Any conditional logic, validation beyond schema constraints, or data transformation must live in the service layer.

### No Database Access Outside Repository

No SQLAlchemy queries, `select()` statements, or ORM model manipulations should exist outside of repository classes. Services must call repository methods, not execute queries directly.

---

## Module Architecture

### Authentication Module

**Responsibilities:** User registration, login, Google OAuth, email verification, two-factor authentication, password reset, token refresh.

**Entry points:**
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/verify-signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/verify-login`
- `POST /api/v1/auth/google`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/password-reset/initiate`
- `POST /api/v1/auth/password-reset/confirm`
- `POST /api/v1/auth/resend-signup-otp`
- `POST /api/v1/auth/resend-login-otp`

**API:** All endpoints return structured JSON. Successful auth returns JWT token pairs. Error responses return standard HTTP status codes with detail messages.

**Database:** Reads and writes to the `users` table. OAuth flows update `google_id`, `oauth_provider`, and `profile_image` fields.

**UI:** AuthPage component handles login, signup, and OAuth flows. Google Identity Services (GSI) runs on the frontend and passes the ID token to the backend.

**Internal flow:** Registration creates a user with `is_verified=False`, generates a 6-digit OTP stored in Redis with a 10-minute TTL, sends the OTP via Celery async email, and returns a `verification_token`. The verify endpoint validates the OTP, marks the user verified, and issues JWT tokens.

### Dashboard Module

**Responsibilities:** Landing page shown after authentication.

**Entry points:** `GET /dashboard` (frontend route)

**API:** No dedicated API. The dashboard page exists as a UI-only route.

**Database:** No direct database interaction. The page optionally fetches user profile via the users module.

**UI:** A simple welcome page with navigation to other modules.

### Calendar Module

**Responsibilities:** Calendar event CRUD, recurring event expansion, multiple view modes.

**Entry points:**
- `POST /api/v1/calendar/events`
- `GET /api/v1/calendar/events?start=&end=`
- `GET /api/v1/calendar/events/{id}`
- `PATCH /api/v1/calendar/events/{id}`
- `DELETE /api/v1/calendar/events/{id}`

**API:** Events are fetched within a date range (start/end query params). Filters support search text, event type, and color. The list endpoint expands recurring events into individual occurrences within the requested range.

**Database:** Reads and writes to the `calendar_events` table. Supports `event_type` (PERSONAL, MEETING, REMINDER) and `color` enums, recurrence configuration (frequency, interval, end date). Soft delete via `deleted_at`.

**UI:** Four view modes (month grid, week grid, day timeline, agenda list) built as separate components. View state and anchor date are persisted in URL search parameters for browser navigation support. Event creation and editing use dialog components.

### Notes Module

**Responsibilities:** Rich text note management with categorization and tagging.

**Entry points:**
- `POST /api/v1/notes`
- `GET /api/v1/notes`
- `GET /api/v1/notes/{id}`
- `PATCH /api/v1/notes/{id}`
- `DELETE /api/v1/notes/{id}`
- `PATCH /api/v1/notes/{id}/restore`
- `PATCH /api/v1/notes/{id}/archive`
- `PATCH /api/v1/notes/{id}/unarchive`
- `PATCH /api/v1/notes/{id}/pin`
- `PATCH /api/v1/notes/{id}/unpin`
- `PATCH /api/v1/notes/{id}/favorite`
- `PATCH /api/v1/notes/{id}/unfavorite`

**API:** Notes support filtering by category, tags, pinned, favorited, archived, deleted status, and full-text search on title and content.

**Database:** The `notes` table stores rich text content as JSONB, category as an indexed string, and tags as a JSONB string array. Supports soft delete with restore.

**UI:** Split-panel layout with searchable note list on the left and Tiptap editor on the right. The editor autosaves on content changes. Supports pin, favorite, archive, and soft delete with confirmation dialogs.

### Tasks Module

**Responsibilities:** Task management with status workflow, priorities, due dates, checklists, and change history.

**Entry points:**
- `POST /api/v1/tasks`
- `GET /api/v1/tasks`
- `GET /api/v1/tasks/{id}`
- `PATCH /api/v1/tasks/{id}`
- `DELETE /api/v1/tasks/{id}`
- `PATCH /api/v1/tasks/{id}/restore`
- `PATCH /api/v1/tasks/{id}/archive`
- `PATCH /api/v1/tasks/{id}/unarchive`
- `PATCH /api/v1/tasks/{id}/pin`
- `PATCH /api/v1/tasks/{id}/unpin`
- `PATCH /api/v1/tasks/{id}/favorite`
- `PATCH /api/v1/tasks/{id}/unfavorite`
- `GET /api/v1/tasks/{id}/history`

**API:** Tasks support filtering by status, priority, labels, pinned, favorited, archived, deleted, due date range, and full-text search. The history endpoint returns a timeline of all field changes.

**Database:** The `tasks` table stores descriptions as JSONB (rich text), labels as JSONB string array, and checklists as JSONB array of `{id, text, completed}` objects. A separate `task_history` table tracks changes with action type, field name, old value, new value, and timestamp.

**UI:** Same split-panel layout pattern as notes. Task editor includes status dropdown, priority selector, date picker, label management, and interactive checklist. The history view shows a chronological list of changes.

### Meetings Module

See the Meetings Module Architecture section below.

### Whiteboards Module

See the Whiteboard Architecture section below.

---

## Meetings Module Architecture

### Lifecycle

A meeting progresses through five states:

```
CREATED --> ACTIVE --> IDLE --> (reactivates to ACTIVE when rejoined)
                  |           |
                  v           v
              CANCELLED     ENDED
```

- **CREATED**: Initial state after creation. Automatically transitions to ACTIVE when the host joins.
- **ACTIVE**: Meeting is in progress. Participants can be admitted, audio flows, screen sharing works.
- **IDLE**: All participants have left. The room is preserved and can be reactivated when someone rejoins.
- **ENDED**: Host ends the meeting. No further participation is possible until reactivation.
- **CANCELLED**: Host cancels the meeting. Permanent terminal state.

### Waiting Room

Participants who are not the host enter a WAITING status upon joining. They are placed in a virtual waiting room:
- The WebSocket sends a `PARTICIPANT_WAITING` event to all connected clients
- The waiting participant receives a `WAITING_ROOM_STATUS` message
- When the host admits them (via `POST /{meeting_id}/participants/{id}/admit`), their status changes to ADMITTED
- The WebSocket broadcasts a `PARTICIPANT_ADMITTED` event
- Until admitted, the participant's WebSocket only responds to `check_admitted` pings

### Host

The host is the user who created the meeting. Host privileges:
- Admit, reject, remove, mute, and unmute participants
- End or cancel the meeting
- Approve or reject screen share requests
- Force-stop active screen shares
- The host bypasses the waiting room (admitted immediately)

### Participant

Participants can be:
- **REGISTERED**: Authenticated users with a JWT token
- **GUEST**: Unauthenticated users joining via meeting link with name and email

Guest identity is tracked via `guest_email`. Redis is not involved in guest session tracking -- the frontend stores guest session data in localStorage.

Participant statuses: `WAITING -> ADMITTED -> LEFT | REMOVED | REJECTED`

Rejoining is supported: if a participant left and rejoins, their previous participant record is reused rather than creating a new one.

### Audio

Audio is transmitted via WebRTC. The backend does not process or store audio streams. It only relays WebRTC signaling messages (offers, answers, ICE candidates) between peers through the WebSocket connection.

### Recording

Meeting recordings are uploaded after the fact via `POST /{meeting_id}/recordings`:
- Files are saved to local storage under `{STORAGE_BASE_DIR}/{meeting_id}/recordings/`
- Metadata (filename, content_type, size, duration, storage path) is stored in the `meeting_recordings` table
- Recordings can be listed, downloaded, and deleted

### Transcript

Meeting transcripts follow the same pattern as recordings:
- Uploaded via `POST /{meeting_id}/transcripts`
- Stored under `{STORAGE_BASE_DIR}/{meeting_id}/transcripts/`
- Metadata in `meeting_transcripts` table
- List, download, delete operations available

### Screen Share

Screen sharing requires host approval:
1. Participant requests permission via WebSocket (`request_screen_share`)
2. The host is notified via `SCREEN_SHARE_REQUESTED` broadcast
3. Host approves (`POST /{meeting_id}/screen-share/approve/{id}`) or rejects
4. On approval, the participant receives `SCREEN_SHARE_PERMISSION_GRANTED`
5. Participant starts sharing via WebSocket (`screen_share_started`)
6. Host can force-stop at any time
7. Only one participant can share at a time

### WebSocket

The WebSocket endpoint at `/ws/meetings/{meeting_id}` is the signaling hub:
- **Connection**: JWT token (authenticated users) or guest name/email (guests)
- **Room isolation**: Each meeting has a room. The `ConnectionManager` tracks room -> connection_id -> WebSocket mappings
- **Polling model**: The WebSocket loops with a 3-second timeout, receiving messages and checking participant status changes from the database
- **Disconnection**: On disconnect, the participant is marked as LEFT, the host departure is broadcast, and the room transitions to IDLE if empty

### WebRTC

WebRTC signaling is relayed through the WebSocket:
- `offer`, `answer`, `ice-candidate` messages are forwarded between peers
- Messages can target a specific peer (`target_connection_id`) or broadcast to all
- The backend does not touch the content of signaling messages -- it only routes them

### Permission Flow

1. **Meeting Access**: Anyone with the meeting link can attempt to join. Authenticated users are identified by JWT. Guests must provide name and email.
2. **Admission**: The host must explicitly admit each non-host participant from the waiting room.
3. **Screen Sharing**: Requires host approval even after admission.
4. **Mute**: Host can mute/unmute any admitted participant. Participants can self-mute/unmute.

### State Flow

The WebSocket loop is a state machine that polls the database every 3 seconds:
- Checks if the participant was removed, rejected, or the meeting ended (close connection)
- Detects admission transitions from WAITING to ADMITTED (sends notification)
- Detects mute state changes initiated by the host (sends notification)
- Blocks WebRTC signaling if the participant is muted by the host

---

## Whiteboard Architecture

### Board

A whiteboard is a persisted document with a title and board data. Boards are user-owned and support:
- Renaming
- Favoriting/unfavoriting
- Archiving/unarchiving
- Soft delete and restore
- Search by title
- Filter by status (all, archived, deleted, favorited)

### Canvas

The canvas is built on Konva (react-konva). It renders elements from the board data's `elements` array. The canvas supports:
- Zoom (min 0.1x, max 5x, step 0.1)
- Pan via scroll
- Element selection via click
- Desktop and mobile stage refs (for export)

### Elements

Elements are stored in the `board_data.elements` JSONB array. Each element has:
- `id`: Unique identifier
- `type`: One of `pen`, `rectangle`, `circle`, `line`, `arrow`, `text`
- `points`: Coordinate data (varies by type)
- Style attributes: `stroke`, `strokeWidth`, `fill`, `rotation`

Element types:
- **Pen**: Freehand drawing stored as an array of points
- **Rectangle**: Position, width, height, rotation
- **Circle**: Position, radius
- **Line**: Start and end points
- **Arrow**: Line with arrowhead rendering
- **Text**: Position, text content, font size

### Autosave

Autosave triggers 1 second after the last element change. A `useEffect` with a debounce timer:
1. User draws or modifies elements
2. Previous timer is cleared
3. New 1-second timer starts
4. On timer fire, the full `board_data` object is sent via `PATCH /{id}/board`
5. The server replaces the `board_data` column

### Export

Export uses the Konva stage's `toDataURL({ pixelRatio: 2 })` method:
1. Finds the visible stage (desktop or mobile ref)
2. Generates a data URL at 2x resolution
3. Creates a temporary anchor element
4. Triggers download with the board title as filename

### History

History is managed client-side as an array of element snapshots:
- `history`: Array of element arrays (each entry is a complete snapshot)
- `historyIndex`: Current position in the history array
- On every element change, the new elements are pushed to history (trimming any redo entries)

### Undo/Redo

- **Undo**: Decrements `historyIndex`, restores elements from `history[historyIndex - 1]`
- **Redo**: Increments `historyIndex`, restores elements from `history[historyIndex + 1]`
- Keyboard shortcuts: Ctrl+Z (undo), Ctrl+Shift+Z or Ctrl+Y (redo)
- Buttons disabled when at the beginning or end of history

### Storage

Board data is stored in the `whiteboards` table:
- `board_data`: JSONB column with `{version: 1, elements: [...]}`
- The entire board state is sent and stored as one JSON object per save
- No incremental/delta updates. Every autosave replaces the full board data.

---

## Database Design

### Entity Relationships

```
User (1) ----< Task                   (user_id FK)
User (1) ----< Note                   (user_id FK)
User (1) ----< CalendarEvent          (user_id FK)
User (1) ----< Meeting (as host)      (host_id FK)
User (1) ----< Whiteboard             (user_id FK)

Meeting (1) ----< MeetingParticipant  (meeting_id FK)
Meeting (1) ----< MeetingRecording    (meeting_id FK)
Meeting (1) ----< MeetingTranscript   (meeting_id FK)

Task (1) ----< TaskHistory            (task_id FK)
```

All foreign keys are UUIDs. All relationships are one-to-many from the owning entity.

### Primary Tables

| Table | Purpose |
|---|---|
| `users` | User accounts, authentication, profile |
| `tasks` | Task items with status, priority, due dates, checklists |
| `task_history` | Audit trail of task field changes |
| `notes` | Rich text notes with categories and tags |
| `calendar_events` | Calendar entries with recurrence |
| `meetings` | Meeting rooms with lifecycle and screen share state |
| `meeting_participants` | Participants with waiting/admitted/left/removed/rejected status |
| `meeting_recordings` | Recording file metadata |
| `meeting_transcripts` | Transcript file metadata |
| `whiteboards` | Canvas board data with elements |

### Soft Delete

The following tables use soft delete via a nullable `deleted_at` column:
- `calendar_events`
- `notes`
- `tasks`
- `meetings`
- `whiteboards`

All read queries filter on `WHERE deleted_at IS NULL` (or explicitly include deleted rows when querying trashed items). Restore sets `deleted_at = NULL`. The `users` table uses a boolean `is_active` column instead of soft delete.

### Status Enums

| Enum | Values | Used By |
|---|---|---|
| `TaskStatus` | TODO, IN_PROGRESS, DONE | tasks |
| `TaskPriority` | LOW, MEDIUM, HIGH | tasks |
| `EventType` | PERSONAL, MEETING, REMINDER | calendar_events |
| `EventColor` | RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, GRAY | calendar_events |
| `RecurrenceFrequency` | DAILY, WEEKLY, MONTHLY | calendar_events |
| `MeetingStatus` | CREATED, ACTIVE, IDLE, ENDED, CANCELLED | meetings |
| `ParticipantType` | REGISTERED, GUEST | meeting_participants |
| `ParticipantStatus` | WAITING, ADMITTED, LEFT, REMOVED, REJECTED | meeting_participants |

---

## Request Lifecycle

### Example: Creating a Task

1. **Frontend**: User fills in the task form and clicks save. The `useCreateTask` mutation hook calls `POST /api/v1/tasks` with the task data via the Axios instance.

2. **Axios interceptor**: The request interceptor reads `access_token` from localStorage and attaches it as `Authorization: Bearer {token}`.

3. **FastAPI routing**: The request arrives at `POST /api/v1/tasks`. FastAPI runs CORS middleware, then calls `create_task_endpoint` in `tasks/routes.py`.

4. **Dependency injection**: FastAPI resolves `get_current_user_id` (decodes JWT, returns UUID) and `get_tasks_service` (creates `TaskRepository` with database session, creates `TaskService` with the repository).

5. **Route**: `create_task_endpoint` receives the validated Pydantic payload, the user ID, and the service. It creates a `TaskController` and calls `ctrl.create_user_task(current_user_id, payload)`.

6. **Controller**: `handle_create_task` calls `self.service.create_task(current_user_id, payload)`.

7. **Service**: `create_task` validates that the user exists (calls `self.repo.get_user_by_id()`), validates business rules (check for duplicate titles if needed), generates a UUID for the task, then calls `self.repo.create(task_data)`.

8. **Repository**: `create` creates a `Task` ORM instance with the provided data, adds it to the session, calls `await self.db.flush()` to persist, and returns the task. It also creates a `TaskHistory` record with action=CREATED.

9. **Response construction**: The task object bubbles back up. The controller wraps it in a `TaskResponse` Pydantic model. FastAPI serializes it to JSON.

10. **Response**: The HTTP response flows back through the middleware (logs duration, sets X-Process-Time header). Axios receives it, React Query caches the response, and the mutation's `onSuccess` callback updates the UI.

---

## Coding Guidelines

### Where New Code Belongs

- **New feature**: Create a new module in `backend/app/modules/{name}/` following the existing pattern (routes, controller, service, repository, schemas, dependencies). Create a corresponding `frontend/src/features/{name}/` with pages, components, hooks, and API.
- **New API endpoint**: Add to the appropriate module's `routes.py`. Follow the existing naming pattern.
- **New database table**: Create an ORM model in `backend/app/models/`, generate an Alembic migration with `alembic revision --autogenerate`, and create repository methods in the appropriate module.
- **New UI component**: If reusable across features, add to `frontend/src/components/ui/`. If feature-specific, add to the feature's `components/` directory.
- **New shared utility**: Add to `frontend/src/lib/` for frontend utilities or `backend/app/utils/` for backend utilities.

### Where Code Should Never Go

- Business logic in route functions
- Database queries in service or controller classes
- HTTP-specific code (status codes, response objects) in service classes
- Feature-specific components in shared UI directories
- API calls directly in page components (use hooks)
- Environment-specific configuration values hardcoded in source files

### How Future Features Should Be Added

1. Create database models and migration
2. Implement the backend module (repository -> service -> controller -> routes)
3. Register routes in `main.py`
4. Implement the frontend feature module (API -> hooks -> components -> pages)
5. Add routes in `AppRoutes.jsx`
6. Add sidebar navigation in `Sidebar.jsx` if needed

Each new module should strictly follow the established architectural patterns. Do not deviate from the layered backend structure or the feature-based frontend organization.

---

## Future Architecture

### Redis

Redis is currently used for session whitelisting, OTP storage, and the Celery broker. Future expansion should include:
- Rate limiting for authentication endpoints
- Caching for frequently accessed data (task lists, calendar events)
- Real-time presence indicators for collaborative features
- Meeting session state management (move state out of the database for lower latency)

### Cross-Module Communication

Modules are currently isolated. Future direction includes:
- Calendar events linking to meetings (click a calendar event to join a meeting)
- Tasks linked to notes (reference a note from a task description)
- Whiteboard embeds within meetings (collaborate on a whiteboard during a meeting)
- A unified activity feed across all modules
- A tagging system that spans across notes, tasks, and meetings

### Real-time Presence

The WebSocket infrastructure used for meetings can be extended to support:
- Online/offline indicators for users
- "User is typing" indicators in collaborative notes
- Live cursor positions in collaborative whiteboards
- Real-time notification delivery

### Notifications

A notification system should span:
- Meeting reminders (before scheduled meetings)
- Task due date alerts
- Changes to shared resources
- Meeting activity (participant joined, host ended meeting)
- Push notifications via WebSocket or service workers

### Collaboration

Collaborative features planned for future versions:
- Real-time collaborative editing on notes (using CRDT or OT via the Tiptap collaboration extension)
- Multi-user whiteboard editing with live cursor synchronization
- Shared task lists assigned to multiple users
- Meeting scheduling with invitees and RSVP
- Role-based access control for shared workspaces

The WebSocket infrastructure, Redis pub/sub, and the existing ConnectionManager provide the foundation for these features. The layered backend architecture allows adding real-time capabilities without disrupting existing REST endpoints.
