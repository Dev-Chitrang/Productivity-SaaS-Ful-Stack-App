# SaaS Productivity Suite — Architecture

## 1. Overall Architecture

The SaaS Productivity Suite is a full-stack collaborative productivity platform. It follows a **modular monorepo** layout with a **FastAPI async backend** and a **React SPA frontend**, communicating over REST and WebSockets.

```mermaid
flowchart TB
    subgraph Frontend["Frontend — React SPA"]
        direction TB
        FE["Vite + React 19 + Tailwind CSS 4"]
        Auth["AuthContext + Axios Interceptors"]
        WS["WebSocket Client (Signaling)"]
        RTCMgr["RTCMeshManager (WebRTC)"]
    end

    subgraph Ingress["Ingress — Nginx Reverse Proxy"]
        Nginx["Nginx :80/:443"]
        TLS["Let's Encrypt TLS"]
    end

    subgraph Backend["Backend — FastAPI + Uvicorn"]
        API["FastAPI App"]
        WS_B["WebSocket Router"]
        MW["Middleware (CORS, Logging)"]
        Core["Core (DB, Redis, Security, RateLimit)"]
        Modules["12 Feature Modules"]
        Workers["Celery Workers + Beat"]
    end

    subgraph Data["Data & Infrastructure"]
        PG["PostgreSQL 16 (asyncpg)"]
        Redis["Redis 7.2 (cache + broker)"]
        S3["Storage (Local / S3)"]
        SMTP["Email (SMTP / Brevo)"]
        NIM["NVIDIA NIM LLM API"]
    end

    FE --> Nginx
    Auth --> API
    WS --> WS_B
    RTCMgr --> WS_B
    Nginx -->|/api/*| API
    Nginx -->|/ws/*| WS_B

    API --> MW
    MW --> Core
    Core --> Modules
    API --> WS_B
    API --> Workers
    Workers --> Core
    Workers --> SMTP
    Workers --> NIM

    Core --> PG
    Core --> Redis
    Core --> S3
    Modules --> Core
```

---

## 2. Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite 8, Tailwind CSS 4, shadcn/ui (Radix), Tiptap 3, Konva, Recharts, Framer Motion, React Query (TanStack), Phosphor Icons |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, pydantic-settings |
| Database | PostgreSQL 16 (asyncpg driver, SQLAlchemy async) |
| Cache/Broker | Redis 7.2 (connection pool, Celery broker, session tokens, rate limiting) |
| Task Queue | Celery + Beat (autoretry, retry backoff) |
| Storage | Local filesystem (LOCAL) / AWS S3 (PRODUCTION) via Strategy pattern |
| Email | SMTP + Mailpit (LOCAL) / Brevo (PRODUCTION) |
| Real-time | WebSockets (FastAPI) + WebRTC mesh (browser-native) |
| AI | NVIDIA NIM (`meta/llama-3.3-70b-instruct`) via OpenAI-compatible client |
| Auth | JWT (HS256, access 15 min, refresh 7 days) + Google Identity Services (popup flow) + 2FA OTP |
| Infra | Docker Compose, Nginx (reverse proxy + TLS), Let's Encrypt |

---

## 3. Folder Structure

