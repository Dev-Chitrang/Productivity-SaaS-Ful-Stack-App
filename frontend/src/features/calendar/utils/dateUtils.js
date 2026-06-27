/**
 * dateUtils.js
 *
 * Pure date/time utilities for calendar grid calculations and formatting.
 * No API serialization lives here — that belongs in api/calendarMapper.js.
 */

import dayjs from "dayjs"
import utc from "dayjs/plugin/utc"
import timezone from "dayjs/plugin/timezone"
import weekOfYear from "dayjs/plugin/weekOfYear"
import isoWeek from "dayjs/plugin/isoWeek"
import isSameOrBefore from "dayjs/plugin/isSameOrBefore"
import isBetween from "dayjs/plugin/isBetween"

dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.extend(weekOfYear)
dayjs.extend(isoWeek)
dayjs.extend(isSameOrBefore)
dayjs.extend(isBetween)

export { dayjs }

// ---------------------------------------------------------------------------
// Display formatters
// ---------------------------------------------------------------------------

/** "Mon, Jan 5" */
export const fmtShortDate = (d) => dayjs(d).format("ddd, MMM D")

/** "January 2025" */
export const fmtMonthYear = (d) => dayjs(d).format("MMMM YYYY")

/** "Jan 5 – 11, 2025" */
export const fmtWeekRange = (anchor) => {
    const start = dayjs(anchor).startOf("isoWeek")
    const end = dayjs(anchor).endOf("isoWeek")
    if (start.month() === end.month()) {
        return `${start.format("MMM D")} – ${end.format("D, YYYY")}`
    }
    return `${start.format("MMM D")} – ${end.format("MMM D, YYYY")}`
}

/** "9:00 AM" */
export const fmtTime = (d) => dayjs(d).format("h:mm A")

/** "9:00 – 10:00 AM" */
export const fmtTimeRange = (start, end) => {
    const s = dayjs(start)
    const e = dayjs(end)
    if (s.format("A") === e.format("A")) return `${s.format("h:mm")} – ${e.format("h:mm A")}`
    return `${s.format("h:mm A")} – ${e.format("h:mm A")}`
}

// ---------------------------------------------------------------------------
// Event positioning — shared by WeekGrid and DayTimeline
// ---------------------------------------------------------------------------

/** Vertical pixels per hour — single source of truth */
export const CELL_HEIGHT = 48

/**
 * Consistent minimum height for event cards in week/day views.
 * Cards fill their starting hour slot up to this height.
 */
export const MIN_CARD_HEIGHT = CELL_HEIGHT

/**
 * Returns the hour label for a given hour (0–23).
 * Shows "12 AM" for h=0, "1 AM" for h=1, etc.
 */
export function getHourLabel(h) {
    return dayjs().startOf("day").add(h, "hour").format("h A")
}

/** 0–23 */
export const HOURS = Array.from({ length: 24 }, (_, i) => i)

/**
 * Assigns overlapping events into columns so they render side by side.
 * Returns events with column/totalColumns metadata.
 * @param {import("../api/calendarTypes").CalendarOccurrence[]} events
 * @returns {Array<{ event: object, column: number, totalColumns: number }>}
 */
export function assignColumns(events) {
    if (events.length === 0) return []
    const sorted = [...events].sort((a, b) => dayjs(a.start_time).diff(dayjs(b.start_time)))
    const columns = []
    const result = sorted.map((ev) => {
        const evStart = dayjs(ev.start_time).valueOf()
        const evEnd = dayjs(ev.end_time).valueOf()
        let col = 0
        while (col < columns.length && columns[col] > evStart) col++
        if (col >= columns.length) columns.push(evEnd)
        else columns[col] = evEnd
        return { event: ev, column: col }
    })
    const totalColumns = Math.max(result.length > 0 ? Math.max(...result.map((r) => r.column)) + 1 : 1, 1)
    return result.map((r) => ({ ...r, totalColumns }))
}

