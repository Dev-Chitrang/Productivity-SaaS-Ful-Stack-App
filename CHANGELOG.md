# Changelog

All notable changes to this project are documented in this file.

This project follows Semantic Versioning.

## [1.0.0]

Initial Project Setup

### Added

- MIT License.

## [1.1.0]

Authentication & Users

### Added

- User registration, login, and logout.
- Forgot password and reset password flows.
- Google OAuth sign-in.
- JWT-based authentication with access and refresh tokens.
- User profile page with update capabilities.
- Application settings page.
- Landing page.
- Docker setup for backend services.
- Frontend project scaffolded with Vite, React, and shadcn/ui.
- Backend API scaffolded with FastAPI.
- Axios-based HTTP client with interceptors.
- React Query integration for server state management.
- Protected routing with authentication guards.

## [1.2.0]

Calendar

### Added

- Calendar with month, week, and day views.
- Event creation, editing, and deletion.
- Event detail dialog.
- Event recurrence configuration.
- Agenda list view.
- Calendar search and filter by type.
- Color-coded events.
- Light and dark theme toggle.
- Collapsible sidebar navigation.
- Backend calendar module with full CRUD API.
- Recurrence engine for event scheduling.

## [1.3.0]

Notes

### Added

- Rich text note editor with formatting toolbar.
- Note creation, editing, and deletion.
- Note list with search and filter by status.
- Pin and archive support for notes.
- Confirmation dialogs for destructive actions.
- Backend notes module with full CRUD API.

## [1.4.0]

Tasks

### Added

- Task creation, editing, and deletion.
- Rich text editor for task descriptions.
- Task filtering by status and priority.
- Task search.
- Activity timeline for task history.
- Shared rich text editor component (used by Notes and Tasks).
- Backend tasks module with full CRUD API.
- TipTap editor utilities.

## [1.5.0]

Audio Meetings

### Added

- Audio meetings with WebRTC-based real-time communication.
- Meeting room with participant management.
- Meeting creation, editing, and deletion.
- Join meeting via link or code.
- Guest session support without authentication.
- Screen sharing.
- Meeting recording with download.
- Live transcription panel.
- In-meeting chat.
- Waiting room with host approval.
- WebSocket manager for real-time events.
- Backend meetings module with file storage and WebSocket support.

## [1.6.0]

Whiteboard

### Added

- Digital whiteboard with freehand drawing tools.
- Shape, text, and image tools on the whiteboard.
- Whiteboard creation, editing, and deletion.
- Whiteboard list with search and filter.
- Sidebar collapse and expand on navigation.
- Project architecture and setup documentation (ARCHITECTURE.md, README.md).

## [1.6.1]

Notes, Tasks, and Dashboard Fixes

### Added

- Dashboard page with analytics overview for calendar, notes, and tasks.
- Today overview widget showing upcoming events and pending tasks.
- Module sidebar collapse on page navigation.

### Fixed

- Notes page pagination, filtering, and error handling.
- Tasks page pagination, filtering, and error handling.
- Whiteboard page loading states and error handling.
- Rich text editor toolbar responsiveness.
- Axios interceptor token refresh logic.

### Refactored

- Dashboard layout to display module-specific analytics cards.