```
.
├── backend/
│   ├── app/
│   │   ├── core/                   # Cross-cutting concerns
│   │   │   ├── config.py           # Settings (pydantic-settings)
│   │   │   ├── database.py         # Async engine, session factory, Base
│   │   │   ├── redis.py            # Redis connection pool & health check
│   │   │   ├── security.py         # Password hashing (pwdlib+bcrypt), JWT
│   │   │   ├── rate_limit.py       # Sliding-window rate limiter (Redis)
│   │   │   ├── storage.py          # StorageProvider ABC + Local/S3 implementations
│   │   │   ├── email.py            # EmailProvider ABC + SMTP/Brevo implementations
│   │   │   ├── providers.py        # Factory functions for storage & email
│   │   │   ├── websocket_manager.py# Global WebSocket room/broadcast manager
│   │   │   ├── middleware.py       # CORS, request logging, timing headers
│   │   │   └── logger.py
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── meetings.py
│   │   │   ├── tasks.py
│   │   │   ├── notes.py
│   │   │   ├── calender.py
│   │   │   ├── whiteboard.py
│   │   │   ├── reminders.py
│   │   │   ├── attachment.py
│   │   │   ├── entity_link.py
│   │   │   ├── meeting_suggested_task.py
│   │   │   └── notification.py
│   │   ├── modules/                # Feature modules (vertical slices)
│   │   │   ├── auth/
│   │   │   ├── users/
│   │   │   ├── calender/
│   │   │   ├── notes/
│   │   │   ├── tasks/
│   │   │   ├── meetings/
│   │   │   ├── whiteboard/
│   │   │   ├── reminders/
│   │   │   ├── attachments/
│   │   │   ├── entity_links/
│   │   │   ├── ai_suggestions/
│   │   │   └── notifications/
│   │   ├── workers/
│   │   │   └── tasks.py            # Celery tasks (email, reminders, AI, push)
│   │   ├── utils/
│   │   │   └── tiptap_converter.py
│   │   └── main.py                 # FastAPI app factory, router inclusion, lifespan
│   ├── tests/
│   └── alembic/                    # DB migrations
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── features/               # Feature-based modules (mirrors backend)
│   │   │   ├── auth/
│   │   │   ├── meetings/
│   │   │   ├── tasks/
│   │   │   ├── notes/
│   │   │   ├── calendar/
│   │   │   ├── whiteboards/
│   │   │   ├── settings/
│   │   │   ├── dashboard/
│   │   │   ├── profile/
│   │   │   └── notifications/
│   │   ├── shared/                 # Shared components (RichTextEditor, etc.)
│   │   ├── components/             # shadcn/ui primitives
│   │   ├── context/                # AuthContext, ThemeContext, SidebarContext
│   │   ├── layouts/                # MainLayout, AuthLayout, Header, Sidebar
│   │   ├── lib/                    # axios client, queryClient, utils, timezone
│   │   └── routes/AppRoutes.jsx
│   ├── index.css
│   ├── main.jsx
│   └── vite.config.js
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 4. Backend Architecture

### 4.1 Repository Pattern

Each module follows a **three-layer architecture**:

```mermaid
flowchart LR
    subgraph Controller["Controller Layer"]
        C["*Controller classes"]
    end
    subgraph Service["Service Layer"]
        S["*Service classes"]
    end
    subgraph Repository["Repository Layer"]
        R["*Repository classes"]
    end
    subgraph DB["PostgreSQL"]
        M["SQLAlchemy Models"]
    end

    C --> S
    S --> R
    R --> M
    M --> DB
```

**Repository** (`app.modules.<module>.repository`):
- Encapsulates all SQLAlchemy queries.
- Receives an `AsyncSession` in `__init__`.
- Returns ORM objects or raw tuples (for analytical queries).
- No business logic — only persistence concerns.

**Service** (`app.modules.<module>.service`):
- Orchestrates business rules.
- Calls one or more repositories.
- Invokes core providers (storage, email, AI).
- Raises domain exceptions (`*NotFoundException`, `*AccessDeniedException`, `*ValidationError`).

**Controller** (`app.modules.<module>.controller`):
- Thin adapter between FastAPI routes and the service layer.
- Validates inputs via Pydantic schemas.
- Maps domain exceptions to HTTP responses (`404`, `403`, `400`, `422`).
- Returns validated response DTOs (`model_validate`).

### 4.2 Dependency Injection

FastAPI’s `Depends` is the primary DI mechanism. Dependencies are defined in `app.modules.<module>.dependencies`:

- `get_db` — yields an `AsyncSession`.
- `get_current_user_id` — extracts and validates the authenticated user.
- `get_optional_user_id` — same, but allows anonymous access (guests).
- `get_redis_client` — yields a Redis connection from the global pool.
- Module-specific providers, e.g. `get_meetings_service`, `get_attachment_service`.

Services are instantiated per-request in dependencies, receiving repositories and core services:

```python
# Example: app.modules.meetings.dependencies.py
async def get_meetings_service(db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis_client)):
    repo = MeetingRepository(db)
    storage = get_storage_service("meetings")
    session_service = MeetingSessionService(
        MeetingSessionRepository(db), redis, meeting_repo=repo
    )
    auth_service = SessionAuthorizationService(...)
    return MeetingService(repo, storage, session_service, auth_service)
```

### 4.3 Controller Layer

Controllers are pure functions that delegate to services. Example:

```python
class MeetingController:
    def __init__(self, service: MeetingService):
        self.service = service

    async def create_meeting(self, host_id: UUID, payload: MeetingCreate) -> dict:
        meeting = await self.service.create_meeting(host_id, payload)
        return MeetingResponse.model_validate(meeting)
