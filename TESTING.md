# Testing Overview

This document describes the backend test suite for the Productivity Suite application. It covers how tests are organized, what is tested, how to execute them, and what is mocked. Frontend testing is intentionally lightweight.

---

## Testing Approach

### Backend-First Strategy

The application follows a **backend-first testing strategy**. The vast majority of automated tests target the Python FastAPI backend. Business logic, data integrity, security rules, and integration boundaries are all enforced through backend unit and integration tests.

### Why Backend Has Comprehensive Coverage

- The backend contains all domain logic, validation, authorization, and persistence code.
- Backend code is deterministic and testable without browsers or external services.
- The layered architecture (Repository → Service → Controller → Routes) maps cleanly to unit-test boundaries.
- Core infrastructure (security, storage, email, Redis, WebSockets) is tested in isolation.

### Why Frontend Testing is Intentionally Lightweight

- The frontend is a thin React consumer of the backend API.
- UI state is managed through React Query and context providers that are straightforward to reason about.
- Component behavior is largely driven by backend responses; if the backend is well-tested, frontend logic is reduced to data-binding and event wiring.
- There is no dedicated frontend test suite. Any frontend verification is performed manually or through integration testing.

---

## Testing Stack

| Tool | Purpose |
|------|---------|
| **pytest** | Test runner and discovery |
| **pytest-asyncio** | Async test support (`asyncio_mode = auto`) |
| **pytest-cov** | Coverage reporting (when invoked) |
| **httpx / TestClient** | FastAPI route integration testing |
| **unittest.mock** | Mocking framework (`AsyncMock`, `MagicMock`, `patch`) |

No factory libraries (e.g., Factory Boy) are used. Test data is constructed inline using `MagicMock`, `AsyncMock`, and direct model instantiation.

---

## Test Architecture

### Folder Structure

```
backend/tests/
├── conftest.py                          # Root fixtures (mock_db, mock_redis, test_user, etc.)
├── test_main.py                         # Application startup tests
├── core/                                # Core infrastructure tests
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_redis.py
│   ├── test_security.py
│   ├── test_storage.py
│   ├── test_email.py
│   ├── test_providers.py
│   └── test_websocket_manager.py
├── models/                              # ORM model unit tests
│   ├── test_user.py
│   ├── test_meetings.py
│   ├── test_tasks.py
│   ├── test_notes.py
│   ├── test_calender.py
│   ├── test_whiteboard.py
│   ├── test_attachment.py
│   └── test_meeting_suggested_task.py
├── workers/                             # Celery task tests
│   └── test_tasks.py
├── utils/                               # Utility tests
│   └── test_tiptap_converter.py
└── modules/                             # Feature module tests (mirrors app/modules/)
    ├── auth/
    │   ├── test_schemas.py
    │   ├── test_routes.py
    │   ├── test_service.py
    │   ├── test_repository.py
    │   ├── test_dependencies.py
    │   └── test_controller.py
    ├── users/
    │   ├── test_schemas.py
    │   ├── test_routes.py
    │   ├── test_service.py
    │   ├── test_repository.py
    │   ├── test_dependencies.py
    │   └── test_controller.py
    ├── calender/
    │   ├── test_schema.py
    │   ├── test_routes.py
    │   ├── test_service.py
    │   ├── test_repository.py
    │   ├── test_recurrence.py
    │   ├── test_exceptions.py
    │   ├── test_enums.py
    │   ├── test_dependencies.py
    │   └── test_controller.py
    ├── notes/
    │   ├── test_schemas.py
    │   ├── test_routes.py
    │   ├── test_services.py
    │   ├── test_repository.py
    │   ├── test_exceptions.py
    │   ├── test_dependencies.py
    │   └── test_controller.py
    ├── tasks/
    │   ├── test_schemas.py
    │   ├── test_routes.py
    │   ├── test_services.py
    │   ├── test_repository.py
    │   ├── test_exceptions.py
    │   ├── test_enums.py
    │   ├── test_dependencies.py
    │   └── test_controller.py
    ├── meetings/
    │   ├── test_schemas.py
    │   ├── test_routes.py
    │   ├── test_service.py
    │   ├── test_repository.py
    │   ├── test_websocket.py
    │   ├── test_transcript_preprocessor.py
    │   ├── test_exceptions.py
    │   ├── test_enums.py
    │   ├── test_dependencies.py
    │   ├── test_controller.py
    │   ├── test_constants.py
    │   ├── test_completion_service.py
    │   ├── test_authorization.py
    │   └── test_ai_provider_service.py
    ├── whiteboard/
    │   ├── test_schemas.py
    │   ├── test_routes.py
    │   ├── test_service.py
    │   ├── test_repository.py
    │   ├── test_exceptions.py
    │   └── test_controller.py
    ├── reminders/
    │   ├── test_service.py
    │   ├── test_repository.py
    │   ├── test_notification_service.py
    │   └── __init__.py
    ├── attachments/
    │   ├── conftest.py
    │   ├── test_schemas.py
    │   ├── test_routes.py
    │   ├── test_service.py
    │   ├── test_repository.py
    │   ├── test_exceptions.py
    │   ├── test_enums.py
    │   ├── test_controller.py
    │   └── test_constants.py
    ├── entity_links/
    │   ├── test_services.py
    │   ├── test_schemas.py
    │   ├── test_routes.py
    │   ├── test_repository.py
    │   ├── test_exceptions.py
    │   ├── test_enums.py
    │   ├── test_dependencies.py
    │   └── test_controller.py
    └── notifications/
        ├── conftest.py
        ├── test_service.py
        ├── test_schemas.py
        ├── test_push_provider.py
        ├── test_enums.py
        ├── test_controller.py
        └── test_routes.py
```

