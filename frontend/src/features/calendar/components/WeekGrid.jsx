import { cn } from "@/lib/utils"
import { getWeekDays, isToday, dayjs, HOURS, CELL_HEIGHT, getHourLabel, assignColumns } from "../utils/dateUtils"
import { EventCard } from "./EventCard"
import { EmptyState } from "./EmptyState"

/**
 * @param {Object} props
 * @param {string} props.anchorDate
 * @param {import("../api/calendarTypes").CalendarOccurrence[]} props.events
 * @param {(event: object) => void} props.onEventClick
 * @param {(date: string, hour: number) => void} props.onSlotClick
 */
export function WeekGrid({ anchorDate, events = [], onEventClick, onSlotClick }) {
    const days = getWeekDays(anchorDate)

    // Bucket timed events by day (using event start_time — no splitting)
    const timedByDay = days.reduce((acc, day) => {
        const isoDate = day.format("YYYY-MM-DD")
        acc[isoDate] = events.filter(
            (e) => !e.is_all_day && dayjs(e.start_time).format("YYYY-MM-DD") === isoDate,
        )
        return acc
    }, {})

    // All-day events across the week
    const allDayEvents = events.filter((e) => e.is_all_day)
    const allDayByDay = days.reduce((acc, day) => {
        const isoDate = day.format("YYYY-MM-DD")
        acc[isoDate] = allDayEvents.filter(
            (e) => dayjs(e.start_time).format("YYYY-MM-DD") === isoDate,
        )
        return acc
    }, {})

    const hasAnyAllDay = allDayEvents.length > 0
    const hasAnyTimed = events.some((e) => !e.is_all_day)

    return (
        <div className="flex flex-col overflow-x-auto">
            <div className="min-w-[560px]">
                {/* Header row */}
                <div className="grid grid-cols-8 border-b border-border sticky top-0 bg-background z-10">
                    <div className="py-2" />
                    {days.map((day) => {
                        const today = isToday(day)
                        return (
                            <div
                                key={day.format("YYYY-MM-DD")}
                                className="py-2 px-2 flex flex-col items-center border-l border-border"
                            >
                                <span className="text-[10px] uppercase text-muted-foreground tracking-wider">
                                    {day.format("ddd")}
                                </span>
                                <span
                                    className={cn(
                                        "mt-0.5 flex size-7 items-center justify-center text-xs font-semibold",
                                        today ? "bg-primary text-primary-foreground" : "text-foreground",
                                    )}
                                >
                                    {day.date()}
                                </span>
                            </div>
                        )
                    })}
                </div>

                {/* All-day row */}
                {hasAnyAllDay && (
                    <div className="grid grid-cols-8 border-b border-border min-h-[28px]">
                        <div className="px-2 py-1 text-[10px] text-muted-foreground text-right pr-2 self-center">
                            All day
                        </div>
                        {days.map((day) => {
                            const isoDate = day.format("YYYY-MM-DD")
                            return (
                                <div key={isoDate} className="border-l border-border p-0.5 space-y-0.5">
                                    {(allDayByDay[isoDate] ?? []).map((ev) => (
                                        <EventCard key={ev.id} event={ev} variant="chip" onClick={onEventClick} />
                                    ))}
                                </div>
                            )
                        })}
                    </div>
                )}

                {/* Time grid */}
                <div className="relative grid grid-cols-8">
                    {/* Hour labels */}
                    <div className="flex flex-col">
                        {HOURS.map((h) => (
                            <div
                                key={h}
                                className="flex items-start justify-end pr-2 text-[10px] text-muted-foreground"
                                style={{ height: CELL_HEIGHT }}
                            >
                                <span className="shrink-0">{getHourLabel(h)}</span>
                            </div>
                        ))}
                    </div>

                    {/* Day columns */}
                    {days.map((day) => {
                        const isoDate = day.format("YYYY-MM-DD")
                        const dayEvents = timedByDay[isoDate] ?? []

                        // Group timed events by the hour they start in
                        const eventsByHour = {}
                        for (const ev of dayEvents) {
                            const h = dayjs(ev.start_time).hour()
                            if (!eventsByHour[h]) eventsByHour[h] = []
                            eventsByHour[h].push(ev)
                        }

                        return (
                            <div key={isoDate} className="relative border-l border-border">
                                {HOURS.map((h) => {
                                    const hourEvents = eventsByHour[h] ?? []
                                    const cols = assignColumns(hourEvents)

                                    return (
                                        <div
                                            key={h}
                                            role="button"
                                            aria-label={`${isoDate} at ${h}:00`}
                                            tabIndex={0}
                                            style={{ height: CELL_HEIGHT }}
                                            className="relative border-b border-border cursor-pointer hover:bg-muted/40 transition-colors"
                                            onClick={() => onSlotClick(isoDate, h)}
                                            onKeyDown={(e) => e.key === "Enter" && onSlotClick(isoDate, h)}
                                        >
                                            {cols.map(({ event: ev, column, totalColumns }) => (
                                                <div
                                                    key={ev.id}
                                                    className="absolute inset-y-0 z-10"
                                                    style={{
                                                        left: `${(column / totalColumns) * 100}%`,
                                                        width: `calc(${100 / totalColumns}% - 2px)`,
                                                    }}
                                                >
                                                    <EventCard event={ev} variant="block" onClick={onEventClick} />
                                                </div>
                                            ))}
                                        </div>
                                    )
                                })}
                            </div>
                        )
                    })}
                </div>

                {!hasAnyTimed && !hasAnyAllDay && (
                    <EmptyState
                        title="No events this week"
                        description="Click any time slot to create an event."
                    />
                )}
            </div>
        </div>
    )
}