```

Routes in `app.modules.<module>.routes` instantiate controllers or accept them via dependency injection:

```python
@router.post("/", status_code=201, response_model=MeetingResponse)
async def create_meeting_endpoint(
    payload: MeetingCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    service = Depends(get_meetings_service)
):
    ctrl = MeetingController(service)
    return await ctrl.create_meeting(current_user_id, payload)
```

---

## 5. Frontend Architecture

### 5.1 Feature-First Structure

```mermaid
flowchart TD
    App --> Routes
    Routes --> Layouts
    Layouts --> Features
    Features --> Hooks["use*Api.js (React Query)"]
    Features --> Components["UI Components"]
    Features --> Utils["utils.js"]
    Hooks --> Axios["axios.js (interceptors)"]
    Axios --> Backend["/api/v1"]
```

### 5.2 Authentication Flow (Frontend)

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Axios
    participant Backend

    User->>Frontend: Enter credentials / Google OAuth
    Frontend->>Backend: POST /api/v1/auth/login or /auth/google
    Backend-->>Frontend: { access_token, refresh_token }
    Frontend->>Frontend: Store tokens in localStorage
    Frontend->>Backend: GET /api/v1/users/profile (with access_token)
    Backend-->>Frontend: { user }
    Frontend->>Frontend: Set AuthContext user

    Note over Frontend,Axios: On subsequent requests
    Frontend->>Axios: API call with access_token
    Axios-->>Frontend: 401 Unauthorized
    Axios->>Backend: POST /api/v1/auth/refresh (refresh_token)
    Backend-->>Axios: { access_token, refresh_token }
    Axios->>Axios: Retry original request
```

### 5.3 Guest Session (Meeting)

Non-authenticated users can join meetings as guests via a link (`/m/:meetingCode`). The frontend stores guest identity in `sessionStorage` and passes it to the WebSocket connection.

---

## 6. Core Infrastructure

### 6.1 Database

```mermaid
flowchart LR
    App["FastAPI / Celery"] --> Engine["AsyncEngine (asyncpg)"]
    Engine --> Session["AsyncSessionLocal"]
    Session --> DB[(PostgreSQL 16)]
```

- `engine` — `create_async_engine` with `pool_pre_ping=True`.
- `AsyncSessionLocal` — `async_sessionmaker` with `expire_on_commit=False`.
- `Base` — `declarative_base()` for all ORM models.
- `get_db` — FastAPI dependency yielding `AsyncSession`, auto-commit/rollback.

### 6.2 Redis

```mermaid
flowchart LR
    subgraph App
        API["FastAPI"]
        Celery["Celery Workers"]
    end
    API --> Pool["ConnectionPool (db=1)"]
    Celery --> CeleryBroker["Celery Broker (db=0)"]
    Pool --> Redis[(Redis 7)]
    CeleryBroker --> Redis
```

Redis is used for:
- **Session tokens** (`session:{user_id}`) — refresh token whitelisting.
- **OTP / Reset tokens** (`otp:signup:`, `otp:login:`, `reset:`) — short-lived auth flows.
- **Rate limiting** — sliding window counters per endpoint/IP/user.
- **Meeting live state** (`meeting:{meeting_id}`) — active session ID cache.
- **Celery broker** — task queue backend.

### 6.3 Security

```mermaid
flowchart LR
    Input["Password / Token"] --> Hash["SecurityEngine"]
    Hash --> Bcrypt["pwdlib + BcryptHasher"]
    Hash --> JWT["JWT (HS256)"]
    JWT --> Access["Access Token (15 min)"]
    JWT --> Refresh["Refresh Token (7 days)"]
    Refresh --> Whitelist["Redis: session:{user_id}"]
```

- Passwords are hashed with **bcrypt** via `pwdlib`.
- JWTs carry `sub` (user_id) and `email`.
- Refresh tokens are whitelisted in Redis; password change or account deactivation revokes them.
- 2FA OTPs are 6-digit codes stored in Redis with TTL.

### 6.4 Rate Limiting

```mermaid
flowchart LR
    Request["Incoming Request"] --> Auth{"Bearer Token?"}
    Auth -->|Yes| UserID["Extract user_id"]
    Auth -->|No| IP["Use client IP"]
    UserID --> Key["rate_limit:{endpoint}:user:{id}"]
    IP --> Key
    Key --> Redis["Redis Sorted Set (sliding window)"]
    Redis --> Check{"count < limit?"}
    Check -->|Yes| Allow["Allow + record request"]
    Check -->|No| Reject["HTTP 429 Too Many Requests"]
```

