import { cn } from "@/lib/utils"
import { fmtDisplayTime, fmtDisplayTimeRange } from "../api/calendarMapper"
import { getEventFaintStyle } from "../utils/colorUtils"
import { RefreshCw } from "lucide-react"

/**
 * Compact event chip / block used inside calendar grids.
 * All times displayed in 12-hour format (h:mm A) via calendarMapper.
 *
 * @param {Object} props
 * @param {import("../api/calendarTypes").CalendarOccurrence} props.event
 * @param {"chip"|"block"} [props.variant]
 * @param {(event: object) => void} [props.onClick]
 */
export function EventCard({ event, variant = "chip", onClick }) {
    const style = getEventFaintStyle(event.color)

    if (variant === "chip") {
        return (
            <button
                type="button"
                aria-label={`Event: ${event.title}`}
                onClick={(e) => { e.stopPropagation(); onClick?.(event) }}
                className={cn(
                    "w-full truncate px-1.5 py-0.5 text-left text-[10px] leading-4 font-medium border",
                    "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                    "hover:opacity-80 transition-opacity",
                    style,
                )}
            >
                {!event.is_all_day && (
                    <span className="mr-1 opacity-70">{fmtDisplayTime(event.start_time)}</span>
                )}
                {event.is_recurring && <RefreshCw className="inline size-2.5 mr-0.5 opacity-60" />}
                {event.title}
            </button>
        )
    }

    return (
        <button
            type="button"
            aria-label={`Event: ${event.title}`}
            onClick={(e) => { e.stopPropagation(); onClick?.(event) }}
            className={cn(
                "w-full h-full px-2 py-1 text-left border-l-2 overflow-hidden",
                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                "hover:opacity-80 transition-opacity",
                style,
            )}
        >
            <p className="text-[11px] font-semibold leading-tight truncate">
                {event.is_recurring && <RefreshCw className="inline size-2.5 mr-0.5 opacity-70" />}
                {event.title}
            </p>
            {!event.is_all_day && (
                <p className="text-[10px] opacity-70 leading-tight mt-0.5 truncate">
                    {fmtDisplayTimeRange(event.start_time, event.end_time)}
                </p>
            )}
            {event.location && (
                <p className="text-[10px] opacity-60 leading-tight mt-0.5 truncate">{event.location}</p>
            )}
        </button>
    )
}