// ---------------------------------------------------------------------------
// Grid builders
// ---------------------------------------------------------------------------

/** Returns 42 dayjs objects for a 6-week month grid (ISO weeks, Mon–Sun) */
export const getMonthGrid = (anchor) => {
    const start = dayjs(anchor).startOf("month").startOf("isoWeek")
    return Array.from({ length: 42 }, (_, i) => start.add(i, "day"))
}

/** Returns 7 dayjs objects for the ISO week containing `anchor` (Mon–Sun) */
export const getWeekDays = (anchor) => {
    const start = dayjs(anchor).startOf("isoWeek")
    return Array.from({ length: 7 }, (_, i) => start.add(i, "day"))
}

// ---------------------------------------------------------------------------
// Comparison helpers
// ---------------------------------------------------------------------------

/** true if `d` is today */
export const isToday = (d) => dayjs(d).isSame(dayjs(), "day")

/** true if `d` is in the same calendar month as `anchor` */
export const isSameMonth = (d, anchor) => dayjs(d).isSame(dayjs(anchor), "month")

// ---------------------------------------------------------------------------
// Serialization helpers (non-API — for URL params and internal state)
// ---------------------------------------------------------------------------

/** "YYYY-MM-DD" */
export const toISODate = (d) => dayjs(d).format("YYYY-MM-DD")

/**
 * Full UTC ISO 8601 string with explicit offset, e.g. "2026-06-25T04:00:00.000+00:00"
 * Uses +00:00 instead of Z for broadest compatibility with backend datetime parsers.
 */
export const toISODateTime = (d) => {
    const dt = dayjs(d).utc()
    return `${dt.format("YYYY-MM-DDTHH:mm:ss.SSS")}+00:00`
}

// ---------------------------------------------------------------------------
// View range helpers — compute the API [start, end] window for each view
// ---------------------------------------------------------------------------

/**
 * @param {string} anchorDate "YYYY-MM-DD"
 * @returns {{ start: string, end: string }}
 */
export const getMonthViewRange = (anchorDate) => {
    const d = dayjs(anchorDate)
    return {
        start: toISODateTime(d.startOf("month").startOf("isoWeek").startOf("day")),
        end: toISODateTime(d.endOf("month").endOf("isoWeek").endOf("day")),
    }
}

/**
 * @param {string} anchorDate "YYYY-MM-DD"
 * @returns {{ start: string, end: string }}
 */
export const getWeekViewRange = (anchorDate) => {
    const d = dayjs(anchorDate)
    return {
        start: toISODateTime(d.startOf("isoWeek").startOf("day")),
        end: toISODateTime(d.endOf("isoWeek").endOf("day")),
    }
}

/**
 * @param {string} anchorDate "YYYY-MM-DD"
 * @returns {{ start: string, end: string }}
 */
export const getDayViewRange = (anchorDate) => {
    const d = dayjs(anchorDate)
    return {
        start: toISODateTime(d.startOf("day")),
        end: toISODateTime(d.endOf("day")),
    }
}

/**
 * @param {string} anchorDate "YYYY-MM-DD"
 * @returns {{ start: string, end: string }}
 */
export const getAgendaViewRange = (anchorDate) => {
    const d = dayjs(anchorDate)
    return {
        start: toISODateTime(d.startOf("day")),
        end: toISODateTime(d.add(3, "month").endOf("day")),
    }
}

/**
 * Dispatches to the correct range helper.
 * @param {"month"|"week"|"day"|"agenda"} view
 * @param {string} anchorDate
 * @returns {{ start: string, end: string }}
 */
export const getViewDateRange = (view, anchorDate) => {
    switch (view) {
        case "month": return getMonthViewRange(anchorDate)
        case "week": return getWeekViewRange(anchorDate)
        case "day": return getDayViewRange(anchorDate)
        case "agenda": return getAgendaViewRange(anchorDate)
        default: return getMonthViewRange(anchorDate)
    }
}