Implemented in `app.core.rate_limit.RateLimiter`:
- Uses a Redis sorted set with timestamps as scores.
- Atomic pipeline operations (`zremrangebyscore`, `zcard`, `zadd`).
- Falls open (logs error) if Redis is unavailable.

### 6.5 Provider Architecture

```mermaid
flowchart TD
    subgraph "Factory"
        get_storage_provider
        get_email_provider
    end

    subgraph "Storage"
        StorageProviderABC["StorageProvider (ABC)"]
        LocalStorage["LocalStorageProvider"]
        S3Storage["S3StorageProvider"]
        StorageService["StorageService (validates + delegates)"]
    end

    subgraph "Email"
        EmailProviderABC["EmailProvider (ABC)"]
        SMTP["SMTPEmailProvider"]
        Brevo["BrevoEmailProvider"]
    end

    get_storage_provider -->|LOCAL| LocalStorage
    get_storage_provider -->|PRODUCTION| S3Storage
    LocalStorage --> StorageProviderABC
    S3Storage --> StorageProviderABC
    StorageService --> StorageProviderABC

    get_email_provider -->|LOCAL| SMTP
    get_email_provider -->|PRODUCTION| Brevo
    SMTP --> EmailProviderABC
    Brevo --> EmailProviderABC
```

- **Storage**: `LocalStorageProvider` writes to `STORAGE_BASE_DIR`; `S3StorageProvider` uses `aioboto3`.
- **Email**: `SMTPEmailProvider` uses Python `smtplib`; `BrevoEmailProvider` uses `brevo` SDK.
- Selection is based on `settings.ENVIRONMENT`.

---

## 7. Docker Architecture

```mermaid
flowchart TB
    Browser["Browser"] -->|"HTTPS :443"| Nginx

    subgraph "Nginx Container (saas_frontend)"
        Nginx["nginx :80/:443"]
        React["React SPA (static)"]
        Nginx --> React
    end

    Nginx -->|"/api/*"| Backend
    Nginx -->|"/ws/*"| Backend

    subgraph "Backend Container (saas_backend)"
        Backend["FastAPI + Uvicorn :8000"]
    end

    subgraph "Celery Container (saas_celery)"
        Celery["Celery Worker + Beat"]
    end

    subgraph "Data Tier"
        Postgres[("PostgreSQL 16")]
        Redis[("Redis 7.2")]
    end

    Backend --> Postgres
    Backend --> Redis
    Celery --> Postgres
    Celery --> Redis

    style Nginx fill:#059669,color:#fff
    style Backend fill:#2563eb,color:#fff
    style Celery fill:#7c3aed,color:#fff
    style Postgres fill:#dc2626,color:#fff
    style Redis fill:#ea580c,color:#fff
```

**Services**:
- `frontend` — React SPA served by Nginx with TLS termination. Reverse-proxies `/api/` and `/ws/` to the backend. Depends on backend health.
- `backend` — FastAPI + Uvicorn with dynamic worker count. Mounts `logs_data` and `uploads_data` volumes.
- `celery` — Shares the backend image; runs `celery_entrypoint.sh` for Beat + Worker.
- `postgres` — Primary data store with persistent volume.
- `redis` — Cache + Celery broker with AOF persistence.
- `mailpit` — SMTP catcher for local development (opt-in via `--profile local`).

---

## 8. Database Entities and Relationships

