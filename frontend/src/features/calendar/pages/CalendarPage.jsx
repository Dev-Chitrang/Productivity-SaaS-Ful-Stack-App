import { useState, useCallback, useMemo } from "react"
import { useSearchParams, useNavigate } from "react-router-dom"
import { CalendarToolbar } from "../components/CalendarToolbar"
import { MonthGrid } from "../components/MonthGrid"
import { WeekGrid } from "../components/WeekGrid"
import { DayTimeline } from "../components/DayTimeline"
import { AgendaList } from "../components/AgendaList"
import { EventDialog } from "../components/EventDialog"
import { EventDetailDialog } from "../components/EventDetailDialog"
import { DeleteConfirmationDialog } from "../components/DeleteConfirmationDialog"
import { FilterPanel } from "../components/FilterPanel"
import { MonthViewSkeleton, WeekViewSkeleton, AgendaSkeleton } from "../components/LoadingSkeleton"
import { useCalendarEvents, useDeleteEvent } from "../hooks/useCalendarApi"
import { useTasks } from "@/features/tasks/hooks/useTasksApi"
import { dayjs, toISODate, getViewDateRange } from "../utils/dateUtils"

/** @typedef {"month"|"week"|"day"|"agenda"} CalendarView */

/** Navigates the anchor date forward or backward one period */
function navigateAnchor(view, anchorDate, direction) {
    const d = dayjs(anchorDate)
    const delta = direction === "next" ? 1 : -1
    switch (view) {
        case "month": return toISODate(d.add(delta, "month"))
        case "week": return toISODate(d.add(delta * 7, "day"))
        case "day": return toISODate(d.add(delta, "day"))
        case "agenda": return toISODate(d.add(delta, "month"))
        default: return anchorDate
    }
}

