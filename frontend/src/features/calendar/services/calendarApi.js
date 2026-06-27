import api from "@/lib/axios"

/**
 * @typedef {Object} CalendarEvent
 * @property {string}  id                      - UUID (original event / series anchor)
 * @property {string}  title
 * @property {string}  [description]
 * @property {string}  event_type              - EventType enum value  (e.g. "MEETING")
 * @property {string}  color                   - EventColor enum value (e.g. "BLUE")
 * @property {string}  start_time              - ISO 8601 datetime with timezone
 * @property {string}  end_time                - ISO 8601 datetime with timezone
 * @property {string}  timezone                - IANA timezone string  (e.g. "Asia/Kolkata")
 * @property {boolean} is_all_day
 * @property {string}  [location]
 * @property {boolean} is_recurring
 * @property {string}  [recurrence_frequency]  - "DAILY" | "WEEKLY" | "MONTHLY"
 * @property {number}  [recurrence_interval]
 * @property {string}  [recurrence_end_date]   - ISO 8601 datetime
 */

/**
 * @typedef {Object} ListEventsParams
 * @property {string}  start        - ISO 8601 datetime (required)
 * @property {string}  end          - ISO 8601 datetime (required)
 * @property {string}  [search]     - Full-text search string
 * @property {string}  [event_type] - EventType enum value
 * @property {string}  [color]      - EventColor enum value
 */

export const calendarApi = {
    /** Create a new event — returns CalendarEventResponse */
    createEvent: (data) => api.post("/calendar/events", data),

    /**
     * List events within a date range.
     * This is the single endpoint used by every calendar view.
     * @param {ListEventsParams} params
     */
    listEvents: (params) => api.get("/calendar/events", { params }),

    /** Retrieve a single event by id — returns CalendarEventResponse */
    getEvent: (id) => api.get(`/calendar/events/${id}`),

    /** Partially update an existing event — returns CalendarEventResponse */
    updateEvent: (id, data) => api.patch(`/calendar/events/${id}`, data),

    /** Soft-delete an event */
    deleteEvent: (id) => api.delete(`/calendar/events/${id}`),
}