```mermaid
erDiagram
    User ||--o{ Task : "owns"
    User ||--o{ Note : "owns"
    User ||--o{ CalendarEvent : "owns"
    User ||--o{ Whiteboard : "owns"
    User ||--o{ Meeting : "hosts"
    User ||--o{ MeetingSession : "hosts"
    User ||--o{ UserReminderSetting : "has"
    User ||--o{ Notification : "receives"
    User ||--o{ NotificationSubscription : "subscribes"
    User ||--o{ MeetingInvitation : "invited as"

    Meeting ||--o{ MeetingSession : "has"
    Meeting ||--o{ MeetingInvitation : "has"
    MeetingSession ||--o{ MeetingParticipant : "has"
    MeetingSession ||--o{ MeetingRecording : "has"
    MeetingSession ||--o{ MeetingTranscript : "has"
    MeetingSession ||--o{ MeetingAIAnalysis : "has"
    MeetingAIAnalysis ||--o{ MeetingSuggestedTask : "generates"
    MeetingSuggestedTask }o--|| Task : "creates"

    Task ||--o{ TaskHistory : "audits"
    Task ||--o{ EntityLink : "source/target"
    Meeting ||--o{ EntityLink : "source/target"
    MeetingSession ||--o{ EntityLink : "source/target"
    Attachment ||--o{ EntityLink : "attached to"

    Attachment {
        UUID id
        UUID owner_user_id
        enum entity_type
        UUID entity_id
        string original_filename
        string stored_filename
        string content_type
        string extension
        int size
        string storage_provider
        string storage_path
        datetime created_at
    }

    EntityLink {
        UUID id
        string source_type
        UUID source_id
        string target_type
        UUID target_id
        string link_type
        enum relation_origin
        UUID created_by
        datetime created_at
        datetime deleted_at
    }
```

### 8.1 Entity Summary

| Model | Table | Key Fields |
|-------|-------|-----------|
| `User` | `users` | `id`, `email`, `password_hash`, `full_name`, `is_verified`, `is_2fa_enabled`, `timezone`, `google_id`, `oauth_provider` |
| `Task` | `tasks` | `id`, `user_id`, `title`, `description` (JSONB), `status`, `priority`, `due_date`, `labels` (JSONB), `checklist` (JSONB), `is_pinned`, `is_archived` |
| `TaskHistory` | `task_history` | `id`, `task_id`, `user_id`, `action`, `field_name`, `old_value`, `new_value` |
| `Note` | `notes` | `id`, `user_id`, `title`, `content`, `category`, `tags` (JSONB), `is_pinned`, `is_archived` |
| `CalendarEvent` | `calendar_events` | `id`, `user_id`, `title`, `event_type`, `color`, `start_time`, `end_time`, `timezone`, `is_all_day`, `recurrence_*` |
| `Whiteboard` | `whiteboards` | `id`, `user_id`, `title`, `board_data` (JSONB), `is_favorite`, `is_archived`, `is_deleted` |
| `Meeting` | `meetings` | `id`, `host_id`, `title`, `meeting_code`, `meeting_link`, `status`, `meeting_type`, `scheduled_start`, `timezone`, `agenda`, `enable_recording`, `enable_transcript`, `enable_ai_analysis` |
| `MeetingSession` | `meeting_sessions` | `id`, `meeting_id`, `host_id`, `status`, `started_at`, `ended_at`, `duration_seconds` |
| `MeetingParticipant` | `meeting_participants` | `id`, `session_id`, `user_id` (nullable), `guest_name`, `guest_email`, `participant_type`, `status`, `is_muted`, `can_start_screen_share`, `joined_at`, `left_at` |
| `MeetingRecording` | `meeting_recordings` | `id`, `session_id`, `filename`, `content_type`, `size`, `duration`, `storage_path` |
| `MeetingTranscript` | `meeting_transcripts` | `id`, `session_id`, `filename`, `content_type`, `size`, `storage_path` |
| `MeetingAIAnalysis` | `meeting_ai_analysis` | `id`, `session_id`, `provider`, `model`, `status`, `summary`, `agenda_coverage_percentage`, `covered_points` (JSON), `out_of_agenda_points` (JSON), `suggested_tasks` (JSON), `raw_response` (JSON) |
| `MeetingSuggestedTask` | `meeting_suggested_tasks` | `id`, `analysis_id`, `title`, `description`, `priority`, `status`, `created_task_id` |
| `MeetingInvitation` | `meeting_invitations` | `id`, `meeting_id`, `name`, `email` |
| `UserReminderSetting` | `user_reminder_settings` | `id`, `user_id`, `reminders_enabled`, `schedule_all`, `global_frequency`, `global_time`, `calendar_config` (JSON), `tasks_config` (JSON), `meetings_config` (JSON) |
| `Notification` | `notifications` | `id`, `user_id`, `type`, `title`, `body`, `extra_data` (JSONB), `is_read`, `sent_at` |
| `NotificationSubscription` | `notification_subscriptions` | `id`, `user_id`, `endpoint`, `p256dh`, `auth`, `browser` |
| `Attachment` | `attachments` | Generic polymorphic attachment owned by any entity via `entity_type` + `entity_id`. |
| `EntityLink` | `entity_links` | Generic relationship between any two entities. |

