import { cn } from "@/lib/utils"
import { isToday, dayjs, HOURS, CELL_HEIGHT, getHourLabel, assignColumns } from "../utils/dateUtils"
import { EventCard } from "./EventCard"
import { EmptyState } from "./EmptyState"

/**
 * @param {Object} props
 * @param {string} props.anchorDate
 * @param {import("../api/calendarTypes").CalendarOccurrence[]} props.events
 * @param {(event: object) => void} props.onEventClick
 * @param {(date: string, hour: number) => void} props.onSlotClick
 */
export function DayTimeline({ anchorDate, events = [], onEventClick, onSlotClick }) {
    const day = dayjs(anchorDate)
    const today = isToday(day)

    // Backend fields: is_all_day, start_time, end_time
    const allDayEvents = events.filter((e) => e.is_all_day)
    const timedEvents = events.filter((e) => !e.is_all_day)

    // Group timed events by the hour they start in
    const eventsByHour = {}
    for (const ev of timedEvents) {
        const h = dayjs(ev.start_time).hour()
        if (!eventsByHour[h]) eventsByHour[h] = []
        eventsByHour[h].push(ev)
    }

    return (
        <div className="flex flex-col">
            {/* Day header */}
            <div className="border-b border-border px-4 py-3 flex items-center gap-3">
                <div className="flex flex-col items-center">
                    <span className="text-[10px] uppercase text-muted-foreground tracking-wider">
                        {day.format("ddd")}
                    </span>
                    <span
                        className={cn(
                            "flex size-9 items-center justify-center text-lg font-semibold",
                            today ? "bg-primary text-primary-foreground" : "text-foreground",
                        )}
                    >
                        {day.date()}
                    </span>
                </div>
                <div>
                    <p className="text-xs font-medium text-foreground">{day.format("MMMM D, YYYY")}</p>
                    <p className="text-[10px] text-muted-foreground">{day.format("dddd")}</p>
                </div>
            </div>

            {/* All-day strip */}
            {allDayEvents.length > 0 && (
                <div className="border-b border-border px-4 py-1.5 flex flex-wrap gap-1">
                    <span className="text-[10px] text-muted-foreground mr-2 self-center">All day</span>
                    {allDayEvents.map((ev) => (
                        <EventCard key={ev.id} event={ev} variant="chip" onClick={onEventClick} />
                    ))}
                </div>
            )}

            {/* Scrollable time grid */}
            <div
                className="relative flex overflow-y-auto"
                style={{ maxHeight: "calc(100vh - 280px)" }}
            >
                {/* Hour labels */}
                <div className="flex flex-col shrink-0 w-16">
                    {HOURS.map((h) => (
                        <div
                            key={h}
                            className="flex items-start justify-end pr-3 text-[10px] text-muted-foreground shrink-0"
                            style={{ height: CELL_HEIGHT }}
                        >
                            <span className="shrink-0">{getHourLabel(h)}</span>
                        </div>
                    ))}
                </div>

                {/* Event column */}
                <div className="relative flex-1 border-l border-border">
                    {HOURS.map((h) => {
                        const hourEvents = eventsByHour[h] ?? []
                        const cols = assignColumns(hourEvents)

                        return (
                            <div
                                key={h}
                                role="button"
                                aria-label={`${anchorDate} at ${h}:00`}
                                tabIndex={0}
                                style={{ height: CELL_HEIGHT }}
                                className="relative border-b border-border cursor-pointer hover:bg-muted/40 transition-colors"
                                onClick={() => onSlotClick(anchorDate, h)}
                                onKeyDown={(e) => e.key === "Enter" && onSlotClick(anchorDate, h)}
                            >
                                {cols.map(({ event: ev, column, totalColumns }) => (
                                    <div
                                        key={ev.id}
                                        className="absolute inset-y-0 z-10"
                                        style={{
                                            left: `${(column / totalColumns) * 100}%`,
                                            width: `calc(${100 / totalColumns}% - 4px)`,
                                        }}
                                    >
                                        <EventCard event={ev} variant="block" onClick={onEventClick} />
                                    </div>
                                ))}
                            </div>
                        )
                    })}
                </div>
            </div>

            {events.length === 0 && (
                <EmptyState
                    title="No events today"
                    description="Click any time slot to schedule an event."
                />
            )}
        </div>
    )
}