### Test Layers

Tests mirror the application architecture in reverse order:

```
Routes
  ↓
Controller
  ↓
Service
  ↓
Repository
  ↓
Models / Database
```

Each layer is tested independently:

- **Routes**: Tested with FastAPI `TestClient` and dependency overrides. Service and repository layers are mocked so route tests verify HTTP status codes, request validation, and response shapes without touching the database.
- **Controllers**: Tested as thin adapters. Mocks verify that controllers call the correct service methods and map exceptions to the right HTTP responses.
- **Services**: Tested as pure business logic. Repositories and external providers are mocked. Tests verify state transitions, authorization rules, and orchestration logic.
- **Repositories**: Tested with mocked `AsyncSession`. SQLAlchemy queries are verified for correctness (filters, joins, ordering) without a real database.
- **Models**: Tested as plain Python classes. Table names, column defaults, and constructor behavior are verified.
- **Core**: Storage, email, security, Redis, WebSocket manager, and database helpers are tested in complete isolation from the network and filesystem.

### Fixture Reuse

Fixtures are defined at multiple levels:

- **Root `conftest.py`**: Provides `mock_db`, `mock_redis`, `mock_repo`, `mock_security`, `mock_service`, `mock_controller`, `test_user`, and `oauth_user`. These are shared across all module tests.
- **Module `conftest.py`**: Modules with complex setup (e.g., `notifications`, `attachments`) define local fixtures for sample IDs, payloads, and mock configurations.
- **Test-class fixtures**: Many test files define fixtures inside the test class (e.g., `repo`, `service`, `storage`) to keep test data local and readable.

Fixtures are designed to be **reusable but not global**. Each test file can override or extend fixtures without affecting other modules.

---

## Running Tests

### Run All Tests

```bash
cd backend
pytest
```

### Run One Module

```bash
pytest tests/modules/meetings/
```

### Run a Single Test File

```bash
pytest tests/modules/meetings/test_service.py
```

### Run a Single Test

```bash
pytest tests/modules/meetings/test_service.py::TestMeetingService::test_create_meeting
```

### Coverage

```bash
pytest --cov=app --cov-report=term-missing
```

Coverage is measured against the `app` package. Reports are printed to the terminal showing missing lines.

### Verbose Mode

```bash
pytest -v
```

### Fail Fast

```bash
pytest -x
```

### Configuration

`pytest.ini` at the backend root:

```ini
[pytest]
asyncio_mode = auto
pythonpath = .
addopts = --import-mode=importlib
filterwarnings =
    ignore::pydantic.warnings.PydanticDeprecatedSince20
```

- `asyncio_mode = auto`: All async tests run without explicit `@pytest.mark.asyncio`.
- `pythonpath = .`: Tests can import `app` directly.
- `--import-mode=importlib`: Prevents import conflicts with test module names.

---

## Coverage

Current backend coverage focuses on **business logic rather than framework internals**. The test suite exercises:

- **Service layer logic**: All state transitions, authorization checks, and orchestration paths.
- **Repository queries**: Filter construction, joins, ordering, and edge cases (soft deletes, nullable fields).
- **Controller exception mapping**: Verification that domain exceptions become correct HTTP responses.
- **Route validation**: Request body validation, query parameter handling, and dependency injection.
- **Core utilities**: Password hashing, JWT creation/verification, file validation, transcript preprocessing, WebSocket room management.
- **Celery tasks**: Task naming, retry configuration, and provider delegation.
- **Worker orchestration**: Reminder sweeps, AI analysis pipeline, completion email logic.

Areas with lower coverage are **infrastructure glue code** that is difficult to unit-test without a real database or external service:
- Alembic migration scripts
- Application lifespan/startup code
- Actual database connection pooling behavior
- Real network I/O (by design)

The project does not maintain a published coverage badge or minimum threshold in `pytest.ini`.

---

## Modules Covered

### Authentication

**Files:** `tests/modules/auth/test_schemas.py`, `test_routes.py`, `test_service.py`, `test_repository.py`, `test_dependencies.py`, `test_controller.py`

**What is tested:**
- Registration with OTP verification and resend
- Login with 2FA challenge and OTP verification
- Google OAuth token verification, account linking, and login
- Password reset initiation and confirmation
- Token refresh with Redis session whitelist
- Route-level HTTP status codes and response schemas
- Repository queries for email, Google ID, and user creation
- Dependency injection for current user extraction

### Dashboard

**Files:** `tests/modules/dashboard/` (integrated via route tests)

**What is tested:**
- Dashboard composition is not tested as a separate unit. Dashboard data is assembled from module-specific queries that are tested individually.

### Meetings

**Files:** `tests/modules/meetings/test_service.py`, `test_routes.py`, `test_repository.py`, `test_controller.py`, `test_websocket.py`, `test_authorization.py`, `test_completion_service.py`, `test_ai_provider_service.py`, `test_transcript_preprocessor.py`, `test_constants.py`, `test_enums.py`, `test_exceptions.py`, `test_schemas.py`, `test_dependencies.py`

**What is tested:**
- Meeting CRUD: create, update, list, end, cancel, delete
- Meeting status lifecycle transitions (CREATED → ACTIVE → IDLE → ENDED / CANCELLED)
- Join flow: instant vs scheduled, guest vs registered, waiting room, invitation validation
- Participant management: admit, reject, remove, mute, unmute
- Screen sharing: request, approve, reject, start, stop, force-stop
- Session management: active session creation, session history, session detail
- Recording and transcript upload, download, and deletion
- Meeting authorization: host-only checks, session access verification
- WebSocket signaling: connect/disconnect, join/leave events, waiting room admission, mute changes, screen share events, broadcast behavior, cleanup logic
- Completion service: session/meeting not found, no recipients, attachment inclusion
- AI provider: transcript analysis, JSON parsing, schema validation, empty/invalid responses
- Transcript preprocessor: whitespace normalization, speaker label preservation
- Constants and enums: URL formats, WS event types, status enums

### Meeting Sessions

**Files:** `tests/modules/meetings/test_service.py`, `test_repository.py`, `test_authorization.py`, `test_websocket.py`

**What is tested:**
- Session creation, retrieval, and update
- Session finishing with duration calculation
- Active session lookup via Redis and database fallback
- Redis state initialization and cleanup
- Session history access control (host sees all, participants see attended only)
- Session detail with participant summaries and artifact flags

### Tasks

**Files:** `tests/modules/tasks/test_services.py`, `test_routes.py`, `test_repository.py`, `test_controller.py`, `test_schemas.py`, `test_enums.py`, `test_exceptions.py`, `test_dependencies.py`

**What is tested:**
- Task CRUD with ownership checks
- Soft delete and restore
- Status workflow transitions (TODO → IN_PROGRESS → DONE)
- Priority and label management
- Checklist creation and updates
- Pin, favorite, archive operations
- Full-text search filtering
- Task history audit trail creation
- Linked meetings via entity links
- Schema validation for create/update payloads

### Calendar

**Files:** `tests/modules/calender/test_schema.py`, `test_routes.py`, `test_service.py`, `test_repository.py`, `test_recurrence.py`, `test_exceptions.py`, `test_enums.py`, `test_dependencies.py`, `test_controller.py`

**What is tested:**
- Event CRUD with timezone handling
- Recurrence engine: daily, weekly, monthly frequency expansion
- Event type and color enums
- Soft delete behavior
- Search and filter logic
- Route validation and response codes

### Notes

