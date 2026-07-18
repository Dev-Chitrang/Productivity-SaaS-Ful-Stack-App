# API Reference

Complete HTTP endpoint reference for the Productivity App backend.

---

## Table of Contents

- [Overview](#overview)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [JWT Flow](#jwt-flow)
- [Error Response Format](#error-response-format)
- [Pagination](#pagination)
- [Filtering](#filtering)
- [Sorting](#sorting)
- [Status Codes](#status-codes)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
  - [Health](#health)
  - [Authentication](#authentication-1)
  - [Users](#users)
  - [Calendar](#calendar)
  - [Notes](#notes)
  - [Tasks](#tasks)
  - [Meetings](#meetings)
  - [Meeting Analysis](#meeting-analysis)
  - [Whiteboards](#whiteboards)
  - [Reminders](#reminders)
  - [Entity Links](#entity-links)
  - [AI Suggestions](#ai-suggestions)
  - [Notifications](#notifications)
  - [Attachments](#attachments)
  - [WebSocket](#websocket)

---

## Overview

RESTful JSON API built with FastAPI. All endpoints (except `/health` and WebSocket) are prefixed with `/api/v1`. The API uses JWT bearer tokens for authentication and Redis-backed sliding-window rate limiting.

---

## Base URL

```
https://<host>[:<port>]/api/v1
```

The health check endpoint is mounted at the root:

```
https://<host>[:<port>]/health
```

WebSocket connections use:

```
ws://<host>[:<port>]/ws/meetings/{meeting_id}
```

---

## Authentication

All protected endpoints require a valid JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are HS256-signed JSON Web Tokens containing:

| Claim | Description |
|-------|-------------|
| `sub` | User ID (UUID string) |
| `email` | User email address |
| `exp` | Token expiration (Unix timestamp) |

---

## JWT Flow

### Token Lifecycle

| Token | Lifetime | Secret |
|-------|----------|--------|
| Access Token | 15 minutes | `JWT_SECRET_KEY` |
| Refresh Token | 7 days | `JWT_REFRESH_SECRET_KEY` |

### Authentication Flow

1. **Register** — `POST /auth/signup` returns a `verification_token` and sends an OTP to the email.
2. **Verify Signup** — `POST /auth/verify-signup` with the OTP returns access and refresh tokens.
3. **Login** — `POST /auth/login` with email and password. If 2FA is enabled, returns a `verification_token`; otherwise returns tokens directly.
4. **Verify Login (2FA)** — `POST /auth/verify-login` with the OTP returns access and refresh tokens.
5. **Refresh** — `POST /auth/refresh` with a valid refresh token returns new access and refresh tokens.
6. **Google Identity Services** — `POST /auth/google` with a Google ID token (popup flow) returns tokens (or a 2FA verification token).

### Two-Factor Authentication

When 2FA is enabled on an account, login returns `requires_2fa: true` and a `verification_token` instead of tokens. Submit the OTP code via the verify endpoint to receive tokens.

---

## Error Response Format

All errors are returned as JSON objects:

```json
{
  "detail": "Human-readable error message"
}
```

### Common Error Codes

| Status | Meaning | Typical Cause |
|--------|---------|---------------|
| `400` | Bad Request | Invalid input, expired token, validation failure |
| `401` | Unauthorized | Missing or invalid JWT token, wrong OTP |
| `403` | Forbidden | Account locked, insufficient permissions |
| `404` | Not Found | Resource does not exist or was deleted |
| `409` | Conflict | Duplicate resource (e.g., existing email) |
| `413` | Payload Too Large | File exceeds size limit |
| `422` | Unprocessable Entity | Request body fails validation |
| `429` | Too Many Requests | Rate limit exceeded (includes `Retry-After` header) |
| `500` | Internal Server Error | Unexpected server failure |
| `503` | Service Unavailable | Database or Redis connection failure |

---

## Pagination

List endpoints that return collections support cursor-based or offset-based pagination:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | `1` | Page number (1-indexed) |
| `page_size` | integer | `20` | Items per page |

Paginated responses follow this structure:

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

Non-paginated list endpoints return a `total_count` field alongside the collection:

```json
{
  "tasks": [],
  "total_count": 100
}
```

---

## Filtering

List endpoints support query-string filters. Available filters vary per endpoint:

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Full-text search across relevant fields |
| `status` | string | Filter by status enum value |
| `priority` | string | Filter by priority level |
| `category` | string | Filter by category string |
| `tag` | string | Filter by tag |
| `favorite` | boolean | Filter by favorite status |
| `pinned` | boolean | Filter by pinned status |
| `archived` | boolean | Filter by archived status |
| `deleted` | boolean | Filter by soft-deleted status |

---

## Sorting

Endpoints that support listing allow sorting via query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort_by` | string | `created_at` | Field to sort by |
| `sort_order` | string | `desc` | Sort direction: `asc` or `desc` |

---

## Status Codes

### Success Codes

| Code | Meaning |
|------|---------|
| `200` | Success (default for most endpoints) |
| `201` | Created successfully |
| `204` | Success with no content (rarely used) |

### Error Codes

See [Common Error Codes](#common-error-codes) above.

---

## Rate Limiting

Rate limiting uses a Redis-backed sliding window algorithm. Limits are applied per endpoint group and per user (identified by JWT `sub` claim) or per IP for unauthenticated requests.

### Rate Limit Headers

| Header | Description |
|--------|-------------|
| `Retry-After` | Seconds to wait before retrying (only on `429`) |

### Limit Groups

| Group | Limit | Window | Applies To |
|-------|-------|--------|------------|
| `auth` | 3 requests | 60s | All authentication endpoints |
| `general_get` | 60 requests | 60s | All read-only list/get endpoints |
| `write_entity` | 20 requests | 60s | Create/update/delete entity endpoints |
| `file_upload` | 3 requests | 60s | File upload endpoints (multipart) |
| `meeting_creation` | 10 requests | 60s | Meeting creation |
| `ai_analysis` | 3 requests | 60s | AI suggestion operations |
| `notification_subscription` | 10 requests | 60s | Push subscription registration |
| `notification_subscription_delete` | 20 requests | 60s | Push subscription removal |

### 429 Response

```json
{
  "detail": "Too many requests. Please try again in 42 seconds."
}
```

Rate limiting is fail-open: if Redis is unavailable, requests pass through without enforcement.

---

## Endpoints

---

### Health

Health check endpoint (no prefix, no authentication).

---

#### `GET /health`

Check database connectivity and application status.

| | |
|---|---|
| **Authentication** | No |
| **Rate Limiting** | No |

**Success Response** `200 OK`

```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "LOCAL"
}
```

**Error Response** `503 Service Unavailable`

```json
{
  "status": "unhealthy",
  "database": "disconnected: <error details>"
}
```

---

### Authentication

All endpoints are prefixed with `/api/v1/auth`.

---

#### `POST /auth/google`

Authenticate or register via Google Identity Services (popup flow).

| | |
|---|---|
| **Authentication** | No |
| **Rate Limiting** | 3 requests / 60s |

**Request Body** `application/json`

```json
{
  "id_token": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id_token` | string | Yes | Google ID token from the frontend OAuth flow |

**Success Response** `200 OK`

Returns tokens directly if 2FA is not enabled:

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

Returns a verification token if 2FA is enabled:

```json
{
  "requires_2fa": true,
  "verification_token": "string"
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `400` | Invalid or malformed Google ID token |
| `401` | Google authentication failed |

---

#### `POST /auth/signup`

Register a new user account.

| | |
|---|---|
| **Authentication** | No |
| **Rate Limiting** | 3 requests / 60s |

**Request Body** `application/json`

```json
{
  "email": "user@example.com",
  "password": "securepass123",
  "full_name": "Jane Doe",
  "enable_2fa": false
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `email` | string (email) | Yes | Must be a valid email domain | User email address |
| `password` | string | Yes | Min 8 characters | Account password |
| `full_name` | string | Yes | Min 2 characters | Display name |
| `enable_2fa` | boolean | No | Default: `false` | Enable two-factor authentication |

**Success Response** `201 Created`

```json
{
  "verification_token": "string",
  "message": "Verification code sent to email."
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `400` | Email already registered or validation failure |

---

#### `POST /auth/verify-signup`

Verify email OTP to complete registration.

| | |
|---|---|
| **Authentication** | No |
| **Rate Limiting** | 3 requests / 60s |

**Request Body** `application/json`

```json
{
  "verification_token": "string",
  "code": "123456"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `verification_token` | string | Yes | — | Token from signup response |
| `code` | string | Yes | Exactly 6 characters | OTP code sent to email |

**Success Response** `200 OK`

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid or expired OTP code |
| `404` | Verification token not found |

---

#### `POST /auth/resend-signup-otp`

Resend the OTP code for signup verification.

| | |
|---|---|
| **Authentication** | No |
| **Rate Limiting** | 3 requests / 60s |

**Request Body** `application/json`

```json
{
  "verification_token": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verification_token` | string | Yes | Token from signup response |

**Success Response** `200 OK`

```json
{
  "message": "Verification code resent successfully."
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `400` | Invalid or expired verification token |

---

#### `POST /auth/login`

Initiate login with email and password.

| | |
|---|---|
| **Authentication** | No |
| **Rate Limiting** | 3 requests / 60s |

**Request Body** `application/json`

```json
{
  "email": "user@example.com",
  "password": "securepass123"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string (email) | Yes | Registered email address |
| `password` | string | Yes | Account password |

**Success Response** `200 OK`

Returns tokens directly:

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

Returns verification token if 2FA is enabled:

```json
{
  "requires_2fa": true,
  "verification_token": "string"
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid email or password |
| `403` | Account is locked or disabled |

---

#### `POST /auth/verify-login`

Verify OTP to complete login (2FA flow).

| | |
|---|---|
| **Authentication** | No |
| **Rate Limiting** | 3 requests / 60s |

**Request Body** `application/json`

```json
{
  "verification_token": "string",
  "code": "123456"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `verification_token` | string | Yes | — | Token from login response |
| `code` | string | Yes | Exactly 6 characters | OTP code sent to email |

**Success Response** `200 OK`

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid or expired OTP code |
| `404` | Verification token not found |

---

#### `POST /auth/resend-login-otp`

Resend the OTP code for login verification.

| | |
|---|---|
| **Authentication** | No |
| **Rate Limiting** | 3 requests / 60s |

**Request Body** `application/json`

```json
{
  "verification_token": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verification_token` | string | Yes | Token from login response |

**Success Response** `200 OK`

```json
{
  "message": "Login verification code resent successfully."
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `400` | Invalid or expired verification token |

---

#### `POST /auth/refresh`

Exchange a refresh token for new access and refresh tokens.

| | |
|---|---|
| **Authentication** | No |
| **Rate Limiting** | No |

**Request Body** `application/json`

```json
{
  "refresh_token": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refresh_token` | string | Yes | Valid refresh token |

**Success Response** `200 OK`

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer"
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid or expired refresh token |

---

#### `POST /auth/password-reset/initiate`

Request a password reset email.

| | |
|---|---|
| **Authentication** | No |
| **Rate Limiting** | 3 requests / 60s |

**Request Body** `application/json`

```json
{
  "email": "user@example.com"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string (email) | Yes | Registered email address |

**Success Response** `200 OK`

```json
{
  "message": "If records match, processing vectors have background initialized."
}
```

> **Note:** The response is identical whether or not the email exists, to prevent user enumeration.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Account is disabled |

---

#### `POST /auth/password-reset/confirm`

Confirm a password reset with the token from the email.

| | |
|---|---|
| **Authentication** | No |
| **Rate Limiting** | 3 requests / 60s |

**Request Body** `application/json`

```json
{
  "token": "string",
  "new_password": "newsecurepass123"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `token` | string | Yes | — | Password reset token from email |
| `new_password` | string | Yes | Min 8 characters | New password |

**Success Response** `200 OK`

```json
{
  "message": "Password updated successfully. Active cached sessions revoked."
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `400` | Invalid or expired reset token |
| `404` | Reset token not found |

---

### Users

All endpoints are prefixed with `/api/v1/users`. All require authentication.

---

#### `GET /users/me`

Get the current authenticated user's profile.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | No |
| **Headers** | `Authorization: Bearer <token>` |

**Success Response** `200 OK`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "is_verified": true,
  "is_2fa_enabled": false,
  "profile_image": "https://...",
  "timezone": "America/New_York",
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid or missing token |
| `404` | User not found |

---

#### `PUT /users/profile`

Update the current user's profile.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | No |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "full_name": "New Name",
  "timezone": "Europe/London"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `full_name` | string | No | Min 2 characters | Updated display name |
| `timezone` | string | No | Valid IANA timezone or null | User timezone |

**Success Response** `200 OK`

Returns the updated `UserProfileResponse` (same shape as `GET /users/me`).

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | User not found |
| `422` | Validation error |

---

#### `PUT /users/change-password`

Change the current user's password.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | No |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `current_password` | string | Yes | — | Current password for verification |
| `new_password` | string | Yes | Min 8 characters | New password |

**Success Response** `200 OK`

```json
{
  "message": "Password updated successfully."
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `400` | Current password is incorrect |
| `401` | Invalid token |

---

#### `PUT /users/change-email`

Change the current user's email address.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | No |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "current_password": "currentpassword",
  "new_email": "newemail@example.com"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `current_password` | string | Yes | Current password for verification |
| `new_email` | string (email) | Yes | New email address |

**Success Response** `200 OK`

```json
{
  "message": "Email change initiated. Please verify the new email."
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `400` | Password incorrect or email already in use |
| `401` | Invalid token |

---

#### `PUT /users/profile-image`

Update the current user's profile image.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | No |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "profile_image": "https://storage.example.com/avatar.jpg"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `profile_image` | string | Yes | URL of the profile image |

**Success Response** `200 OK`

Returns the updated `UserProfileResponse`.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | User not found |

---

#### `PUT /users/2fa`

Enable or disable two-factor authentication.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | No |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "enable": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `enable` | boolean | Yes | `true` to enable 2FA, `false` to disable |

**Success Response** `200 OK`

Returns the updated `UserProfileResponse`.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | User not found |

---

#### `DELETE /users/deactivate`

Deactivate the current user's account.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | No |
| **Headers** | `Authorization: Bearer <token>` |

**Success Response** `200 OK`

```json
{
  "message": "Account deactivated successfully."
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | User not found |

---

### Calendar

All endpoints are prefixed with `/api/v1/calendar`. All require authentication.

---

#### `POST /calendar/events`

Create a new calendar event.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "title": "Team Standup",
  "description": "Daily sync meeting",
  "event_type": "MEETING",
  "color": "BLUE",
  "start_time": "2025-07-20T09:00:00Z",
  "end_time": "2025-07-20T09:30:00Z",
  "timezone": "America/New_York",
  "is_all_day": false,
  "location": "Conference Room A",
  "recurrence_frequency": "DAILY",
  "recurrence_interval": 1,
  "recurrence_end_date": "2025-08-20T09:00:00Z"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | string | Yes | Max 255 chars, must not be empty | Event title |
| `description` | string | No | — | Event description |
| `event_type` | string | No | `PERSONAL`, `MEETING`, or `REMINDER`. Default: `PERSONAL` | Event category |
| `color` | string | No | One of: `RED`, `BLUE`, `GREEN`, `YELLOW`, `PURPLE`, `ORANGE`, `GRAY`. Default: `BLUE` | Display color |
| `start_time` | datetime | Yes | Must be before `end_time` | Start datetime (UTC) |
| `end_time` | datetime | Yes | Must be after `start_time` | End datetime (UTC) |
| `timezone` | string | No | Valid IANA timezone | Viewing timezone |
| `is_all_day` | boolean | No | Default: `false` | All-day event flag |
| `location` | string | No | Max 500 chars | Event location |
| `recurrence_frequency` | string | No | `DAILY`, `WEEKLY`, or `MONTHLY` | Recurrence pattern |
| `recurrence_interval` | integer | No | Min: 1 | Recurrence interval |
| `recurrence_end_date` | datetime | No | Must be >= `start_time` | Recurrence end date |

**Success Response** `201 Created`

Returns the full `CalendarEventResponse`.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | User not found |
| `422` | Validation error (e.g., `start_time >= end_time`) |

---

#### `GET /calendar/analytics`

Get calendar analytics for the current user.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Success Response** `200 OK`

Returns analytics object with event counts, upcoming events, and other summary data.

---

#### `GET /calendar/events/{event_id}`

Get a single calendar event by ID.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | UUID | Calendar event ID |

**Success Response** `200 OK`

Returns the full `CalendarEventResponse`.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | Event not found |

---

#### `PATCH /calendar/events/{event_id}`

Update a calendar event.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | UUID | Calendar event ID |

**Request Body** `application/json`

All fields are optional (partial update):

```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "event_type": "MEETING",
  "color": "RED",
  "start_time": "2025-07-20T10:00:00Z",
  "end_time": "2025-07-20T11:00:00Z",
  "timezone": "Europe/London",
  "is_all_day": true,
  "location": "New Location",
  "recurrence_frequency": "WEEKLY",
  "recurrence_interval": 2,
  "recurrence_end_date": "2025-12-31T00:00:00Z"
}
```

**Success Response** `200 OK`

Returns the updated `CalendarEventResponse`.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | Event not found |
| `422` | Validation error |

---

#### `DELETE /calendar/events/{event_id}`

Delete a calendar event.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | UUID | Calendar event ID |

**Success Response** `200 OK`

```json
{
  "message": "Event deleted successfully."
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | Event not found |

---

#### `GET /calendar/events`

List calendar events within a time range. Supports recurring event expansion.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start` | datetime | Yes | Range start (UTC) |
| `end` | datetime | Yes | Range end (UTC) |
| `search` | string | No | Search term for title/description |
| `event_type` | string | No | Filter by type: `PERSONAL`, `MEETING`, `REMINDER` |
| `color` | string | No | Filter by color |

**Success Response** `200 OK`

```json
[
  {
    "id": "uuid",
    "title": "Team Standup",
    "description": "Daily sync",
    "event_type": "MEETING",
    "color": "BLUE",
    "start_time": "2025-07-20T09:00:00Z",
    "end_time": "2025-07-20T09:30:00Z",
    "timezone": "America/New_York",
    "is_all_day": false,
    "location": "Conference Room A",
    "is_recurring": true,
    "recurrence_frequency": "DAILY",
    "recurrence_interval": 1,
    "recurrence_end_date": "2025-08-20T09:00:00Z"
  }
]
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `422` | Missing required query parameters (`start`, `end`) |

---

#### `POST /calendar/events/{event_id}/attachments`

Upload an attachment to a calendar event.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 3 requests / 60s |
| **Headers** | `Authorization: Bearer <token>`, `Content-Type: multipart/form-data` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | UUID | Calendar event ID |

**Request Body** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | File to upload |

**Success Response** `201 Created`

Returns the full `AttachmentResponse`.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | Event not found |
| `413` | File too large |

---

#### `GET /calendar/events/{event_id}/attachments`

List all attachments for a calendar event.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | UUID | Calendar event ID |

**Success Response** `200 OK`

```json
{
  "attachments": [ ... ],
  "total_count": 3
}
```

Returns `AttachmentListResponse`.

---

#### `GET /calendar/events/{event_id}/attachments/{attachment_id}/download`

Download a specific attachment from a calendar event.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | UUID | Calendar event ID |
| `attachment_id` | UUID | Attachment ID |

**Success Response** `200 OK`

Returns the file as `FileResponse` with appropriate `Content-Type` and `Content-Disposition` headers.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | Attachment not found |

---

#### `DELETE /calendar/events/{event_id}/attachments/{attachment_id}`

Delete a specific attachment from a calendar event.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | UUID | Calendar event ID |
| `attachment_id` | UUID | Attachment ID |

**Success Response** `200 OK`

```json
{
  "message": "Attachment deleted successfully."
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | Attachment not found |

---

### Notes

All endpoints are prefixed with `/api/v1/notes`. All require authentication.

---

#### `POST /notes`

Create a new note.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "title": "Meeting Notes",
  "content": "Today we discussed...",
  "category": "work",
  "tags": ["meetings", "planning"],
  "is_pinned": false,
  "is_favorite": false,
  "is_archived": false
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | string | No | Max 255 chars | Note title (title or content required) |
| `content` | string | Yes | Max 50,000 chars | Note body text |
| `category` | string | No | Max 100 chars | Classification category |
| `tags` | array of strings | No | Stripped, lowercased, deduplicated | Tag labels |
| `is_pinned` | boolean | No | Default: `false` | Pinned status |
| `is_favorite` | boolean | No | Default: `false` | Favorite status |
| `is_archived` | boolean | No | Default: `false` | Archived status |

**Success Response** `201 Created`

Returns the full `NoteResponse`.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `422` | Validation error (title and content cannot both be empty) |

---

#### `GET /notes`

List notes with filtering and sorting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search` | string | No | Search term for title/content |
| `category` | string | No | Filter by category |
| `tag` | string | No | Filter by tag |
| `favorite` | boolean | No | Filter by favorite status |
| `pinned` | boolean | No | Filter by pinned status |
| `archived` | boolean | No | Filter by archived status |
| `deleted` | boolean | No | Include soft-deleted notes |
| `sort_by` | string | No | Sort field (default: `created_at`) |
| `sort_order` | string | No | `asc` or `desc` (default: `desc`) |

**Success Response** `200 OK`

```json
{
  "notes": [ ... ],
  "total_count": 42
}
```

---

#### `GET /notes/analytics`

Get notes analytics for the current user.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Success Response** `200 OK`

Returns analytics summary with note counts by category, tag distribution, and other metrics.

---

#### `GET /notes/{note_id}`

Get a single note by ID.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `note_id` | UUID | Note ID |

**Success Response** `200 OK`

Returns the full `NoteResponse`.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | Note not found |

---

#### `PATCH /notes/{note_id}`

Update a note (partial update).

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `note_id` | UUID | Note ID |

**Request Body** `application/json`

All fields optional (partial update):

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `title` | string | Max 255 chars | Updated title |
| `content` | string | Max 50,000 chars | Updated content |
| `category` | string | Max 100 chars | Updated category |
| `tags` | array of strings | — | Replace tag set |

**Success Response** `200 OK`

Returns the updated `NoteResponse`.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | Note not found |
| `422` | Validation error |

---

#### `DELETE /notes/{note_id}`

Soft-delete a note.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `note_id` | UUID | Note ID |

**Success Response** `200 OK`

```json
{
  "message": "Note deleted successfully."
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | Note not found |

---

#### `PATCH /notes/{note_id}/restore`

Restore a soft-deleted note.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `note_id` | UUID | Note ID |

**Success Response** `200 OK`

Returns the restored `NoteResponse`.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | Note not found |

---

#### `PATCH /notes/{note_id}/archive`

Archive a note.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `note_id` | UUID | Note ID |

**Success Response** `200 OK`

Returns the updated `NoteResponse`.

---

#### `PATCH /notes/{note_id}/unarchive`

Unarchive a note.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `note_id` | UUID | Note ID |

**Success Response** `200 OK`

Returns the updated `NoteResponse`.

---

#### `PATCH /notes/{note_id}/pin`

Pin a note.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `note_id` | UUID | Note ID |

**Success Response** `200 OK`

Returns the updated `NoteResponse`.

---

#### `PATCH /notes/{note_id}/unpin`

Unpin a note.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `note_id` | UUID | Note ID |

**Success Response** `200 OK`

Returns the updated `NoteResponse`.

---

#### `PATCH /notes/{note_id}/favorite`

Mark a note as favorite.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `note_id` | UUID | Note ID |

**Success Response** `200 OK`

Returns the updated `NoteResponse`.

---

#### `PATCH /notes/{note_id}/unfavorite`

Remove a note from favorites.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `note_id` | UUID | Note ID |

**Success Response** `200 OK`

Returns the updated `NoteResponse`.

---

### Tasks

All endpoints are prefixed with `/api/v1/tasks`. All require authentication.

---

#### `POST /tasks`

Create a new task.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "title": "Implement login",
  "description": { "rich": "content" },
  "status": "TODO",
  "priority": "HIGH",
  "due_date": "2025-07-25T17:00:00Z",
  "labels": ["backend", "auth"],
  "checklist": [
    { "id": "item-1", "text": "Write auth module", "completed": false },
    { "id": "item-2", "text": "Write tests", "completed": false }
  ],
  "is_pinned": false,
  "is_favorite": false,
  "is_archived": false
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | string | Yes | Max 255 chars, must not be blank | Task title |
| `description` | object | No | — | Rich description payload (JSON object) |
| `status` | string | No | `TODO`, `IN_PROGRESS`, `DONE`. Default: `TODO` | Task status |
| `priority` | string | No | `LOW`, `MEDIUM`, `HIGH`. Default: `MEDIUM` | Task priority |
| `due_date` | datetime | No | Must not be in the past | Due date (UTC) |
| `labels` | array of strings | No | Stripped, lowercased, deduplicated | Label tags |
| `checklist` | array | No | — | Sub-items (see below) |
| `checklist[].id` | string | Yes | Client-generated unique ID | Item identifier |
| `checklist[].text` | string | Yes | Must not be empty | Item description |
| `checklist[].completed` | boolean | No | Default: `false` | Completion status |
| `is_pinned` | boolean | No | Default: `false` | Pinned status |
| `is_favorite` | boolean | No | Default: `false` | Favorite status |
| `is_archived` | boolean | No | Default: `false` | Archived status |

**Success Response** `201 Created`

Returns the full `TaskResponse`.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `422` | Validation error (e.g., blank title, past due date) |

---

#### `GET /tasks`

List tasks with filtering and sorting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search` | string | No | Search term for title/description |
| `status` | string | No | Filter: `TODO`, `IN_PROGRESS`, `DONE` |
| `priority` | string | No | Filter: `LOW`, `MEDIUM`, `HIGH` |
| `label` | string | No | Filter by label |
| `favorite` | boolean | No | Filter by favorite status |
| `pinned` | boolean | No | Filter by pinned status |
| `archived` | boolean | No | Filter by archived status |
| `deleted` | boolean | No | Include soft-deleted tasks |
| `due_date` | datetime | No | Filter by due date |
| `sort_by` | string | No | Sort field (default: `created_at`) |
| `sort_order` | string | No | `asc` or `desc` (default: `desc`) |

**Success Response** `200 OK`

```json
{
  "tasks": [ ... ],
  "total_count": 55
}
```

---

#### `GET /tasks/analytics`

Get task analytics for the current user.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Success Response** `200 OK`

Returns analytics summary with task counts by status, priority distribution, and other metrics.

---

#### `GET /tasks/{task_id}`

Get a single task by ID.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Success Response** `200 OK`

Returns the full `TaskResponse`.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | Task not found |

---

#### `PATCH /tasks/{task_id}`

Update a task (partial update).

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Request Body** `application/json`

All fields optional (partial update):

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `title` | string | Max 255 chars | Updated title (cannot be empty) |
| `description` | object | — | Updated rich description |
| `status` | string | `TODO`, `IN_PROGRESS`, `DONE` | Updated status |
| `priority` | string | `LOW`, `MEDIUM`, `HIGH` | Updated priority |
| `due_date` | datetime | — | Updated due date |
| `labels` | array of strings | — | Replace label set |
| `checklist` | array | — | Replace checklist |

**Success Response** `200 OK`

Returns the updated `TaskResponse`.

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | Task not found |
| `422` | Validation error |

---

#### `DELETE /tasks/{task_id}`

Soft-delete a task.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Success Response** `200 OK`

```json
{
  "message": "Task deleted successfully."
}
```

**Error Responses**

| Status | Detail |
|--------|--------|
| `401` | Invalid token |
| `404` | Task not found |

---

#### `PATCH /tasks/{task_id}/restore`

Restore a soft-deleted task.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Success Response** `200 OK`

Returns the restored `TaskResponse`.

---

#### `PATCH /tasks/{task_id}/archive`

Archive a task.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Success Response** `200 OK`

Returns the updated `TaskResponse`.

---

#### `PATCH /tasks/{task_id}/unarchive`

Unarchive a task.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Success Response** `200 OK`

Returns the updated `TaskResponse`.

---

#### `PATCH /tasks/{task_id}/pin`

Pin a task.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Success Response** `200 OK`

Returns the updated `TaskResponse`.

---

#### `PATCH /tasks/{task_id}/unpin`

Unpin a task.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Success Response** `200 OK`

Returns the updated `TaskResponse`.

---

#### `PATCH /tasks/{task_id}/favorite`

Mark a task as favorite.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Success Response** `200 OK`

Returns the updated `TaskResponse`.

---

#### `PATCH /tasks/{task_id}/unfavorite`

Remove a task from favorites.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Success Response** `200 OK`

Returns the updated `TaskResponse`.

---

#### `GET /tasks/{task_id}/history`

Get the change history for a task.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Success Response** `200 OK`

```json
{
  "history": [
    {
      "id": "uuid",
      "action": "status_changed",
      "field_name": "status",
      "old_value": "TODO",
      "new_value": "IN_PROGRESS",
      "created_at": "2025-07-20T10:00:00Z",
      "user": {
        "id": "uuid",
        "name": "Jane Doe"
      }
    }
  ],
  "total_count": 5
}
```

---

#### `POST /tasks/{task_id}/attachments`

Upload an attachment to a task.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 3 requests / 60s |
| **Headers** | `Authorization: Bearer <token>`, `Content-Type: multipart/form-data` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Request Body** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | File to upload |

**Success Response** `201 Created`

Returns the full `AttachmentResponse`.

---

#### `GET /tasks/{task_id}/attachments`

List all attachments for a task.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Success Response** `200 OK`

Returns `AttachmentListResponse`.

---

#### `GET /tasks/{task_id}/attachments/{attachment_id}/download`

Download a specific attachment from a task.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |
| `attachment_id` | UUID | Attachment ID |

**Success Response** `200 OK`

Returns the file as `FileResponse`.

---

#### `DELETE /tasks/{task_id}/attachments/{attachment_id}`

Delete a specific attachment from a task.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |
| `attachment_id` | UUID | Attachment ID |

**Success Response** `200 OK`

```json
{
  "message": "Attachment deleted successfully."
}
```

---

### Meetings

All endpoints are prefixed with `/api/v1/meetings`. Most require authentication; some support guest access.

---

#### `POST /meetings/`

Create an instant meeting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 10 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "title": "Design Review",
  "description": "Review new UI mockups",
  "enable_recording": true,
  "enable_transcript": true,
  "agenda": "Discuss landing page redesign",
  "enable_ai_analysis": false
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | string | Yes | Max 255 chars, must not be blank | Meeting title |
| `description` | string | No | — | Meeting description |
| `enable_recording` | boolean | No | Default: `false` | Enable recording |
| `enable_transcript` | boolean | No | Default: `false` | Enable transcription |
| `agenda` | string | No | — | Meeting agenda |
| `enable_ai_analysis` | boolean | No | Default: `false` | Enable AI analysis |

**Success Response** `201 Created`

Returns the full `MeetingResponse`.

---

#### `GET /meetings`

List all meetings for the current user.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Success Response** `200 OK`

```json
[
  {
    "id": "uuid",
    "host_id": "uuid",
    "title": "Design Review",
    "meeting_code": "abc-def-ghi",
    "meeting_link": "https://app.example.com/meet/abc-def-ghi",
    "status": "ACTIVE",
    "meeting_type": "INSTANT",
    "created_at": "2025-07-20T10:00:00Z",
    ...
  }
]
```

Returns `List[MeetingResponse]`.

---

#### `GET /meetings/by-code/{code}`

Get meeting information by short code (public join info).

| | |
|---|---|
| **Authentication** | No |
| **Headers** | None |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Meeting short code |

**Success Response** `200 OK`

Returns `MeetingJoinInfoResponse` (extends `MeetingResponse` with `host_name`).

---

#### `GET /meetings/recent-analyses`

List recent AI analysis results across meetings.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 5 | Max items (1-20) |

**Success Response** `200 OK`

Returns `List[RecentAIAnalysisItem]`.

---

#### `GET /meetings/{meeting_id}`

Get a single meeting by ID.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

Returns the full `MeetingResponse`.

---

#### `PATCH /meetings/{meeting_id}`

Update a meeting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Request Body** `application/json`

All fields optional:

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Updated title (max 255 chars) |
| `description` | string | Updated description |
| `enable_recording` | boolean | Toggle recording |
| `enable_transcript` | boolean | Toggle transcription |
| `agenda` | string | Updated agenda |
| `enable_ai_analysis` | boolean | Toggle AI analysis |

**Success Response** `200 OK`

Returns the updated `MeetingResponse`.

---

#### `POST /meetings/{meeting_id}/end`

End an active meeting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

Returns the updated `MeetingResponse` with `status: "ENDED"`.

---

#### `POST /meetings/{meeting_id}/cancel`

Cancel a scheduled meeting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

Returns the updated `MeetingResponse` with `status: "CANCELLED"`.

---

#### `DELETE /meetings/{meeting_id}`

Delete a meeting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

Returns the deleted `MeetingResponse`.

---

#### `POST /meetings/{meeting_id}/copy-link`

Copy the meeting join link.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

```json
{
  "link": "https://app.example.com/meet/abc-def-ghi"
}
```

---

#### `POST /meetings/{meeting_id}/join`

Join a meeting (supports both authenticated and guest users).

| | |
|---|---|
| **Authentication** | Optional (bearer token for registered users) |
| **Headers** | `Authorization: Bearer <token>` (optional) |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Request Body** `application/json`

```json
{
  "guest_name": "John Guest",
  "guest_email": "guest@example.com"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `guest_name` | string | No | Max 100 chars | Guest display name (required for unauthenticated) |
| `guest_email` | string | No | Max 255 chars | Guest email |

**Success Response** `200 OK`

Returns `MeetingJoinResponse` which includes all participant fields plus `meeting_session_token`.

---

#### `GET /meetings/{meeting_id}/participants`

List all participants in a meeting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

Returns `List[MeetingParticipantResponse]`.

---

#### `POST /meetings/{meeting_id}/recordings`

Upload a recording to a meeting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 3 requests / 60s |
| **Headers** | `Authorization: Bearer <token>`, `Content-Type: multipart/form-data` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Request Body** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | Recording file |
| `duration` | float | No | Recording duration in seconds |

**Success Response** `201 Created`

Returns the full `RecordingResponse`.

---

#### `GET /meetings/{meeting_id}/recordings`

List all recordings for a meeting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

Returns `List[RecordingResponse]`.

---

#### `GET /meetings/recordings/{recording_id}/download`

Download a recording file.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `recording_id` | UUID | Recording ID |

**Success Response** `200 OK`

Returns the file as `FileResponse`.

---

#### `DELETE /meetings/recordings/{recording_id}`

Delete a recording.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `recording_id` | UUID | Recording ID |

**Success Response** `200 OK`

```json
{
  "message": "Recording deleted successfully."
}
```

---

#### `POST /meetings/{meeting_id}/transcripts`

Upload a transcript to a meeting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 3 requests / 60s |
| **Headers** | `Authorization: Bearer <token>`, `Content-Type: multipart/form-data` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Request Body** `multipart/form-data`

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | file | Yes | — | Transcript file |
| `content_type` | string | No | `text/plain` | MIME type of the transcript |

**Success Response** `201 Created`

Returns the full `TranscriptResponse`.

---

#### `GET /meetings/{meeting_id}/transcripts`

List all transcripts for a meeting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

Returns `List[TranscriptResponse]`.

---

#### `GET /meetings/transcripts/{transcript_id}/download`

Download a transcript file.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `transcript_id` | UUID | Transcript ID |

**Success Response** `200 OK`

Returns the file as `FileResponse`.

---

#### `DELETE /meetings/transcripts/{transcript_id}`

Delete a transcript.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `transcript_id` | UUID | Transcript ID |

**Success Response** `200 OK`

```json
{
  "message": "Transcript deleted successfully."
}
```

---

#### `POST /meetings/{meeting_id}/participants/{participant_id}/admit`

Admit a participant from the waiting room.

| | |
|---|---|
| **Authentication** | Bearer token required (host only) |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `participant_id` | UUID | Participant ID |

**Success Response** `200 OK`

```json
{
  "message": "Participant admitted."
}
```

---

#### `POST /meetings/{meeting_id}/participants/{participant_id}/reject`

Reject a participant from the waiting room.

| | |
|---|---|
| **Authentication** | Bearer token required (host only) |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `participant_id` | UUID | Participant ID |

**Success Response** `200 OK`

```json
{
  "message": "Participant rejected."
}
```

---

#### `POST /meetings/{meeting_id}/participants/{participant_id}/remove`

Remove an active participant from the meeting.

| | |
|---|---|
| **Authentication** | Bearer token required (host only) |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `participant_id` | UUID | Participant ID |

**Success Response** `200 OK`

```json
{
  "message": "Participant removed."
}
```

---

#### `POST /meetings/{meeting_id}/participants/{participant_id}/mute`

Mute a participant's audio.

| | |
|---|---|
| **Authentication** | Bearer token required (host only) |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `participant_id` | UUID | Participant ID |

**Success Response** `200 OK`

```json
{
  "message": "Participant muted."
}
```

---

#### `POST /meetings/{meeting_id}/participants/{participant_id}/unmute`

Unmute a participant's audio.

| | |
|---|---|
| **Authentication** | Bearer token required (host only) |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `participant_id` | UUID | Participant ID |

**Success Response** `200 OK`

```json
{
  "message": "Participant unmuted."
}
```

---

#### `POST /meetings/{meeting_id}/leave`

Leave a meeting.

| | |
|---|---|
| **Authentication** | Optional (bearer token or guest) |
| **Headers** | `Authorization: Bearer <token>` (optional) |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Request Body** `application/json` (optional)

```json
{
  "reason": "Scheduled conflict"
}
```

**Success Response** `200 OK`

Returns the `MeetingParticipantResponse` of the leaving participant.

---

#### `GET /meetings/{meeting_id}/waiting-count`

Get the count of participants in the waiting room.

| | |
|---|---|
| **Authentication** | No |
| **Headers** | None |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

```json
{
  "waiting_count": 3
}
```

---

#### `POST /meetings/{meeting_id}/screen-share/approve/{participant_id}`

Approve a participant's screen share request.

| | |
|---|---|
| **Authentication** | Bearer token required (host only) |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `participant_id` | UUID | Participant requesting screen share |

**Success Response** `200 OK`

```json
{
  "message": "Screen share approved."
}
```

---

#### `POST /meetings/{meeting_id}/screen-share/reject/{participant_id}`

Reject a participant's screen share request.

| | |
|---|---|
| **Authentication** | Bearer token required (host only) |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `participant_id` | UUID | Participant requesting screen share |

**Success Response** `200 OK`

```json
{
  "message": "Screen share rejected."
}
```

---

#### `POST /meetings/{meeting_id}/screen-share/stop`

Force-stop the current screen sharer.

| | |
|---|---|
| **Authentication** | Bearer token required (host only) |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

```json
{
  "message": "Screen share stopped."
}
```

---

#### `POST /meetings/{meeting_id}/screen-share/request`

Request permission to share screen.

| | |
|---|---|
| **Authentication** | Bearer token required (participant) |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Request Body** `application/json`

```json
{
  "reason": "Need to present slides"
}
```

**Success Response** `200 OK`

```json
{
  "message": "Screen share request sent."
}
```

---

#### `POST /meetings/scheduled`

Create a scheduled meeting with invitations.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "title": "Quarterly Review",
  "description": "Q3 performance review",
  "enable_recording": true,
  "enable_transcript": true,
  "enable_ai_analysis": true,
  "agenda": "Review Q3 metrics and plan Q4",
  "scheduled_start": "2025-08-01T14:00:00Z",
  "timezone": "America/New_York",
  "invitations": [
    { "name": "Alice", "email": "alice@example.com" },
    { "name": "Bob", "email": "bob@example.com" }
  ]
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | string | Yes | Min 1, max 255 chars | Meeting title |
| `description` | string | No | — | Meeting description |
| `enable_recording` | boolean | No | Default: `false` | Enable recording |
| `enable_transcript` | boolean | No | Default: `false` | Enable transcription |
| `enable_ai_analysis` | boolean | No | Default: `false` | Enable AI analysis |
| `agenda` | string | No | — | Meeting agenda |
| `scheduled_start` | datetime | Yes | Must be in the future | Scheduled start time (UTC) |
| `timezone` | string | No | Max 64 chars | Timezone identifier |
| `invitations` | array | Yes | Min 1 invitation | List of participants to invite |
| `invitations[].name` | string | Yes | Min 1, max 255 chars | Invitee name |
| `invitations[].email` | string (email) | Yes | — | Invitee email |

**Success Response** `201 Created`

Returns the full `MeetingResponse`.

---

#### `POST /meetings/{meeting_id}/invitations`

Send invitations to participants.

| | |
|---|---|
| **Authentication** | Bearer token required (host only) |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Request Body** `application/json`

```json
[
  { "name": "Charlie", "email": "charlie@example.com" }
]
```

**Success Response** `200 OK`

Returns `List[InvitationResponse]`.

---

#### `GET /meetings/{meeting_id}/invitations`

List all invitations for a meeting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

Returns `List[InvitationResponse]`.

---

#### `GET /meetings/{meeting_id}/sessions`

List all sessions for a meeting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

Returns `List[SessionHistoryItemResponse]`.

---

#### `GET /meetings/{meeting_id}/sessions/{session_id}`

Get detailed information about a specific session.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `session_id` | UUID | Session ID |

**Success Response** `200 OK`

Returns `SessionDetailResponse` with participants and artifact flags.

---

#### `GET /meetings/{meeting_id}/sessions/{session_id}/recordings`

List recordings for a specific session.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `session_id` | UUID | Session ID |

**Success Response** `200 OK`

Returns `List[RecordingResponse]`.

---

#### `GET /meetings/{meeting_id}/sessions/{session_id}/transcripts`

List transcripts for a specific session.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `session_id` | UUID | Session ID |

**Success Response** `200 OK`

Returns `List[TranscriptResponse]`.

---

#### `GET /meetings/{meeting_id}/sessions/{session_id}/analysis`

Get AI analysis for a specific session.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `session_id` | UUID | Session ID |

**Success Response** `200 OK`

Returns the full `AIAnalysisResponse`.

---

#### `GET /meetings/{meeting_id}/sessions/{session_id}/analysis/status`

Get the processing status of a session's AI analysis.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `session_id` | UUID | Session ID |

**Success Response** `200 OK`

```json
{
  "session_id": "uuid",
  "status": "COMPLETED",
  "processing_started_at": "2025-07-20T10:00:00Z",
  "processing_completed_at": "2025-07-20T10:05:00Z"
}
```

---

#### `POST /meetings/{meeting_id}/sessions/{session_id}/attachments`

Upload an attachment to a session.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 3 requests / 60s |
| **Headers** | `Authorization: Bearer <token>`, `Content-Type: multipart/form-data` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `session_id` | UUID | Session ID |

**Request Body** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | File to upload |

**Success Response** `201 Created`

Returns the full `AttachmentResponse`.

---

#### `GET /meetings/{meeting_id}/sessions/{session_id}/attachments`

List all attachments for a session.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `session_id` | UUID | Session ID |

**Success Response** `200 OK`

Returns `AttachmentListResponse`.

---

#### `GET /meetings/{meeting_id}/sessions/{session_id}/attachments/{attachment_id}/download`

Download a session attachment.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `session_id` | UUID | Session ID |
| `attachment_id` | UUID | Attachment ID |

**Success Response** `200 OK`

Returns the file as `FileResponse`.

---

#### `DELETE /meetings/{meeting_id}/sessions/{session_id}/attachments/{attachment_id}`

Delete a session attachment.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `session_id` | UUID | Session ID |
| `attachment_id` | UUID | Attachment ID |

**Success Response** `200 OK`

```json
{
  "message": "Attachment deleted successfully."
}
```

---

### Meeting Analysis

Prefixed with `/api/v1/meetings/{meeting_id}/analysis`. All require authentication.

---

#### `GET /meetings/{meeting_id}/analysis`

Get the AI analysis result for a meeting's most recent session.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

Returns the full `AIAnalysisResponse`:

```json
{
  "id": "uuid",
  "session_id": "uuid",
  "provider": "nvidia-nim",
  "model": "meta/llama-3.1-70b-instruct",
  "status": "COMPLETED",
  "summary": "Meeting covered...",
  "agenda_coverage_percentage": 85,
  "covered_points": ["Point A", "Point B"],
  "out_of_agenda_points": ["Off-topic discussion"],
  "suggested_tasks": [
    {
      "title": "Follow up on action item",
      "description": "Details...",
      "priority": "HIGH"
    }
  ],
  "processing_started_at": "2025-07-20T10:00:00Z",
  "processing_completed_at": "2025-07-20T10:05:00Z",
  "created_at": "2025-07-20T10:00:00Z"
}
```

---

#### `GET /meetings/{meeting_id}/analysis/status`

Get the processing status of a meeting's AI analysis.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

```json
{
  "session_id": "uuid",
  "status": "COMPLETED",
  "processing_started_at": "2025-07-20T10:00:00Z",
  "processing_completed_at": "2025-07-20T10:05:00Z"
}
```

**Analysis Status Values**: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`

---

### Whiteboards

All endpoints are prefixed with `/api/v1/whiteboards`. All require authentication.

---

#### `POST /whiteboards`

Create a new whiteboard.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "title": "Architecture Diagram",
  "board_data": {
    "version": 1,
    "elements": []
  }
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | string | Yes | Min 1, max 255 chars, must not be blank | Whiteboard title |
| `board_data` | object | No | Default: `{"version": 1, "elements": []}` | Opaque board canvas data |

**Success Response** `201 Created`

Returns the full `WhiteboardResponse`.

---

#### `GET /whiteboards`

List whiteboards with filtering.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `is_archived` | boolean | `false` | Filter by archived status |
| `is_deleted` | boolean | `false` | Filter by deleted status |
| `is_favorite` | boolean | — | Filter by favorite status |
| `search` | string | — | Search term for title |

**Success Response** `200 OK`

Returns `List[WhiteboardResponse]`.

---

#### `GET /whiteboards/{id}`

Get a single whiteboard by ID.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Whiteboard ID |

**Success Response** `200 OK`

Returns the full `WhiteboardResponse`.

---

#### `PATCH /whiteboards/{id}`

Rename a whiteboard.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Whiteboard ID |

**Request Body** `application/json`

```json
{
  "title": "New Title"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | string | Yes | Min 1, max 255 chars, must not be blank | New title |

**Success Response** `200 OK`

Returns the updated `WhiteboardResponse`.

---

#### `PATCH /whiteboards/{id}/board`

Autosave whiteboard canvas data.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Whiteboard ID |

**Request Body** `application/json`

```json
{
  "board_data": {
    "version": 2,
    "elements": [ ... ]
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `board_data` | object | Yes | Updated canvas data payload |

**Success Response** `200 OK`

Returns the updated `WhiteboardResponse`.

---

#### `PATCH /whiteboards/{id}/favorite`

Toggle favorite status.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Whiteboard ID |

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `is_favorite` | boolean | Yes | New favorite status |

**Success Response** `200 OK`

Returns the updated `WhiteboardResponse`.

---

#### `PATCH /whiteboards/{id}/archive`

Toggle archive status.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Whiteboard ID |

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `is_archived` | boolean | Yes | New archive status |

**Success Response** `200 OK`

Returns the updated `WhiteboardResponse`.

---

#### `DELETE /whiteboards/{id}`

Soft-delete a whiteboard.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Whiteboard ID |

**Success Response** `200 OK`

```json
{
  "message": "Whiteboard deleted successfully."
}
```

---

#### `PATCH /whiteboards/{id}/restore`

Restore a soft-deleted whiteboard.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Whiteboard ID |

**Success Response** `200 OK`

Returns the restored `WhiteboardResponse`.

---

### Reminders

All endpoints are prefixed with `/api/v1/settings/reminders`. All require authentication.

---

#### `GET /settings/reminders`

Get the current user's reminder preferences.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Success Response** `200 OK`

```json
{
  "user_id": "uuid",
  "reminders_enabled": true,
  "schedule_all": true,
  "global_frequency": "DAILY",
  "global_time": "09:00:00",
  "calendar_config": {
    "enabled": true,
    "frequency": "DAILY",
    "time": "09:00:00"
  },
  "tasks_config": {
    "enabled": true,
    "frequency": "WEEKLY",
    "time": "08:00:00"
  },
  "meetings_config": {
    "enabled": false,
    "frequency": "DAILY",
    "time": "09:00:00"
  }
}
```

---

#### `PUT /settings/reminders`

Update the current user's reminder preferences.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "reminders_enabled": true,
  "schedule_all": false,
  "global_frequency": "WEEKLY",
  "global_time": "10:00:00",
  "calendar_config": {
    "enabled": true,
    "frequency": "DAILY",
    "time": "08:30:00"
  },
  "tasks_config": {
    "enabled": false,
    "frequency": "DAILY",
    "time": "09:00:00"
  },
  "meetings_config": {
    "enabled": true,
    "frequency": "WEEKLY",
    "time": "14:00:00"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reminders_enabled` | boolean | No | Master toggle |
| `schedule_all` | boolean | Yes | Apply global settings to all modules |
| `global_frequency` | string | No | `DAILY`, `WEEKLY`, or `MONTHLY` |
| `global_time` | time | No | Reminder time (HH:MM:SS) |
| `calendar_config` | object | No | Calendar-specific config |
| `calendar_config.enabled` | boolean | No | Default: `true` |
| `calendar_config.frequency` | string | No | Default: `DAILY` |
| `calendar_config.time` | time | Yes | Reminder time |
| `tasks_config` | object | No | Tasks-specific config (same shape) |
| `meetings_config` | object | No | Meetings-specific config (same shape) |

**Success Response** `200 OK`

Returns the updated `ReminderSettingResponse` (same shape as GET).

---

### Entity Links

All endpoints are prefixed with `/api/v1`. All require authentication.

---

#### `POST /entity-links`

Create a link between two entities (e.g., task to meeting).

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "source_type": "task",
  "source_id": "uuid",
  "target_type": "meeting",
  "target_id": "uuid",
  "link_type": "RELATED_TO",
  "relation_origin": "USER"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `source_type` | string | Yes | — | `meeting`, `meeting_session`, or `task` |
| `source_id` | UUID | Yes | — | Source entity ID |
| `target_type` | string | Yes | — | `meeting`, `meeting_session`, or `task` |
| `target_id` | UUID | Yes | — | Target entity ID |
| `link_type` | string | No | `RELATED_TO` | Relationship type |
| `relation_origin` | string | No | `USER` | Origin: `USER`, `SYSTEM`, or `AI` |

**Success Response** `201 Created`

Returns the full `EntityLinkResponse`.

---

#### `DELETE /entity-links/{link_id}`

Delete an entity link.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `link_id` | UUID | Entity link ID |

**Success Response** `200 OK`

```json
{
  "message": "Link deleted successfully."
}
```

---

#### `GET /entity-links`

List entity links with optional filters.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_type` | string | No | Filter by source entity type |
| `source_id` | UUID | No | Filter by source entity ID |
| `target_type` | string | No | Filter by target entity type |
| `target_id` | UUID | No | Filter by target entity ID |

**Success Response** `200 OK`

```json
{
  "links": [ ... ],
  "total_count": 12
}
```

---

#### `GET /meetings/{meeting_id}/linked-tasks`

List all tasks linked to a meeting.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |

**Success Response** `200 OK`

```json
[
  {
    "id": "uuid",
    "title": "Follow-up task",
    "priority": "HIGH",
    "status": "TODO",
    "due_date": "2025-07-25T17:00:00Z",
    "link_id": "uuid"
  }
]
```

---

#### `GET /meetings/{meeting_id}/sessions/{session_id}/linked-tasks`

List all tasks linked to a specific meeting session.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | UUID | Meeting ID |
| `session_id` | UUID | Session ID |

**Success Response** `200 OK`

Returns `List[LinkedTaskResponse]` (same shape as above).

---

#### `GET /tasks/{task_id}/linked-meetings`

List all meetings linked to a task.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Task ID |

**Success Response** `200 OK`

```json
[
  {
    "id": "uuid",
    "title": "Design Review",
    "status": "ACTIVE",
    "meeting_code": "abc-def-ghi",
    "scheduled_start": "2025-07-20T10:00:00Z",
    "link_id": "uuid",
    "session_id": "uuid"
  }
]
```

---

### AI Suggestions

All endpoints are prefixed with `/api/v1/ai-suggestions`. All require authentication.

---

#### `GET /ai-suggestions`

List all AI-generated task suggestions from an analysis.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 3 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analysis_id` | UUID | Yes | AI analysis ID to retrieve suggestions for |

**Success Response** `200 OK`

```json
{
  "suggestions": [
    {
      "id": "uuid",
      "analysis_id": "uuid",
      "title": "Review code changes",
      "description": "Review the PR mentioned in the meeting",
      "priority": "HIGH",
      "status": "PENDING",
      "created_task_id": null,
      "created_at": "2025-07-20T10:05:00Z"
    }
  ],
  "total_count": 5
}
```

---

#### `POST /ai-suggestions/{suggestion_id}/create-task`

Create a task from an AI suggestion.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 3 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `suggestion_id` | UUID | Suggestion ID |

**Request Body** `application/json` (optional)

```json
{
  "title": "Custom task title override"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Override the default suggestion title |

**Success Response** `200 OK`

Returns the updated `SuggestionResponse` with `status: "CREATED"` and `created_task_id` populated.

---

#### `POST /ai-suggestions/{suggestion_id}/reject`

Reject an AI suggestion.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 3 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `suggestion_id` | UUID | Suggestion ID |

**Success Response** `200 OK`

Returns the updated `SuggestionResponse` with `status: "REJECTED"`.

---

### Notifications

All endpoints are prefixed with `/api/v1/notifications`. All require authentication.

---

#### `POST /notifications/subscriptions`

Register a push notification subscription (Web Push).

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 10 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "endpoint": "https://fcm.googleapis.com/...",
  "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XHhrgnQg1sRkiYDxAWRtOA",
  "auth": "tBHItJI5svmE9jqxWT0fZA",
  "browser": "Chrome"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `endpoint` | string | Yes | Max 512 chars | Push service endpoint URL |
| `p256dh` | string | Yes | Max 256 chars | P256DH encryption key |
| `auth` | string | Yes | Max 256 chars | Auth secret |
| `browser` | string | No | Max 50 chars | Browser identifier |

**Success Response** `201 Created`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "endpoint": "https://fcm.googleapis.com/...",
  "browser": "Chrome",
  "created_at": "2025-07-20T10:00:00Z"
}
```

---

#### `DELETE /notifications/subscriptions`

Remove a push notification subscription.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `endpoint` | string | Yes | The subscription endpoint to remove |

**Success Response** `200 OK`

```json
{
  "message": "Subscription removed."
}
```

---

#### `GET /notifications`

List notifications with pagination and filtering.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | `1` | Page number |
| `page_size` | integer | `20` | Items per page |
| `search` | string | — | Search in title/body |
| `type` | string | — | Filter by `NotificationType` (e.g., `MEETING_REMINDER`) |

**Success Response** `200 OK`

```json
{
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "type": "MEETING_REMINDER",
      "title": "Meeting starting soon",
      "body": "Your meeting 'Design Review' starts in 5 minutes",
      "extra_data": { "meeting_id": "uuid" },
      "is_read": false,
      "sent_at": "2025-07-20T10:55:00Z",
      "created_at": "2025-07-20T10:55:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

---

#### `GET /notifications/unread-count`

Get the count of unread notifications.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Success Response** `200 OK`

```json
{
  "count": 7
}
```

---

#### `GET /notifications/recent`

Get the most recent notifications (unpaginated).

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Success Response** `200 OK`

Returns `List[NotificationResponse]`.

---

#### `GET /notifications/{notification_id}`

Get a single notification by ID.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `notification_id` | UUID | Notification ID |

**Success Response** `200 OK`

Returns the full `NotificationResponse`.

---

#### `POST /notifications/mark-read`

Mark specific notifications as read.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "notification_ids": ["uuid1", "uuid2"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `notification_ids` | array of UUIDs | Yes | IDs to mark as read |

**Success Response** `200 OK`

```json
{
  "message": "Notifications marked as read."
}
```

---

#### `POST /notifications/mark-all-read`

Mark all notifications as read.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Headers** | `Authorization: Bearer <token>` |

**Success Response** `200 OK`

```json
{
  "message": "All notifications marked as read."
}
```

---

### Attachments

All endpoints are prefixed with `/api/v1/attachments`. All require authentication.

---

#### `POST /attachments`

Upload a file attachment (multipart/form-data).

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 3 requests / 60s |
| **Headers** | `Authorization: Bearer <token>`, `Content-Type: multipart/form-data` |

**Request Body** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_type` | string | Yes | `TASK`, `CALENDAR_EVENT`, `MEETING_SESSION`, or `NOTE` |
| `entity_id` | UUID | Yes | ID of the parent entity |
| `file` | file | Yes | File to upload |

**Success Response** `201 Created`

Returns the full `AttachmentResponse`.

---

#### `POST /attachments/presigned-upload`

Generate a presigned upload URL for direct-to-storage uploads.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 10 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "entity_type": "TASK",
  "entity_id": "uuid",
  "filename": "document.pdf",
  "content_type": "application/pdf"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `entity_type` | string | Yes | — | `TASK`, `CALENDAR_EVENT`, `MEETING_SESSION`, or `NOTE` |
| `entity_id` | UUID | Yes | — | Parent entity ID |
| `filename` | string | Yes | Min 1, max 255 chars | Original filename |
| `content_type` | string | Yes | Min 1 char | MIME type |

**Success Response** `200 OK`

```json
{
  "upload_url": "https://storage.example.com/presigned-url",
  "key": "storage-key",
  "expires_in": 3600
}
```

---

#### `POST /attachments/confirm-upload`

Confirm a presigned upload was completed and register the attachment.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 10 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Request Body** `application/json`

```json
{
  "entity_type": "TASK",
  "entity_id": "uuid",
  "key": "storage-key",
  "original_filename": "document.pdf",
  "content_type": "application/pdf",
  "size": 1024000
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `entity_type` | string | Yes | — | Entity type |
| `entity_id` | UUID | Yes | — | Parent entity ID |
| `key` | string | Yes | Min 1 char | Storage key from presigned response |
| `original_filename` | string | Yes | Min 1, max 255 chars | Original filename |
| `content_type` | string | Yes | Min 1 char | MIME type |
| `size` | integer | Yes | Min: 1 | File size in bytes |

**Success Response** `201 Created`

Returns the full `AttachmentResponse`.

---

#### `GET /attachments/recent`

List recently uploaded attachments.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Query Parameters**

| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `limit` | integer | `10` | Min: 1, Max: 50 | Number of recent attachments |

**Success Response** `200 OK`

```json
{
  "attachments": [ ... ],
  "total_count": 10
}
```

---

#### `GET /attachments/{attachment_id}`

Get metadata for a specific attachment.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `attachment_id` | UUID | Attachment ID |

**Success Response** `200 OK`

Returns the full `AttachmentResponse`:

```json
{
  "id": "uuid",
  "owner_user_id": "uuid",
  "entity_type": "TASK",
  "entity_id": "uuid",
  "original_filename": "document.pdf",
  "stored_filename": "abc123.pdf",
  "content_type": "application/pdf",
  "extension": ".pdf",
  "size": 1024000,
  "storage_provider": "local",
  "created_at": "2025-07-20T10:00:00Z",
  "updated_at": "2025-07-20T10:00:00Z"
}
```

---

#### `GET /attachments/{attachment_id}/download`

Download an attachment file.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `attachment_id` | UUID | Attachment ID |

**Success Response** `200 OK`

Returns the file as `FileResponse` with appropriate headers.

---

#### `DELETE /attachments/{attachment_id}`

Delete an attachment.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 20 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `attachment_id` | UUID | Attachment ID |

**Success Response** `200 OK`

```json
{
  "message": "Attachment deleted successfully."
}
```

---

#### `GET /attachments`

List attachments for a specific entity.

| | |
|---|---|
| **Authentication** | Bearer token required |
| **Rate Limiting** | 60 requests / 60s |
| **Headers** | `Authorization: Bearer <token>` |

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_type` | string | Yes | `TASK`, `CALENDAR_EVENT`, `MEETING_SESSION`, or `NOTE` |
| `entity_id` | UUID | Yes | Parent entity ID |

**Success Response** `200 OK`

```json
{
  "attachments": [ ... ],
  "total_count": 5
}
```

---

### WebSocket

WebSocket endpoint for real-time meeting signaling.

---

#### `WS /ws/meetings/{meeting_id}`

Establish a WebSocket connection for WebRTC signaling in a meeting.

| | |
|---|---|
| **Authentication** | Optional (bearer token or guest credentials via query params) |

**Connection Parameters**

| Parameter | Type | Location | Description |
|-----------|------|----------|-------------|
| `meeting_id` | UUID | Path | Meeting ID |
| `token` | string | Query | JWT access token (for authenticated users) |
| `guest_name` | string | Query | Guest display name (for unauthenticated users) |
| `guest_email` | string | Query | Guest email (for unauthenticated users) |

**Connection URL**

```
ws://<host>[:<port>]/ws/meetings/{meeting_id}?token=<jwt_token>
```

or for guests:

```
ws://<host>[:<port>]/ws/meetings/{meeting_id}?guest_name=John&guest_email=john@example.com
```

**Signaling Protocol**

The WebSocket handles the full WebRTC lifecycle through JSON messages:

| Event | Direction | Description |
|-------|-----------|-------------|
| `join` | Client -> Server | Request to join the meeting |
| `waiting` | Server -> Client | Participant placed in waiting room |
| `admitted` | Server -> Client | Participant admitted to meeting |
| `rejected` | Server -> Client | Participant rejected from meeting |
| `offer` | Client -> Server | WebRTC SDP offer |
| `answer` | Client -> Server | WebRTC SDP answer |
| `ice-candidate` | Client -> Server | ICE candidate exchange |
| `mute` / `unmute` | Both | Audio mute state change |
| `screen-share-request` | Client -> Server | Request screen share permission |
| `screen-share-approved` | Server -> Client | Screen share permission granted |
| `screen-share-rejected` | Server -> Client | Screen share permission denied |
| `screen-share-started` | Server -> Client | Screen share stream started |
| `screen-share-stopped` | Server -> Client | Screen share stream stopped |
| `participant-joined` | Server -> Client | New participant notification |
| `participant-left` | Server -> Client | Participant departure notification |
| `leave` | Client -> Server | Voluntary departure |
| `disconnect` | Both | Connection closed |

> **Note:** This is a WebSocket endpoint, not a REST endpoint. It does not follow the standard HTTP request/response pattern.
