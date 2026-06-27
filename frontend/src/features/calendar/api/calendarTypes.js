/**
 * calendarTypes.js
 *
 * Single source of truth for all Calendar enum values and type definitions.
 * These MUST exactly match the backend Pydantic enums in:
 *   app/modules/calender/enums.py
 *
 * Never hard-code enum strings in components. Always import from here.
 */

// ---------------------------------------------------------------------------
// Backend enum values — uppercase, matching Python enums exactly
// ---------------------------------------------------------------------------

/** @enum {string} — matches backend EventType */
export const EventType = Object.freeze({
    PERSONAL: "PERSONAL",
    MEETING: "MEETING",
    REMINDER: "REMINDER",
})

/** @enum {string} — matches backend EventColor */
export const EventColor = Object.freeze({
    RED: "RED",
    BLUE: "BLUE",
    GREEN: "GREEN",
    YELLOW: "YELLOW",
    PURPLE: "PURPLE",
    ORANGE: "ORANGE",
    GRAY: "GRAY",
})

/** @enum {string} — matches backend RecurrenceFrequency */
export const RecurrenceFrequency = Object.freeze({
    DAILY: "DAILY",
    WEEKLY: "WEEKLY",
    MONTHLY: "MONTHLY",
})

// ---------------------------------------------------------------------------
// Arrays for iteration (dropdowns, filters, pickers)
// ---------------------------------------------------------------------------

export const EVENT_TYPE_OPTIONS = Object.values(EventType)
export const EVENT_COLOR_OPTIONS = Object.values(EventColor)
export const RECURRENCE_FREQUENCY_OPTIONS = Object.values(RecurrenceFrequency)

// ---------------------------------------------------------------------------
// Display labels (UI → lowercase, capitalised)
// ---------------------------------------------------------------------------

/** @type {Record<string, string>} */
export const EVENT_TYPE_LABELS = {
    PERSONAL: "Personal",
    MEETING: "Meeting",
    REMINDER: "Reminder",
}

/** @type {Record<string, string>} */
export const EVENT_COLOR_LABELS = {
    RED: "Red",
    BLUE: "Blue",
    GREEN: "Green",
    YELLOW: "Yellow",
    PURPLE: "Purple",
    ORANGE: "Orange",
    GRAY: "Gray",
}

/** @type {Record<string, string>} */
export const RECURRENCE_LABELS = {
    DAILY: "Daily",
    WEEKLY: "Weekly",
    MONTHLY: "Monthly",
}

// ---------------------------------------------------------------------------
// Hex colour swatches — keyed by EventColor enum value
// ---------------------------------------------------------------------------

/** @type {Record<string, string>} */
export const EVENT_COLOR_HEX = {
    RED: "#ef4444",
    BLUE: "#3b82f6",
    GREEN: "#10b981",
    YELLOW: "#f59e0b",
    PURPLE: "#a855f7",
    ORANGE: "#f97316",
    GRAY: "#6b7280",
}

// ---------------------------------------------------------------------------
// Tailwind class bundles — keyed by EventColor enum value
// ---------------------------------------------------------------------------

/**
 * @typedef {{ bg: string, dot: string, faint: string }} ColorClasses
 * @type {Record<string, ColorClasses>}
 */
export const EVENT_COLOR_CLASSES = {
    RED: { bg: "bg-red-500", dot: "bg-red-500", faint: "bg-red-50    text-red-700    border-red-200" },
    BLUE: { bg: "bg-blue-500", dot: "bg-blue-500", faint: "bg-blue-50   text-blue-700   border-blue-200" },
    GREEN: { bg: "bg-emerald-500", dot: "bg-emerald-500", faint: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    YELLOW: { bg: "bg-amber-400", dot: "bg-amber-400", faint: "bg-amber-50  text-amber-700  border-amber-200" },
    PURPLE: { bg: "bg-purple-500", dot: "bg-purple-500", faint: "bg-purple-50 text-purple-700 border-purple-200" },
    ORANGE: { bg: "bg-orange-500", dot: "bg-orange-500", faint: "bg-orange-50 text-orange-700 border-orange-200" },
    GRAY: { bg: "bg-gray-400", dot: "bg-gray-400", faint: "bg-gray-50   text-gray-700   border-gray-200" },
}

// ---------------------------------------------------------------------------
// JSDoc typedefs — backend response shapes
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} CalendarEventResponse
 * Backend: CalendarEventResponse (from CRUD endpoints)
 * @property {string}  id
 * @property {string}  user_id
 * @property {string}  title
 * @property {string|null} description
 * @property {string}  event_type           - EventType enum
 * @property {string}  color                - EventColor enum
 * @property {string}  start_time           - ISO 8601 with tz offset
 * @property {string}  end_time             - ISO 8601 with tz offset
 * @property {string}  timezone             - IANA string
 * @property {boolean} is_all_day
 * @property {string|null} location
 * @property {string|null} recurrence_frequency  - RecurrenceFrequency enum
 * @property {number|null} recurrence_interval
 * @property {string|null} recurrence_end_date   - ISO 8601 with tz offset
 * @property {string}  created_at
 * @property {string}  updated_at
 */

/**
 * @typedef {Object} CalendarOccurrence
 * Backend: CalendarOccurrenceResponse (from list endpoint)
 * @property {string}  id
 * @property {string}  title
 * @property {string|null} description
 * @property {string}  event_type
 * @property {string}  color
 * @property {string}  start_time
 * @property {string}  end_time
 * @property {string}  timezone
 * @property {boolean} is_all_day
 * @property {string|null} location
 * @property {boolean} is_recurring
 * @property {string|null} recurrence_frequency
 * @property {number|null} recurrence_interval
 * @property {string|null} recurrence_end_date
 */

/**
 * @typedef {Object} CreateEventPayload
 * Backend: CalendarEventCreate
 * @property {string}  title
 * @property {string|null} description
 * @property {string}  event_type
 * @property {string}  color
 * @property {string}  start_time           - ISO 8601 with tz offset (required)
 * @property {string}  end_time             - ISO 8601 with tz offset (required)
 * @property {string}  timezone
 * @property {boolean} is_all_day
 * @property {string|null} location
 * @property {string|null} recurrence_frequency
 * @property {number|null} recurrence_interval
 * @property {string|null} recurrence_end_date  - ISO 8601 with tz offset
 */

/**
 * @typedef {Object} ListEventsParams
 * @property {string}  start        - ISO 8601 datetime (required)
 * @property {string}  end          - ISO 8601 datetime (required)
 * @property {string}  [search]
 * @property {string}  [event_type] - EventType enum value
 * @property {string}  [color]      - EventColor enum value
 */
