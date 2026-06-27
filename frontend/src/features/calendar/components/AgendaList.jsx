import { cn } from "@/lib/utils"
import { dayjs, fmtTimeRange } from "../utils/dateUtils"
import { getEventFaintStyle, getEventDotStyle } from "../utils/colorUtils"
import { RefreshCw, MapPin } from "lucide-react"
import { EmptyState } from "./EmptyState"

/**
 * Groups events into day sections and renders a chronological list.
 *
 * Backend field names used here:
 *   start_time, end_time, is_all_day, event_type, color (uppercase enum)
 *
 * @param {Object} props
 * @param {import("../api/calendarTypes").CalendarOccurrence[]} props.events
 * @param {(event: object) => void} props.onEventClick
 * @param {() => void} [props.onCreateEvent]
 */
export function AgendaList({ events = [], onEventClick, onCreateEvent }) {
    if (events.length === 0) {
        return (
            <EmptyState
                title="No upcoming events"
                description="Your agenda is clear for the selected period."
                onCreateEvent={onCreateEvent}
            />
        )
    }

    // Group events by calendar date (using start_time)
    const groups = events.reduce((acc, ev) => {
        const date = dayjs(ev.start_time).format("YYYY-MM-DD")
        if (!acc[date]) acc[date] = []
        acc[date].push(ev)
        return acc
    }, {})

    const sortedDates = Object.keys(groups).sort()

    return (
        <div className="space-y-6 py-2">
            {sortedDates.map((date) => {
                const d = dayjs(date)
                const isToday = d.isSame(dayjs(), "day")
                const isPast = d.isBefore(dayjs(), "day")

                return (
                    <div key={date}>
                        {/* Day header */}
                        <div className="flex items-center gap-3 mb-2 px-1">
                            <div
                                className={cn(
                                    "flex flex-col items-center w-12 shrink-0",
                                    isPast && "opacity-50",
                                )}
                            >
                                <span className="text-[10px] uppercase text-muted-foreground tracking-wider">
                                    {d.format("ddd")}
                                </span>
                                <span
                                    className={cn(
                                        "flex size-7 items-center justify-center text-sm font-semibold",
                                        isToday ? "bg-primary text-primary-foreground" : "text-foreground",
                                    )}
                                >
                                    {d.date()}
                                </span>
                            </div>
                            <div className="flex-1 h-px bg-border" />
                            <span className="text-[10px] text-muted-foreground shrink-0">
                                {d.format("MMMM YYYY")}
                            </span>
                        </div>

                        {/* Events for this day */}
                        <div className="space-y-1.5">
                            {groups[date].map((ev) => {
                                const faint = getEventFaintStyle(ev.color)
                                const dot = getEventDotStyle(ev.color)

                                return (
                                    <button
                                        key={ev.id}
                                        type="button"
                                        onClick={() => onEventClick(ev)}
                                        aria-label={`Event: ${ev.title}`}
                                        className={cn(
                                            "w-full text-left flex gap-3 px-3 py-2.5 border transition-opacity",
                                            "hover:opacity-80 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                                            faint,
                                            isPast && "opacity-60",
                                        )}
                                    >
                                        {/* Color dot */}
                                        <div className="flex flex-col items-center pt-0.5 shrink-0">
                                            <div className={cn("size-2 rounded-full mt-0.5", dot)} />
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            {/* Title */}
                                            <div className="flex items-center gap-1.5 flex-wrap">
                                                <span className="text-xs font-semibold truncate">{ev.title}</span>
                                                {ev.is_recurring && (
                                                    <RefreshCw className="size-3 shrink-0 opacity-60" />
                                                )}
                                            </div>

                                            {/* Time */}
                                            <p className="text-[10px] opacity-70 mt-0.5">
                                                {ev.is_all_day
                                                    ? "All day"
                                                    : fmtTimeRange(ev.start_time, ev.end_time)}
                                            </p>

                                            {/* Location */}
                                            {ev.location && (
                                                <p className="text-[10px] opacity-60 flex items-center gap-1 mt-0.5">
                                                    <MapPin className="size-2.5 shrink-0" />
                                                    <span className="truncate">{ev.location}</span>
                                                </p>
                                            )}
                                        </div>

                                        {/* Event type badge */}
                                        <span className="text-[9px] uppercase tracking-wider opacity-60 self-start shrink-0 mt-0.5">
                                            {ev.event_type}
                                        </span>
                                    </button>
                                )
                            })}
                        </div>
                    </div>
                )
            })}
        </div>
    )
}
