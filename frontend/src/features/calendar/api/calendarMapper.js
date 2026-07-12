/**
 * calendarMapper.js
 *
 * The single place responsible for:
 *   - Converting UI form values → backend DTOs  (toCreatePayload / toUpdatePayload)
 *   - Serializing local date+time+timezone → ISO 8601 with tz offset
 *   - Converting backend response fields → UI display values
 *   - 12-hour UI time ↔ HH:mm internal representation
 *
 * No component or hook should perform datetime serialization directly.
 * All Calendar API transformations go through this module.
 */

import dayjs from "dayjs"
import utc from "dayjs/plugin/utc"
import timezone from "dayjs/plugin/timezone"
import { EventType, EventColor, RecurrenceFrequency } from "./calendarTypes"

dayjs.extend(utc)
dayjs.extend(timezone)

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/**
 * Builds a timezone-aware ISO 8601 string from separate date, HH:mm, and
 * IANA timezone strings.
 *
 * Examples:
 *   toISOWithTz("2026-06-25", "09:30", "Asia/Kolkata")
 *   → "2026-06-25T09:30:00+05:30"
 *
 * @param {string} dateStr  - "YYYY-MM-DD"
 * @param {string} timeStr  - "HH:mm"
 * @param {string} tz       - IANA timezone (e.g. "Asia/Kolkata")
 * @returns {string}
 */
export function toISOWithTz(dateStr, timeStr, tz) {
    return dayjs.tz(`${dateStr}T${timeStr}`, tz).format()
}

/**
 * Converts a 12-hour UI time object to an HH:mm string.
 *
 * @param {string} hour   - "1"–"12"
 * @param {string} minute - "00"–"59"
 * @param {string} ampm   - "AM" | "PM"
 * @returns {string} "HH:mm"
 */
export function ampmToHHmm(hour, minute, ampm) {
    let h = parseInt(hour, 10)
    if (ampm === "AM" && h === 12) h = 0
    if (ampm === "PM" && h !== 12) h += 12
    return `${String(h).padStart(2, "0")}:${minute}`
}

/**
 * Converts an HH:mm string to a 12-hour display object.
 *
 * @param {string} hhmm - "HH:mm"
 * @returns {{ hour: string, minute: string, ampm: "AM"|"PM" }}
 */
export function hhmmToAmpm(hhmm) {
    const [hStr, mStr] = hhmm.split(":")
    const h = parseInt(hStr, 10)
    const ampm = h < 12 ? "AM" : "PM"
    const hour12 = h === 0 ? 12 : h > 12 ? h - 12 : h
    return { hour: String(hour12), minute: mStr ?? "00", ampm }
}

/**
 * Formats a backend ISO datetime string for display: "9:30 AM"
 * @param {string} isoStr
 * @returns {string}
 */
export function fmtDisplayTime(isoStr) {
    return dayjs(isoStr).format("h:mm A")
}

/**
 * Formats a backend ISO datetime string as a short date: "Mon, Jun 25"
 * @param {string} isoStr
 * @returns {string}
 */
export function fmtDisplayDate(isoStr) {
    return dayjs(isoStr).format("ddd, MMM D")
}

/**
 * Formats a time range for display: "9:00 – 10:30 AM"
 * @param {string} startIso
 * @param {string} endIso
 * @returns {string}
 */
export function fmtDisplayTimeRange(startIso, endIso) {
    const s = dayjs(startIso)
    const e = dayjs(endIso)
    if (s.format("A") === e.format("A")) {
        return `${s.format("h:mm")} – ${e.format("h:mm A")}`
    }
    return `${s.format("h:mm A")} – ${e.format("h:mm A")}`
}

/**
 * Returns a human-readable recurrence label: "Weekly" / "Every 2 weeks"
 * @param {import("./calendarTypes").CalendarOccurrence} event
 * @returns {string|null}
 */