---

## 9. Meeting Session Engine

```mermaid
flowchart LR
    subgraph "Lifecycle"
        Created["CREATED"] --> Scheduled["SCHEDULED"]
        Created --> Active["ACTIVE"]
        Scheduled --> Active
        Active --> Idle["IDLE"]
        Idle --> Active
        Active --> Ended["ENDED"]
        Active --> Cancelled["CANCELLED"]
    end

    subgraph "Participant States"
        Waiting["WAITING"] --> Admitted["ADMITTED"]
        Admitted --> Left["LEFT"]
        Waiting --> Rejected["REJECTED"]
        Admitted --> Removed["REMOVED"]
    end
```

### 9.1 Meeting Lifecycle

1. **Creation** — Host creates an instant or scheduled meeting. Scheduled meetings store `scheduled_start`, `timezone`, and `agenda`.
2. **Invitation** — For scheduled meetings, hosts invite participants by email. Celery Beat checks upcoming meetings every minute and sends push notifications. Emails are sent asynchronously via Celery.
3. **Joining** — Users join via `/api/v1/meetings/{id}/join` or WebSocket. Registered users are auto-admitted as host; guests and non-host users enter `WAITING`.
4. **Waiting Room** — Host admits/rejects/removes participants via REST endpoints, which broadcast WebSocket events.
5. **Active Session** — First admit creates a `MeetingSession`. Subsequent joins reuse the active session. Screen sharing is tracked via `active_screen_sharer_id`.
6. **Ending** — Host ends the meeting. Active session finishes, recordings/transcripts are processed, and the completion pipeline is triggered.
7. **Completion** — Celery worker reads transcripts, runs AI analysis, creates suggested tasks, and sends completion email.

### 9.2 Meeting Session Lifecycle

```mermaid
stateDiagram-v2
    [*] --> ACTIVE: Host admits first participant
    ACTIVE --> ENDED: Host ends meeting
    ACTIVE --> CANCELLED: Host cancels before end

    note right of ACTIVE
        - Redis key "meeting:{id}" holds session_id
        - Participants join/leave via WebSocket
        - Recordings & transcripts uploaded
    end note

    note right of ENDED
        - Celery pipeline triggered
        - AI analysis on transcript
        - Completion email sent
    end note
```

### 9.3 WebSocket Signaling

The WebSocket router (`app.modules.meetings.websocket`) handles real-time signaling at `/ws/meetings/{meeting_id}`.

```mermaid
sequenceDiagram
    participant Client
    participant WS as WebSocket Endpoint
    participant Service as MeetingService
    participant Redis
    participant Room as ConnectionManager

    Client->>WS: Connect (token + guest info)
    WS->>Service: join_meeting_flow()
    Service->>Redis: Check/set active session
    Service-->>WS: Participant created
    WS->>Room: connect(room_id, connection_id, ws, metadata)
    WS-->>Client: PARTICIPANT_JOINED / PARTICIPANT_WAITING

    loop Poll + Receive
        WS->>Service: get_participant_by_id()
        alt status changed
            WS-->>Client: PARTICIPANT_ADMITTED / MUTE_CHANGED
        end
        Client->>WS: offer / ice-candidate / self_mute / screen_share_*
        WS->>Room: broadcast / send_personal
    end

    Client-->>WS: Disconnect
    WS->>Room: disconnect()
    WS->>Service: leave_meeting_flow()
    WS->>Room: broadcast PARTICIPANT_LEFT
```

---

## 10. Attachment Upload Flow

```mermaid
flowchart TD
    Client["Frontend (UploadFile)"] --> Route["POST /meetings/{id}/sessions/{session_id}/attachments"]
    Route --> Verify["_verify_session_access()"]
    Verify --> Service["AttachmentService.upload()"]
    Service --> Sanitize["_sanitise_filename()"]
    Service --> Read["Read file content"]
    Service --> Storage["StorageService.save_attachment()"]
    Storage --> Validate["validate_uploaded_file()<br/>- size check<br/>- extension check<br/>- MIME detection (python-magic)"]
    Validate --> Provider["StorageProvider.save_to_path()"]
    Provider -->|Local| LocalDisk["Write to base_dir/entity_type/entity_id/"]
    Provider -->|S3| S3["aioboto3 put_object"]
    Service --> Repo["AttachmentRepository.create()"]
    Repo --> DB[(PostgreSQL)]
```

---

## 11. AI Analysis Flow

