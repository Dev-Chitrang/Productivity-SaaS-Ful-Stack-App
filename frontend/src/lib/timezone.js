/**
 * timezone.js
 *
 * Single source of truth for browser timezone detection.
 * Used throughout the app wherever a timezone default is needed.
 *
 * Do NOT import Intl directly in components — always use this module
 * so the fallback logic lives in exactly one place.
 */

/**
 * Returns the browser's IANA timezone string.
 * Falls back to "UTC" if the browser API is unavailable.
 *
 * @returns {string}
 */
export function getBrowserTimezone() {
    try {
        return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"
    } catch {
        return "UTC"
    }
}

/**
 * Returns the effective timezone for the current user.
 * Prefers user.timezone when set, falls back to the browser timezone.
 *
 * @param {string|null|undefined} userTimezone - value from user profile
 * @returns {string}
 */
export function getEffectiveTimezone(userTimezone) {
    return userTimezone || getBrowserTimezone()
}

/**
 * A broad list of IANA timezone identifiers for the timezone selector.
 * Sorted roughly by UTC offset.
 */
export const COMMON_TIMEZONES = [
    "UTC",
    "Pacific/Honolulu",
    "America/Anchorage",
    "America/Los_Angeles",
    "America/Denver",
    "America/Chicago",
    "America/New_York",
    "America/Sao_Paulo",
    "Atlantic/Azores",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Europe/Helsinki",
    "Europe/Moscow",
    "Africa/Cairo",
    "Africa/Nairobi",
    "Asia/Dubai",
    "Asia/Karachi",
    "Asia/Kolkata",
    "Asia/Dhaka",
    "Asia/Bangkok",
    "Asia/Singapore",
    "Asia/Shanghai",
    "Asia/Tokyo",
    "Asia/Seoul",
    "Australia/Perth",
    "Australia/Sydney",
    "Pacific/Auckland",
]