export function fmtRecurrenceLabel(event) {
    if (!event.is_recurring || !event.recurrence_frequency) return null
    const interval = event.recurrence_interval ?? 1
    const freq = event.recurrence_frequency // already uppercase from backend
    if (interval === 1) {
        return { DAILY: "Daily", WEEKLY: "Weekly", MONTHLY: "Monthly" }[freq] ?? freq
    }
    const unit = { DAILY: "days", WEEKLY: "weeks", MONTHLY: "months" }[freq] ?? "periods"
    return `Every ${interval} ${unit}`
}

// ---------------------------------------------------------------------------
// Enum normalisation helpers
// ---------------------------------------------------------------------------

/**
 * Normalises a color value to a valid EventColor enum string.
 * Falls back to BLUE for any unrecognised value (e.g. legacy "indigo", "pink").
 * @param {string} raw
 * @returns {string}
 */
export function normaliseColor(raw) {
    if (!raw) return EventColor.BLUE
    const upper = raw.toUpperCase()
    return Object.values(EventColor).includes(upper) ? upper : EventColor.BLUE
}

/**
 * Normalises an event_type value to a valid EventType enum string.
 * Falls back to PERSONAL for any unrecognised value (e.g. legacy "task", "other").
 * @param {string} raw
 * @returns {string}
 */
export function normaliseEventType(raw) {
    if (!raw) return EventType.PERSONAL
    const upper = raw.toUpperCase()
    return Object.values(EventType).includes(upper) ? upper : EventType.PERSONAL
}

/**
 * Normalises a recurrence frequency to a valid enum string.
 * Falls back to WEEKLY for any unrecognised value (e.g. legacy "yearly").
 * @param {string} raw
 * @returns {string}
 */
export function normaliseFrequency(raw) {
    if (!raw) return RecurrenceFrequency.WEEKLY
    const upper = raw.toUpperCase()
    return Object.values(RecurrenceFrequency).includes(upper) ? upper : RecurrenceFrequency.WEEKLY
}

// ---------------------------------------------------------------------------
// Form default builders
// ---------------------------------------------------------------------------

/**
 * Builds default form values for the Create Event form.
 * All times stored internally as HH:mm; enums are uppercase backend values.
 *
 * @param {string|null} anchorDate   - "YYYY-MM-DD" or null for today
 * @param {string|null} anchorHHmm  - "HH:mm" or null for current time
 * @param {string|null} [userTimezone] - user.timezone from profile (preferred over browser)
 * @returns {object}
 */
export function buildCreateDefaults(anchorDate, anchorHHmm, userTimezone) {
    const base = anchorDate ? dayjs(anchorDate) : dayjs()
    const userTz = userTimezone || Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"
    const now = dayjs()

    let startHH
    if (anchorHHmm != null) {
        startHH = anchorHHmm
    } else {
        // Round to the next half-hour
        const minutes = now.minute()
        const hour = now.hour()
        if (minutes < 30) {
            startHH = `${String(hour).padStart(2, "0")}:30`
        } else {
            const nextHour = (hour + 1) % 24
            startHH = `${String(nextHour).padStart(2, "0")}:00`
        }
    }

    const endHH = dayjs(`${base.format("YYYY-MM-DD")}T${startHH}`)
        .add(1, "hour")
        .format("HH:mm")

    return {
        title: "",
        description: "",
        event_type: EventType.PERSONAL,
        start_date: base.format("YYYY-MM-DD"),
        start_hhmm: startHH,
        end_date: base.format("YYYY-MM-DD"),
        end_hhmm: endHH,
        timezone: userTz,
        is_all_day: false,
        location: "",
        color: EventColor.BLUE,
        is_recurring: false,
        recurrence_frequency: RecurrenceFrequency.WEEKLY,
        recurrence_interval: 1,
        recurrence_end_date: "",
    }
}