```mermaid
flowchart TD
    EndMeeting["Host ends meeting"] --> Trigger["_trigger_completion_pipeline()"]
    Trigger --> Celery["analyze_meeting_transcript.delay(session_id)"]
    Celery --> Worker["Celery Worker"]
    Worker --> ReadTx["Read transcript file from Storage"]
    ReadTx --> Preprocess["preprocess_transcript()"]
    Preprocess --> AI["AIProviderService.generate_transcript_analysis()"]
    AI --> NIM["NVIDIA NIM API (Llama 3.3 70B)"]
    NIM --> Parse["Parse JSON response"]
    Parse --> Status["Update analysis status = PROCESSING"]
    Status --> Save["Persist summary, coverage, suggested_tasks"]
    Save --> BulkCreate["AISuggestionRepository.bulk_create()"]
    BulkCreate --> Email["MeetingCompletionService.send_completion_email()"]
```

```mermaid
sequenceDiagram
    participant Host
    participant API as FastAPI
    participant Redis
    participant Celery
    participant Storage
    participant NIM as NVIDIA NIM
    participant DB

    Host->>API: POST /meetings/{id}/end
    API->>Redis: Clear meeting state
    API->>Celery: delay(analyze_meeting_transcript, session_id)
    API-->>Host: Meeting ENDED

    Celery->>DB: Load meeting, session, transcripts
    Celery->>Storage: Read transcript file
    Celery->>NIM: POST /chat/completions (agenda + transcript)
    NIM-->>Celery: JSON { summary, coverage, suggested_tasks }
    Celery->>DB: Update MeetingAIAnalysis (status=COMPLETED)
    Celery->>DB: Bulk create MeetingSuggestedTask records
    Celery->>Storage: Read recording
    Celery->>Host: Send completion email with attachments
```

---

## 12. Authentication Flow

```mermaid
flowchart TD
    subgraph "Registration"
        Signup["POST /auth/signup"] --> CreateUser["Create User (unverified)"]
        CreateUser --> GenOTP["Generate 6-digit OTP"]
        GenOTP --> StoreOTP["Redis: otp:signup:{token} = {email, otp}"]
        StoreOTP --> SendEmail["Celery: send_async_email(OTP)"]
        SendEmail --> Verify["POST /auth/verify-signup"]
        Verify --> ValidateOTP["Validate OTP in Redis"]
        ValidateOTP --> MarkVerified["Mark user is_verified=True"]
        MarkVerified --> IssueTokens["Issue JWT + store refresh in Redis"]
    end

    subgraph "Login"
        Login["POST /auth/login"] --> CheckPwd["Verify password"]
        CheckPwd -->|2FA enabled| GenLoginOTP["Generate 6-digit OTP"]
        GenLoginOTP --> StoreLoginOTP["Redis: otp:login:{token}"]
        StoreLoginOTP --> SendLoginEmail["Celery: send_async_email(OTP)"]
        SendLoginEmail --> VerifyLogin["POST /auth/verify-login"]
        VerifyLogin --> ValidateLoginOTP["Validate OTP"]
        ValidateLoginOTP --> IssueLoginTokens["Issue JWT + store refresh in Redis"]
        CheckPwd -->|No 2FA| IssueLoginTokens
    end

    subgraph "Google OAuth"
        Google["POST /auth/google"] --> VerifyToken["google.oauth2.id_token.verify_oauth2_token"]
        VerifyToken --> FindUser["Find by google_id or email"]
        FindUser -->|Exists| Check2FA
        FindUser -->|New| CreateOAuthUser["Create OAuth-only user"]
        CreateOAuthUser --> Check2FA{"2FA enabled?"}
        Check2FA -->|Yes| GenLoginOTP
        Check2FA -->|No| IssueGoogleTokens["Issue JWT + store refresh in Redis"]
    end

    subgraph "Token Refresh"
        Refresh["POST /auth/refresh"] --> DecodeRefresh["Decode refresh token"]
        DecodeRefresh --> CheckWhitelist["Redis: session:{user_id}"]
        CheckWhitelist -->|Match| RotateTokens["Issue new JWT pair"]
        CheckWhitelist -->|Mismatch| Reject["401 Unauthorized"]
    end
```

---

## 13. Task Flow

