import { useNavigate } from "react-router-dom"
import { Calendar, Clock, CheckSquare, Presentation } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useTasksAnalytics, useCalendarAnalytics } from "../hooks/useDashboardApi"
import { useMeetings } from "@/features/meetings/hooks/useMeetingsApi"
import { useMemo } from "react"

function AgendaItem({ icon: Icon, label, sublabel, onClick, colorClass }) {
    return (
        <button
            onClick={onClick}
            className="flex w-full items-center gap-3 rounded-sm px-2 py-1.5 text-left transition-colors hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
            <div className={`flex size-7 shrink-0 items-center justify-center rounded-full ${colorClass || "bg-primary/10"}`}>
                <Icon className="size-3.5" />
            </div>
            <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{label}</p>
                {sublabel && (
                    <p className="text-[10px] text-muted-foreground truncate">{sublabel}</p>
                )}
            </div>
        </button>
    )
}

function formatTime(dateStr) {
    if (!dateStr) return ""
    return new Date(dateStr).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}

export function TodaysAgenda() {
    const navigate = useNavigate()
    const { data: tasksData, isLoading: tasksLoading } = useTasksAnalytics()
    const { data: calendarData, isLoading: calendarLoading } = useCalendarAnalytics()
    const { data: meetings, isLoading: meetingsLoading } = useMeetings()

    const todayStr = useMemo(() => new Date().toISOString().slice(0, 10), [])
    const loading = tasksLoading || calendarLoading || meetingsLoading

    // Meetings today — MeetingResponse now includes scheduled_start
    // MeetingStatus enum values are uppercase: ENDED, CANCELLED, ACTIVE, SCHEDULED, CREATED, IDLE
    const todaysMeetings = useMemo(() => {
        if (!meetings) return []
        return meetings
            .filter(
                (m) =>
                    m.scheduled_start &&
                    m.scheduled_start.slice(0, 10) === todayStr &&
                    m.status !== "CANCELLED" &&
                    m.status !== "ENDED"
            )
            .sort((a, b) => new Date(a.scheduled_start) - new Date(b.scheduled_start))
    }, [meetings, todayStr])

    // Calendar analytics: next_events = [{id, title, start_time, end_time, color}]
    // Filter to only show events starting today
    const events = useMemo(() => {
        if (!calendarData?.next_events) return []
        return calendarData.next_events.filter(
            (e) => e.start_time && e.start_time.slice(0, 10) === todayStr
        )
    }, [calendarData, todayStr])

    // Tasks analytics: due_today = [{id, title, status, priority, due_date}]
    const dueToday = useMemo(() => tasksData?.due_today || [], [tasksData])

    // Merge into a single chronological list
    const agendaItems = useMemo(() => {
        const items = []

        todaysMeetings.forEach((m) => {
            items.push({
                id: `meeting-${m.id}`,
                icon: Presentation,
                label: m.title,
                sublabel: `${formatTime(m.scheduled_start)} · Meeting`,
                colorClass: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
                time: new Date(m.scheduled_start),
                onClick: () => navigate(`/meetings/${m.id}`),
            })
        })

        events.forEach((ev) => {
            items.push({
                id: `event-${ev.id}`,
                icon: Calendar,
                label: ev.title,
                sublabel: `${formatTime(ev.start_time)} · Event`,
                colorClass: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
                time: new Date(ev.start_time),
                onClick: () => navigate("/calendar"),
            })
        })

        dueToday.forEach((t) => {
            items.push({
                id: `task-${t.id}`,
                icon: CheckSquare,
                label: t.title,
                sublabel: `Due today${t.priority ? ` · ${t.priority}` : ""}`,
                colorClass: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
                time: t.due_date ? new Date(t.due_date) : new Date(8640000000000000), // sort to end if no time
                onClick: () => navigate(`/tasks?task=${t.id}`),
            })
        })

        return items.sort((a, b) => a.time - b.time)
    }, [todaysMeetings, events, dueToday, navigate])

    return (
        <Card size="sm">
            <CardHeader>
                <CardTitle className="flex items-center gap-1.5 text-xs">
                    <Clock className="size-3.5 text-muted-foreground" />
                    Today's Agenda
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
                {loading ? (
                    <div className="space-y-2 py-1">
                        <Skeleton className="h-8 w-full" />
                        <Skeleton className="h-8 w-3/4" />
                        <Skeleton className="h-8 w-5/6" />
                    </div>
                ) : agendaItems.length > 0 ? (
                    agendaItems.map((item) => (
                        <AgendaItem
                            key={item.id}
                            icon={item.icon}
                            label={item.label}
                            sublabel={item.sublabel}
                            colorClass={item.colorClass}
                            onClick={item.onClick}
                        />
                    ))
                ) : (
                    <p className="text-xs text-muted-foreground py-3 text-center">
                        Nothing scheduled for today
                    </p>
                )}
            </CardContent>
        </Card>
    )
}