/**
 * Builds pre-populated form values from a backend CalendarEventResponse
 * or CalendarOccurrence. Converts backend fields to internal form representation.
 *
 * Note: The CRUD response (CalendarEventResponse) does not include is_recurring;
 * the list response (CalendarOccurrence) does. We derive is_recurring from
 * recurrence_frequency when the field is absent.
 *
 * @param {import("./calendarTypes").CalendarEventResponse|import("./calendarTypes").CalendarOccurrence} event
 * @returns {object}
 */
export function buildEditDefaults(event) {
    const hasRecurrence = event.is_recurring ?? !!event.recurrence_frequency
    return {
        title: event.title ?? "",
        description: event.description ?? "",
        event_type: normaliseEventType(event.event_type),
        start_date: dayjs(event.start_time).format("YYYY-MM-DD"),
        start_hhmm: dayjs(event.start_time).format("HH:mm"),
        end_date: dayjs(event.end_time).format("YYYY-MM-DD"),
        end_hhmm: dayjs(event.end_time).format("HH:mm"),
        timezone: event.timezone ?? "UTC",
        is_all_day: event.is_all_day ?? false,
        location: event.location ?? "",
        color: normaliseColor(event.color),
        is_recurring: hasRecurrence,
        recurrence_frequency: normaliseFrequency(event.recurrence_frequency),
        recurrence_interval: event.recurrence_interval ?? 1,
        recurrence_end_date: event.recurrence_end_date
            ? dayjs(event.recurrence_end_date).format("YYYY-MM-DD")
            : "",
    }
}

// ---------------------------------------------------------------------------
// Request payload builders
// ---------------------------------------------------------------------------

/**
 * Converts validated form values → CreateEventPayload for POST /calendar/events.
 *
 * Key contract rules enforced here:
 *  - start_time / end_time must be timezone-aware ISO 8601 strings
 *  - field names match backend exactly (event_type, is_all_day, start_time, end_time)
 *  - recurrence fields only sent when is_recurring is true
 *  - recurrence_end_date sent as full ISO datetime (not bare date)
 *
 * @param {object} formValues - validated form values from useForm
 * @returns {import("./calendarTypes").CreateEventPayload}
 */
export function toCreatePayload(formValues) {
    const {
        title,
        description,
        event_type,
        color,
        start_date,
        start_hhmm,
        end_date,
        end_hhmm,
        timezone: tz,
        is_all_day,
        location,
        is_recurring,
        recurrence_frequency,
        recurrence_interval,
        recurrence_end_date,
    } = formValues

    const payload = {
        title: title.trim(),
        description: description || null,
        event_type: normaliseEventType(event_type),
        color: normaliseColor(color),
        // Serialize as timezone-aware ISO 8601 string
        start_time: is_all_day
            ? toISOWithTz(start_date, "00:00", tz)
            : toISOWithTz(start_date, start_hhmm, tz),
        end_time: is_all_day
            ? toISOWithTz(end_date, "23:59", tz)
            : toISOWithTz(end_date, end_hhmm, tz),
        timezone: tz,
        is_all_day: Boolean(is_all_day),
        location: location || null,
        // Recurrence fields — only include when the event is recurring
        recurrence_frequency: is_recurring ? normaliseFrequency(recurrence_frequency) : null,
        recurrence_interval: is_recurring ? (recurrence_interval ?? 1) : null,
        recurrence_end_date: (is_recurring && recurrence_end_date)
            ? toISOWithTz(recurrence_end_date, "23:59", tz)
            : null,
    }

    return payload
}

/**
 * Converts validated form values → UpdateEventPayload for PATCH /calendar/events/{id}.
 * Only includes fields that have changed (exclude_unset semantics mirrored client-side).
 *
 * @param {object} formValues
 * @returns {object}
 */
export function toUpdatePayload(formValues) {
    // For PATCH we send everything — backend uses exclude_unset so null fields are fine.
    // We reuse the same transformation as create.
    return toCreatePayload(formValues)
}