export default function CalendarPage() {
    const [searchParams, setSearchParams] = useSearchParams()
    const navigate = useNavigate()

    // Persist view + anchor date in the URL so browser back/forward works
    const view = /** @type {CalendarView} */ (searchParams.get("view") || "month")
    const anchorDate = searchParams.get("date") || toISODate(dayjs())

    const setView = (v) => setSearchParams((p) => { p.set("view", v); return p })
    const setAnchorDate = (d) => setSearchParams((p) => { p.set("date", d); return p })

    // Filters & search
    const [filters, setFilters] = useState({})
    const [filterOpen, setFilterOpen] = useState(false)
    const [search, setSearch] = useState("")

    const hasActiveFilters = useMemo(
        () => Object.values(filters).some(Boolean),
        [filters],
    )

    // Dialog state
    const [createDialogOpen, setCreateDialogOpen] = useState(false)
    const [createAnchorDate, setCreateAnchorDate] = useState(null)
    const [createAnchorHour, setCreateAnchorHour] = useState(null)
    const [detailEvent, setDetailEvent] = useState(null)
    const [editEvent, setEditEvent] = useState(null)
    const [deleteTarget, setDeleteTarget] = useState(null)

    // -----------------------------------------------------------------------
    // Data fetching — single hook for all views
    // -----------------------------------------------------------------------

    // Compute the ISO datetime range the current view requires
    const { start, end } = useMemo(
        () => getViewDateRange(view, anchorDate),
        [view, anchorDate],
    )

    // All filters forwarded to the one endpoint
    const queryFilters = useMemo(
        () => ({
            search: search || undefined,
            event_type: filters.event_type || undefined,
            color: filters.color || undefined,
        }),
        [search, filters],
    )

    const { data: events = [], isLoading, isError } = useCalendarEvents(start, end, queryFilters)

    const { data: tasksData } = useTasks({ archived: false })
    const tasks = useMemo(() => tasksData?.tasks ?? [], [tasksData])

    const mergedEvents = useMemo(() => {
      const taskEvents = tasks
        .filter((t) => t.due_date && !t.deleted_at)
        .map((t) => {
          const dueDay = dayjs(t.due_date)
          const inRange = dueDay.isAfter(dayjs(start).subtract(1, "day")) && dueDay.isBefore(dayjs(end).add(1, "day"))
          if (!inRange) return null
          return {
            __type: "task",
            id: `task_${t.id}`,
            title: t.title,
            description: null,
            event_type: "TASK",
            color: t.priority === "HIGH" ? "RED" : t.priority === "LOW" ? "GREEN" : "PURPLE",
            start_time: dueDay.startOf("day").format(),
            end_time: dueDay.endOf("day").format(),
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            is_all_day: true,
            location: null,
            is_recurring: false,
            recurrence_frequency: null,
            recurrence_interval: null,
            recurrence_end_date: null,
            task_id: t.id,
          }
        })
        .filter(Boolean)

      const meetingEvents = events.map((e) => ({ ...e, __type: "event" }))

      return [...meetingEvents, ...taskEvents]
    }, [events, tasks, start, end])

    const deleteMutation = useDeleteEvent(() => setDeleteTarget(null))

    // -----------------------------------------------------------------------
    // Navigation
    // -----------------------------------------------------------------------
    const handlePrev = useCallback(() => setAnchorDate(navigateAnchor(view, anchorDate, "prev")), [view, anchorDate])
    const handleNext = useCallback(() => setAnchorDate(navigateAnchor(view, anchorDate, "next")), [view, anchorDate])
    const handleToday = useCallback(() => setAnchorDate(toISODate(dayjs())), [])

    // -----------------------------------------------------------------------
    // Event interactions
    // -----------------------------------------------------------------------
    const handleEventClick = useCallback((event) => {
      if (event.__type === "task") {
        navigate(`/tasks`)
        return
      }
      setDetailEvent(event)
    }, [navigate])

    const handleDayClick = useCallback((isoDate) => {
        if (view === "month") {
            // Drill into day view on month-cell click
            setAnchorDate(isoDate)
            setView("day")
        } else {
            setCreateAnchorDate(isoDate)
            setCreateAnchorHour(null)
            setCreateDialogOpen(true)
        }
    }, [view])

    const handleSlotClick = useCallback((isoDate, hour) => {
        setCreateAnchorDate(isoDate)
        setCreateAnchorHour(hour)
        setCreateDialogOpen(true)
    }, [])

    const handleCreateEvent = useCallback(() => {
        setCreateAnchorDate(anchorDate)
        setCreateAnchorHour(null)
        setCreateDialogOpen(true)
    }, [anchorDate])

    // -----------------------------------------------------------------------
    // Detail → edit / delete flow
    // -----------------------------------------------------------------------
    const handleEditFromDetail = useCallback(() => {
        setEditEvent(detailEvent)
        setDetailEvent(null)
    }, [detailEvent])

    const handleDeleteFromDetail = useCallback(() => {
        setDeleteTarget(detailEvent)
        setDetailEvent(null)
    }, [detailEvent])

    const handleConfirmDelete = useCallback(() => {
        if (deleteTarget) deleteMutation.mutate(deleteTarget.id)
    }, [deleteTarget, deleteMutation])

    // -----------------------------------------------------------------------
    // Render
    // -----------------------------------------------------------------------
    const renderView = () => {
        if (isLoading) {
            if (view === "month") return <MonthViewSkeleton />
            if (view === "week") return <WeekViewSkeleton />
            return <AgendaSkeleton />
        }

        if (isError) {
            return (
                <div className="flex items-center justify-center py-16 text-xs text-muted-foreground">
                    Failed to load events. Try refreshing.
                </div>
            )
        }

        switch (view) {
            case "month":
                return (
                    <MonthGrid
                        anchorDate={anchorDate}
                        events={mergedEvents}
                        onEventClick={handleEventClick}
                        onDayClick={handleDayClick}
                        onCreateEvent={handleCreateEvent}
                    />
                )
            case "week":
                return (
                    <WeekGrid
                        anchorDate={anchorDate}
                        events={mergedEvents}
                        onEventClick={handleEventClick}
                        onSlotClick={handleSlotClick}
                    />
                )
            case "day":
                return (
                    <DayTimeline
                        anchorDate={anchorDate}
                        events={mergedEvents}
                        onEventClick={handleEventClick}
                        onSlotClick={handleSlotClick}
                    />
                )
            case "agenda":
                return (
                    <AgendaList
                        events={mergedEvents}
                        onEventClick={handleEventClick}
                        onCreateEvent={handleCreateEvent}
                    />
                )
            default:
                return null
        }
    }

    return (
        <div className="flex flex-col">
            {/* Toolbar */}
            <CalendarToolbar
                view={view}
                onViewChange={setView}
                anchorDate={anchorDate}
                onPrev={handlePrev}
                onNext={handleNext}
                onToday={handleToday}
                search={search}
                onSearchChange={setSearch}
                filterOpen={filterOpen}
                onToggleFilter={() => setFilterOpen((p) => !p)}
                hasActiveFilters={hasActiveFilters}
                onCreateEvent={handleCreateEvent}
            />

            {/* Main content */}
            <div className="flex flex-1 overflow-hidden">
                <main
                    className="flex-1 overflow-auto"
                    aria-label="Calendar view"
                    role="region"
                    aria-live="polite"
                    aria-busy={isLoading}
                >
                    {renderView()}
                </main>

                {filterOpen && (
                    <aside className="shrink-0 border-l border-border">
                        <FilterPanel
                            filters={filters}
                            onChange={setFilters}
                            onClose={() => setFilterOpen(false)}
                        />
                    </aside>
                )}
            </div>

            {/* ---- Dialogs ---- */}

            <EventDialog
                open={createDialogOpen}
                mode="create"
                anchorDate={createAnchorDate ?? anchorDate}
                anchorHour={createAnchorHour}
                onClose={() => setCreateDialogOpen(false)}
            />

            <EventDialog
                open={!!editEvent}
                mode="edit"
                event={editEvent}
                onClose={() => setEditEvent(null)}
            />

            <EventDetailDialog
                open={!!detailEvent}
                event={detailEvent}
                onClose={() => setDetailEvent(null)}
                onEdit={handleEditFromDetail}
                onDelete={handleDeleteFromDetail}
            />

            <DeleteConfirmationDialog
                open={!!deleteTarget}
                eventTitle={deleteTarget?.title}
                onClose={() => setDeleteTarget(null)}
                onConfirm={handleConfirmDelete}
                isPending={deleteMutation.isPending}
            />
        </div>
    )
}
