const GUEST_SESSION_KEY = "guest_session"

export function getGuestSession() {
  try {
    const raw = localStorage.getItem(GUEST_SESSION_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function saveGuestSession(session) {
  localStorage.setItem(GUEST_SESSION_KEY, JSON.stringify(session))
}

export function clearGuestSession() {
  localStorage.removeItem(GUEST_SESSION_KEY)
}

export function hasGuestSessionForMeeting(meetingId) {
  const session = getGuestSession()
  return session?.meetingId === meetingId
}

export function getGuestEmail() {
  const session = getGuestSession()
  return session?.guestEmail || null
}