```mermaid
flowchart LR
    Create["POST /api/v1/tasks"] --> Validate["TaskCreate schema"]
    Validate --> Service["TaskService.create_task()"]
    Service --> Repo["TaskRepository.create()"]
    Repo --> DB[(PostgreSQL)]

    Update["PATCH /api/v1/tasks/{id}"] --> UpdateService["TaskService.update_task()"]
    UpdateService --> History["TaskHistoryRepository.create()"]
    UpdateService --> Repo

    AI["AI Analysis completes"] --> Suggestion["MeetingSuggestedTask created"]
    Suggestion --> Convert["POST /api/v1/ai-suggestions/{id}/create-task"]
    Convert --> Create
```

---

## 14. Relation Flow

```mermaid
flowchart LR
    Create["POST /api/v1/entity-links"] --> Validate["Validate source/target entity access"]
    Validate --> Service["EntityLinkService.create_link()"]
    Service --> Repo["EntityLinkRepository.create()"]
    Repo --> DB[(PostgreSQL)]

    GetLinkedTasks["GET /api/v1/entity-links/tasks?meeting_id={id}"] --> Query["Query EntityLink + Task joins"]
    Query --> Filter["Filter by user ownership"]
    Filter --> Return["Return linked tasks"]

    GetLinkedMeetings["GET /api/v1/entity-links/meetings?task_id={id}"] --> Query2["Query EntityLink + Meeting joins"]
    Query2 --> Filter2["Filter by user ownership"]
    Filter2 --> Return2["Return linked meetings/sessions"]
```

---

## 15. Dashboard

The dashboard (`/dashboard`) is a feature module that aggregates data from all other modules:
- Upcoming calendar events.
- Pending tasks with due dates.
- Recent meetings and upcoming scheduled meetings.
- Recent AI analyses.
- Unread notifications.

It uses React Query for parallel data fetching and aggregates results client-side.

---

## 16. Security Summary

| Mechanism | Implementation |
|-----------|---------------|
| Authentication | JWT (HS256) — 15 min access, 7 day refresh |
| Session Management | Redis whitelist (`session:{user_id}`) — revoked on password change / deactivation |
| Password Hashing | `pwdlib` + `BcryptHasher` |
| 2FA | 6-digit OTP via email, stored in Redis with TTL |
| OAuth | Google Identity Services — popup flow, ID token verified server-side with `google.oauth2.id_token.verify_oauth2_token` |
| Authorization | Per-module checks (host-only, participant-only, owner-only) |
| Rate Limiting | Redis sliding window per endpoint/IP/user |
| CORS | `allow_origins=["*"]` with credentials (intended for nginx reverse proxy in production) |
| File Upload Validation | Extension allowlist + MIME detection (`python-magic`) + size limit |

---

## 17. Celery Tasks

| Task Name | Schedule | Description |
|-----------|----------|-------------|
| `tasks.process_all_reminders` | Every 30 min | Scans upcoming meetings, calendar events, and tasks; sends email reminders based on user preferences. |
| `tasks.send_meeting_push_reminders` | Every 60s | Finds scheduled meetings starting within 10 minutes and sends browser push notifications + in-app notifications. |
| `tasks.analyze_meeting_transcript` | On-demand (triggered on meeting end) | Reads transcript, runs NVIDIA NIM AI analysis, persists results, creates suggested tasks, sends completion email. |
| `tasks.send_async_email` | On-demand | Sends plain-text email via SMTP/Brevo with autoretry. |
| `tasks.send_html_email` | On-demand | Sends HTML email with optional attachments via SMTP/Brevo with autoretry. |

---

## 18. Summary

| Concern | Detail |
|---------|--------|
| **Pattern** | Repository → Service → Controller (vertical slice modules) |
| **DB Access** | SQLAlchemy 2.0 async, `AsyncSession` per request |
| **Real-time** | WebSocket signaling + WebRTC mesh (browser-native) |
| **Background** | Celery + Redis broker + Beat scheduler |
| **Storage** | Strategy pattern (Local vs S3), validated uploads |
| **Email** | Strategy pattern (SMTP vs Brevo), async via Celery |
| **Auth** | JWT + Google Identity Services + Redis session whitelist + 2FA OTP |
| **AI** | NVIDIA NIM (Llama 3.3 70B), triggered by Celery on meeting end |
| **Rate Limiting** | Redis sliding window, fails open |
| **Frontend** | React Query for server state, Axios interceptors for token refresh, feature-first organization |
| **Deployment** | Docker Compose, Nginx reverse proxy with TLS, Let's Encrypt, DuckDNS |
