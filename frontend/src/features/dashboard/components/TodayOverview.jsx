import { Calendar, CheckSquare, Clock, FileText, AlertCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

function EventItem({ event }) {
    const start = new Date(event.start_time)
    const time = start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    return (
        <div className="flex items-center gap-2 py-1">
            <div className={cn("size-2 rounded-full shrink-0", event.color ? `bg-${event.color.toLowerCase()}-500` : "bg-primary")} />
            <span className="text-xs text-foreground truncate flex-1">{event.title}</span>
            <span className="text-xs text-muted-foreground shrink-0">{time}</span>
        </div>
    )
}

function TaskItem({ task, isOverdue }) {
    return (
        <div className="flex items-center gap-2 py-1">
            {isOverdue ? (
                <AlertCircle className="size-3 text-destructive shrink-0" />
            ) : (
                <CheckSquare className="size-3 text-muted-foreground shrink-0" />
            )}
            <span className={cn("text-xs truncate flex-1", isOverdue && "text-destructive")}>{task.title}</span>
            {task.due_date && (
                <span className={cn("text-xs shrink-0", isOverdue ? "text-destructive" : "text-muted-foreground")}>
                    {new Date(task.due_date).toLocaleDateString([], { month: "short", day: "numeric" })}
                </span>
            )}
        </div>
    )
}

function NoteItem({ note }) {
    return (
        <div className="flex items-center gap-2 py-1">
            <FileText className="size-3 text-muted-foreground shrink-0" />
            <span className="text-xs text-foreground truncate flex-1">{note.title || "Untitled"}</span>
            <span className="text-xs text-muted-foreground shrink-0">
                {new Date(note.updated_at).toLocaleDateString([], { month: "short", day: "numeric" })}
            </span>
        </div>
    )
}

function SectionCard({ icon: Icon, title, children, loading }) {
    return (
        <Card size="sm" className="flex-1 min-w-0">
            <CardHeader>
                <CardTitle className="flex items-center gap-1.5 text-xs">
                    <Icon className="size-3.5 text-muted-foreground" />
                    {title}
                </CardTitle>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="text-xs text-muted-foreground">Loading...</div>
                ) : children ? (
                    children
                ) : (
                    <div className="text-xs text-muted-foreground">None</div>
                )}
            </CardContent>
        </Card>
    )
}

export function TodayOverview({ calendarData, tasksData, notesData, loading }) {
    const nextEvents = calendarData?.next_events || []
    const dueToday = tasksData?.due_today || []
    const overdueTasks = tasksData?.overdue_tasks || []
    const recentNotes = notesData?.recent_notes || []

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <SectionCard icon={Calendar} title="Next Events" loading={loading}>
                {nextEvents.length > 0 ? nextEvents.map((ev, i) => <EventItem key={ev.id || i} event={ev} />) : null}
            </SectionCard>
            <SectionCard icon={CheckSquare} title="Due Today" loading={loading}>
                {dueToday.length > 0 ? dueToday.map((t, i) => <TaskItem key={t.id || i} task={t} />) : null}
            </SectionCard>
            <SectionCard icon={AlertCircle} title="Overdue Tasks" loading={loading}>
                {overdueTasks.length > 0 ? overdueTasks.map((t, i) => <TaskItem key={t.id || i} task={t} isOverdue />) : null}
            </SectionCard>
            <SectionCard icon={Clock} title="Recent Notes" loading={loading}>
                {recentNotes.length > 0 ? recentNotes.map((n, i) => <NoteItem key={n.id || i} note={n} />) : null}
            </SectionCard>
        </div>
    )
}
