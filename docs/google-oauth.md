# Google OAuth (GIS) Integration

This document is the single source of truth for Google Identity Services (GIS) integration in the Productivity Suite.

---

## Architecture Overview

The application uses Google Identity Services with the **One Tap / Sign in with Google popup flow**. This is **not** the OAuth Authorization Code flow.

```
Browser (React)                         Backend (FastAPI)
─────────────                           ────────────────
1. Load GIS script from Google
2. Initialize google.accounts.id
3. User clicks "Continue with Google"
4. Google popup → user consents
5. Receives Google ID Token (JWT)
   ─────── POST /api/v1/auth/google ──────►
                                        6. Verify ID token with Google's public keys
                                        7. Extract sub, email, name, picture
                                        8. Find or create user
                                        9. Issue JWT access + refresh tokens
   ◄────────── { access_token } ───────────
10. Store tokens, redirect to dashboard
```

---

## Frontend Responsibilities

### Google Identity Services Script

Loaded dynamically from `https://accounts.google.com/gsi/client` when the auth page mounts. The script provides the `window.google.accounts.id` API.

### Initialization

```js
window.google.accounts.id.initialize({
  client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
  callback: handleCredentialResponse,  // receives { credential: "..." }
  auto_select: false,
  cancel_on_tap_outside: true,
});
```

The `credential` field in the callback response is a **Google ID Token** (a signed JWT). It is **not** an OAuth access token.

### Credential Handling

The `useGoogleOAuth` hook (`frontend/src/features/auth/hooks/useAuth.js`):

1. Receives the raw `credential` (ID token) from the GIS callback
2. Calls `authApi.googleLogin(id_token)` → `POST /api/v1/auth/google` with `{ id_token: "..." }`
3. Backend verifies and returns JWT tokens
4. If `requires_2fa` is true, navigates to 2FA verification
5. Otherwise, stores the access token and redirects to dashboard

### Token Refresh

The GIS script also attempts to silently refresh the Google session on subsequent page loads. If the user is already signed into Google, `auto_select` can present One Tap without user interaction. The `cancel_on_tap_outside: true` setting allows users to dismiss the prompt.

---

## Backend Responsibilities

### Endpoint

```
POST /api/v1/auth/google
Content-Type: application/json

{
  "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "requires_2fa": false
}
```

**Response with 2FA (200):**
```json
{
  "access_token": null,
  "token_type": "bearer",
  "requires_2fa": true,
  "verification_token": "..."
}
```

**Rate limit:** 3 requests per 60 seconds per IP.

### ID Token Verification

The backend uses the `google-auth` library to verify the ID token server-side:

```python
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

_GOOGLE_REQUEST = google_requests.Request()  # reusable transport

idinfo = google_id_token.verify_oauth2_token(
    raw_id_token,
    _GOOGLE_REQUEST,
    settings.GOOGLE_CLIENT_ID,
)
```

This performs:
- **Signature verification** against Google's public keys (fetched and cached by `google-auth`)
- **Issuer check** — must be `https://accounts.google.com` or `accounts.google.com`
- **Audience check** — must match `GOOGLE_CLIENT_ID`
- **Expiry check** — token must not be expired

### User Resolution Logic

After verification, the backend extracts:
- `sub` — Google's unique user ID
- `email` — user's email address
- `name` — display name (optional)
- `picture` — profile photo URL (optional)

Resolution priority:
1. **Find by `google_id`** — fastest path, user has logged in with Google before
2. **Find by email** — if a password-based account exists with the same email, link Google to it (account merging)
3. **Create new user** — no existing account, create one with `auth_provider="google"`

### Account Linking

When a password-based account exists with the same email as the Google account:
- The Google ID is linked to the existing user (`link_google_account`)
- The user can subsequently log in via either method

---

## Environment Variables

| Variable | Set In | Purpose |
|---|---|---|
| `VITE_GOOGLE_CLIENT_ID` | `APP_ENV` secret (frontend) | Client ID passed to GIS initialization |
| `GOOGLE_CLIENT_ID` | `APP_ENV` secret (backend) | Used to verify ID tokens server-side |

### Variables NOT Used

| Variable | Why Not Used |
|---|---|
| `GOOGLE_CLIENT_SECRET` | Not needed — popup flow never exchanges an authorization code |
| `GOOGLE_REDIRECT_URI` | Not needed — no server-side redirect, no authorization code flow |

---

## Google Cloud Console Configuration

### OAuth 2.0 Client ID

The project uses a **Web application** type OAuth 2.0 Client ID.

**Authorized JavaScript origins:**
- `https://unified-workspace.duckdns.org` (production)
- `http://localhost:5173` (Vite dev server)
- `http://localhost:5174` (Vite dev server alternate)

**Authorized redirect URIs:**
- Not required for the popup flow, but typically configured for other OAuth flows if needed later

### Required APIs

- **Google Identity Services API** — must be enabled in the Google Cloud project
- No other Google APIs are required

### Consent Screen

- **User type:** External
- **App name:** Productivity Suite
- **Scopes:** `openid`, `email`, `profile` (basic info)

---

## Flow Diagrams

### New Google User

```
Browser                    Google                    Backend
  |                          |                          |
  |-- initialize GIS ------>|                          |
  |-- user clicks sign in ->|                          |
  |   <-- popup consent --->|                          |
  |-- credential (ID tok) ->|                          |
  |                     [user consents]                 |
  |<-- { credential } ------|                          |
  |-- POST /auth/google ----------------------------->|
  |                          |   verify_oauth2_token -->|
  |                          |   <-- idinfo ------------|
  |                          |   create user            |
  |                          |   issue JWT tokens       |
  |<-- { access_token } -------------------------------|
  |   store in AuthContext                            |
  |   redirect to /dashboard                          |
```

### Existing Password User (Account Linking)

```
Browser                    Google                    Backend
  |                          |                          |
  |-- POST /auth/google ----------------------------->|
  |                          |   verify_oauth2_token -->|
  |                          |   <-- idinfo ------------|
  |                          |   find by email          |
  |                          |   link Google ID         |
  |<-- { access_token } -------------------------------|
```

### Existing Google User (Returning)

```
Browser                    Google                    Backend
  |                          |                          |
  |-- POST /auth/google ----------------------------->|
  |                          |   verify_oauth2_token -->|
  |                          |   <-- idinfo ------------|
  |                          |   find by google_id      |
  |<-- { access_token } -------------------------------|
```

### User with 2FA Enabled

```
Browser                    Backend
  |-- POST /auth/google -->|
  |   verify token         |
  |   find user (has 2fa)  |
  |<-- { requires_2fa: true, verification_token } --|
  |-- show OTP form ------>|
  |-- POST /auth/verify-signup-otp -->|
  |   verify OTP           |
  |   issue JWT tokens     |
  |<-- { access_token } ---|
```

---

## Error Cases

| Error | HTTP Status | Cause |
|---|---|---|
| `Google token verification failed` | 401 | Invalid, expired, or tampered ID token |
| `User not found` | 401 | 2FA verification token invalid |
| Rate limit exceeded | 429 | More than 3 requests per 60 seconds |

---

## Security Notes

- The ID token is verified **server-side** using Google's public keys. The backend never trusts the token blindly.
- `GOOGLE_CLIENT_ID` is validated against the token's audience field, preventing tokens from other GCP projects from being accepted.
- The `google-auth` library automatically fetches and caches Google's public signing keys.
- The reusable `_GOOGLE_REQUEST` transport object avoids creating a new HTTP session per verification call.
- The endpoint is rate-limited to 3 requests per 60 seconds per IP to prevent abuse.
