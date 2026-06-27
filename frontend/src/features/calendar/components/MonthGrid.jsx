import { cn } from "@/lib/utils"
import { getMonthGrid, isToday, isSameMonth, dayjs } from "../utils/dateUtils"
import { EventCard } from "./EventCard"
import { EmptyState } from "./EmptyState"

const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
const MAX_VISIBLE_EVENTS = 3

/**
 * Groups events into all days they span (multi-day support).
 */
function groupEventsByDay(events) {
    return events.reduce((acc, ev) => {
        const evStart = dayjs(ev.start_time).startOf("day")
        const evEnd = dayjs(ev.end_time).startOf("day")
        let cursor = evStart
        while (cursor.isSameOrBefore(evEnd)) {
            const key = cursor.format("YYYY-MM-DD")
            if (!acc[key]) acc[key] = []
            acc[key].push(ev)
            cursor = cursor.add(1, "day")
        }
        return acc
    }, {})
}

/**
 * @param {Object} props
 * @param {string} props.anchorDate
 * @param {import("../api/calendarTypes").CalendarOccurrence[]} props.events
 * @param {(event) => void} props.onEventClick
 * @param {(date: string) => void} props.onDayClick
 * @param {() => void} props.onCreateEvent
 */
export function MonthGrid({ anchorDate, events = [], onEventClick, onDayClick, onCreateEvent }) {
    const cells = getMonthGrid(anchorDate)
    const eventsByDay = groupEventsByDay(events)

    return (
        <div className="flex flex-col overflow-x-auto">
            {/* Day-name header */}
            <div className="grid grid-cols-7 border-b border-border sticky top-0 bg-background z-10 min-w-[560px]">
                {DAY_NAMES.map((name) => (
                    <div key={name} className="py-2 px-3 text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                        {name}
                    </div>
                ))}
            </div>

            {/* 6 week rows */}
            <div className="min-w-[560px]">
                {Array.from({ length: 6 }).map((_, wi) => (
                    <div key={wi} className="grid grid-cols-7 border-b border-border last:border-b-0">
                        {cells.slice(wi * 7, wi * 7 + 7).map((day) => {
                            const isoDate = day.format("YYYY-MM-DD")
                            const dayEvents = eventsByDay[isoDate] ?? []
                            const overflow = dayEvents.length - MAX_VISIBLE_EVENTS
                            const inMonth = isSameMonth(day, anchorDate)
                            const today = isToday(day)

                            return (
                                <div
                                    key={isoDate}
                                    role="button"
                                    tabIndex={0}
                                    aria-label={`${isoDate}${dayEvents.length ? `, ${dayEvents.length} events` : ""}`}
                                    onClick={() => onDayClick(isoDate)}
                                    onKeyDown={(e) => e.key === "Enter" && onDayClick(isoDate)}
                                    className={cn(
                                        "min-h-[96px] border-r border-border last:border-r-0 p-1.5 select-none overflow-hidden",
                                        "cursor-pointer hover:bg-muted/50 transition-colors",
                                        !inMonth && "bg-muted/20",
                                    )}
                                >
                                    {/* Day number */}
                                    <span
                                        className={cn(
                                            "inline-flex size-6 items-center justify-center text-xs mb-1",
                                            today && "bg-primary text-primary-foreground font-semibold",
                                            !today && !inMonth && "text-muted-foreground",
                                            !today && inMonth && "text-foreground",
                                        )}
                                    >
                                        {day.date()}
                                    </span>

                                    {/* Events */}
                                    <div className="space-y-0.5">
                                        {dayEvents.slice(0, MAX_VISIBLE_EVENTS).map((ev) => (
                                            <EventCard
                                                key={ev.id}
                                                event={ev}
                                                variant="chip"
                                                onClick={onEventClick}
                                            />
                                        ))}
                                        {overflow > 0 && (
                                            <button
                                                type="button"
                                                onClick={(e) => { e.stopPropagation(); onDayClick(isoDate) }}
                                                className="w-full text-left text-[10px] text-muted-foreground hover:text-foreground pl-1.5"
                                            >
                                                +{overflow} more
                                            </button>
                                        )}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                ))}
            </div>

            {events.length === 0 && (
                <EmptyState
                    title="No events this month"
                    description="Click a day to create an event, or use the Create button."
                    onCreateEvent={onCreateEvent}
                />
            )}
        </div>
    )
}
