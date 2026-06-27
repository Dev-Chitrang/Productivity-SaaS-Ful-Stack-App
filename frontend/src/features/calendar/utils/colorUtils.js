/**
 * colorUtils.js
 *
 * Re-exports color utilities backed by the canonical definitions in
 * calendarTypes.js. Components import from here for Tailwind class lookups.
 */

import {
    EVENT_COLOR_CLASSES,
    EVENT_COLOR_HEX,
    EventColor,
} from "../api/calendarTypes"

/**
 * Normalises a raw color value (backend uppercase enum or legacy lowercase)
 * to a key present in EVENT_COLOR_CLASSES.  Falls back to BLUE.
 * @param {string} raw
 * @returns {string}
 */
function toColorKey(raw) {
    if (!raw) return EventColor.BLUE
    const upper = raw.toUpperCase()
    return Object.values(EventColor).includes(upper) ? upper : EventColor.BLUE
}

/** Returns the faint Tailwind classes for an event color */
export const getEventFaintStyle = (color) =>
    (EVENT_COLOR_CLASSES[toColorKey(color)] ?? EVENT_COLOR_CLASSES[EventColor.BLUE]).faint

/** Returns the solid bg Tailwind class for an event color */
export const getEventBgStyle = (color) =>
    (EVENT_COLOR_CLASSES[toColorKey(color)] ?? EVENT_COLOR_CLASSES[EventColor.BLUE]).bg

/** Returns the dot Tailwind class for an event color */
export const getEventDotStyle = (color) =>
    (EVENT_COLOR_CLASSES[toColorKey(color)] ?? EVENT_COLOR_CLASSES[EventColor.BLUE]).dot

/**
 * Returns the hex swatch for an event color.
 * Accepts both uppercase backend values ("BLUE") and lowercase legacy values ("blue").
 */
export const getEventColorHex = (color) =>
    EVENT_COLOR_HEX[toColorKey(color)] ?? EVENT_COLOR_HEX[EventColor.BLUE]

// Keep COLOR_SWATCHES export for any component that uses it directly
export const COLOR_SWATCHES = EVENT_COLOR_HEX