**Files:** `tests/modules/notes/test_services.py`, `test_routes.py`, `test_repository.py`, `test_schemas.py`, `test_exceptions.py`, `test_dependencies.py`, `test_controller.py`

**What is tested:**
- Note CRUD with ownership checks
- Category and tag management
- Pin, favorite, archive, soft delete, restore
- Full-text search on title and content
- Auto-save behavior
- Schema validation for create/update payloads

### Whiteboard

**Files:** `tests/modules/whiteboard/test_service.py`, `test_routes.py`, `test_repository.py`, `test_schemas.py`, `test_exceptions.py`, `test_controller.py`

**What is tested:**
- Board CRUD with ownership checks
- Favorite, archive, soft delete, restore
- Board data validation
- Search and filter logic
- Route response codes and dependency injection

### Attachments

**Files:** `tests/modules/attachments/test_service.py`, `test_routes.py`, `test_repository.py`, `test_schemas.py`, `test_exceptions.py`, `test_enums.py`, `test_controller.py`, `test_constants.py`, `conftest.py`

**What is tested:**
- Filename sanitization and extension extraction
- File upload flow with mocked storage
- Presigned upload and confirm flows
- Download response generation
- Attachment metadata and listing
- Entity-scoped attachment operations
- Permission checks (owner-only access)
- Bulk deletion for entity cleanup
- Route-level upload, download, list, and delete endpoints
- Allowed extensions, MIME types, and size constants

### Relations

**Files:** `tests/modules/entity_links/test_services.py`, `test_routes.py`, `test_repository.py`, `test_schemas.py`, `test_exceptions.py`, `test_enums.py`, `test_dependencies.py`, `test_controller.py`

**What is tested:**
- Link creation with self-link prevention
- Link retrieval and access control (creator-only)
- Link deletion and soft delete
- Linked tasks resolution for meetings (bidirectional)
- Linked meetings resolution for tasks (bidirectional)
- Linked tasks for sessions
- List and filter by source/target entity
- Schema validation for link creation

### AI Analysis

**Files:** `tests/modules/meetings/test_ai_provider_service.py`, `test_completion_service.py`

**What is tested:**
- AI provider request construction (model name, JSON mode, temperature, max tokens)
- Response parsing and schema validation
- Empty response and invalid JSON error handling
- Completion email orchestration: session/meeting not found, no recipients, attachment inclusion
- Analysis status transitions (PENDING → PROCESSING → COMPLETED / FAILED)

### Reminder Engine

**Files:** `tests/modules/reminders/test_service.py`, `test_repository.py`, `test_notification_service.py`

**What is tested:**
- User reminder settings retrieval and default creation
- Settings update with change detection
- Reminder preference snapshots
- Notification service delegation
- Repository queries for scheduled meetings, calendar events, and tasks

### Storage

**Files:** `tests/core/test_storage.py`

**What is tested:**
- `validate_uploaded_file`: empty content, oversize, invalid extension, valid files, MIME detection failures, MIME mismatches, case insensitivity
- `EXTENSION_TO_MIMES` map completeness (pdf, docx, etc.)
- `LocalStorageProvider` and `S3StorageProvider` are mocked; no real filesystem or S3 I/O occurs

### Provider Architecture

**Files:** `tests/core/test_providers.py`

**What is tested:**
- `get_storage_provider()` returns `LocalStorageProvider` in LOCAL environment
- `get_storage_provider()` returns `S3StorageProvider` in PRODUCTION environment
- `get_storage_service()` wraps provider correctly and passes subdirectory
- `get_email_provider()` returns `SMTPEmailProvider` in LOCAL
- `get_email_provider()` returns `BrevoEmailProvider` in PRODUCTION

### Security

**Files:** `tests/core/test_security.py`

**What is tested:**
- Password hashing: returns string, different hashes for same password, empty and long passwords
- Password verification: correct password, wrong password, empty password, invalid hash formats, None hash
- Token creation: returns string, contains payload, has expiration, expiration matches delta
- Auth tokens: generates access and refresh tokens with correct claims

### Rate Limiting

**Files:** (integrated in `tests/modules/auth/test_routes.py` and other route tests)

**What is tested:**
- Sliding-window logic via mocked Redis pipeline
- 429 responses when limit is exceeded
- Retry-After header calculation
- Fail-open behavior when Redis errors occur
- User identification from JWT vs IP fallback

### Redis

**Files:** `tests/core/test_redis.py`

