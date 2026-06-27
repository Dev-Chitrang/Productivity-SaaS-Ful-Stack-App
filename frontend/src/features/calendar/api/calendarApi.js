/**
 * calendarApi.js
 *
 * Axios request functions for every Calendar endpoint.
 * This is the ONLY place that knows the endpoint URLs.
 *
 * All serialization/deserialization is handled by calendarMapper.js.
 * All type definitions live in calendarTypes.js.
 */

import api from "@/lib/axios"

// ---------------------------------------------------------------------------
// CRUD
// ---------------------------------------------------------------------------

/**
 * POST /calendar/events
 * @param {import("./calendarTypes").CreateEventPayload} payload
 */
export const createEvent = (payload) => api.post("/calendar/events", payload)

/**
 * GET /calendar/events/{id}
 * @param {string} id - UUID string
 */
export const getEvent = (id) => api.get(`/calendar/events/${id}`)

/**
 * PATCH /calendar/events/{id}
 * @param {string} id
 * @param {object} payload
 */
export const updateEvent = (id, payload) => api.patch(`/calendar/events/${id}`, payload)

/**
 * DELETE /calendar/events/{id}
 * @param {string} id
 */
export const deleteEvent = (id) => api.delete(`/calendar/events/${id}`)

// ---------------------------------------------------------------------------
// List / query
// ---------------------------------------------------------------------------

/**
 * GET /calendar/events
 *
 * Returns a flat list of CalendarOccurrenceResponse objects.
 * The `start` and `end` params must be timezone-aware ISO 8601 strings.
 * Undefined/null filter values are stripped before sending.
 *
 * @param {import("./calendarTypes").ListEventsParams} params
 */
export const listEvents = (params) => {
    // Strip any undefined/null/empty-string values so FastAPI doesn't receive
    // empty query parameters that could trigger enum validation failures.
    const clean = Object.fromEntries(
        Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""),
    )
    return api.get("/calendar/events", { params: clean })
}