**What is tested:**
- Connection pool initialization: DB index 1, `decode_responses=False`
- Health check success and failure paths
- `get_redis_client()` yields client and closes after use

### Celery

**Files:** `tests/workers/test_tasks.py`

**What is tested:**
- Task naming and retry configuration (`autoretry_for`, `max_retries`)
- `send_async_email`: delegates to email provider, propagates exceptions
- `send_html_email`: delegates with attachments
- `analyze_meeting_transcript`: mocked storage read, AI analysis delegation, completion email dispatch
- `process_all_reminders`: meeting, calendar, and task reminder orchestration
- `send_meeting_push_reminders`: meeting lookup, push notification dispatch, notification creation
- No real Celery broker or worker pool is started

---

## Mocked Services

No external APIs are contacted during test execution. All network, filesystem, and database I/O is mocked.

### AWS S3

- `S3StorageProvider` is never instantiated in tests. `get_storage_provider()` is patched to return a mock when testing S3 selection logic.
- `aioboto3` calls (`put_object`, `get_object`, `delete_object`, `generate_presigned_url`) are not executed.

### Brevo

- `BrevoEmailProvider` is never instantiated in tests. `get_email_provider()` is patched.
- The `brevo` SDK client is mocked; `send_transac_email` is never called.

### SMTP

- `SMTPEmailProvider` is tested with `smtplib.SMTP` patched. The mock verifies `sendmail`, `starttls`, and `login` calls without opening a real network connection.

### Google OAuth

- Google ID token verification is never executed in tests. `google.oauth2.id_token.verify_oauth2_token` is patched.
- OAuth flows are tested through `AuthService` with mocked repository and Redis.

### NVIDIA NIM

- `AIProviderService` is tested with the OpenAI-compatible client patched. `chat.completions.create` returns a mock completion.
- No HTTP request is made to `https://integrate.api.nvidia.com`.

### Redis

- `redis.asyncio.Redis` and `ConnectionPool` are patched in core tests.
- In service and route tests, `mock_redis` is an `AsyncMock` with no real connection.
- Pipeline operations (`zremrangebyscore`, `zcard`, `zadd`, `expire`) are mocked with `MagicMock` or `AsyncMock`.

### Celery

- Celery tasks are tested as plain functions. `celery_app` is imported but `delay()` and `apply_async()` are never called.
- The async loop inside tasks is mocked or bypassed.

### Filesystem

- File reads and writes are mocked. `aiofiles.open`, `os.path.getsize`, `os.remove`, `os.makedirs` are patched where needed.
- `python-magic` (`magic.from_buffer`) is patched in storage validation tests.

### Signed URLs

- Presigned URL generation is never executed. `S3StorageProvider.create_upload` and `get_download_response` are mocked or patched.

---

## Testing Philosophy

### Behaviour-Driven Testing

Tests verify **what the code does**, not **how it does it**. Assertions focus on outputs, side effects, and state changes rather than internal implementation details.

### Business Logic Over Implementation Details

- Service tests mock repositories and assert on business rules (e.g., "host can end meeting", "participant can only be admitted from waiting").
- Repository tests assert on query construction (filters, joins) without requiring a real database.
- Route tests assert on HTTP status codes and response bodies without exercising the database.

### Reusable Fixtures

Fixtures are small, composable, and overridable. Root fixtures provide common mocks; test-class fixtures provide module-specific data. This avoids duplication while keeping tests readable.

### Isolation

Each test is independent. No test relies on the side effects of another test. Fixtures are function-scoped by default. Database sessions, Redis connections, and external clients are all mocked.

### Deterministic Execution

Tests do not depend on wall-clock time, network availability, or external service state. Time-dependent logic uses fixed timestamps or is mocked. Retries and backoffs are tested by asserting on call counts, not by waiting.

---

## Future Testing

The following improvements naturally extend the existing strategy:

- **Coverage reporting in CI**: Add `pytest-cov` with a minimum threshold gate.
- **Contract tests for API routes**: Generate OpenAPI schema snapshots and diff them on each run.
- **Property-based testing**: Use `hypothesis` for input validation edge cases (e.g., filename sanitization, date recurrence expansion).
- **Performance regression tests**: Add timed assertions for high-traffic endpoints (meeting join, task list).
- **Frontend smoke tests**: Add Playwright or Cypress for critical user journeys (login, create meeting, join room).

No changes to production code or existing tests are required for these extensions.
