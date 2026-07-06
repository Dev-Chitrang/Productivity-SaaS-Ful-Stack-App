import { useNavigate } from "react-router-dom"
import { Presentation, Clock } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useMeetings } from "@/features/meetings/hooks/useMeetingsApi"
import { useMemo } from "react"

// MeetingStatus enum values (uppercase): CREATED, SCHEDULED, ACTIVE, IDLE, ENDED, CANCELLED
// MeetingType enum values: INSTANT, SCHEDULED
const STATUS_LABELS = {
    CREATED: "Created",
    SCHEDULED: "Scheduled",
    ACTIVE: "Live",
    IDLE: "Idle",
    ENDED: "Ended",
    CANCELLED: "Cancelled",
}

const STATUS_CLASS = {
    ACTIVE: "text-emerald-600 dark:text-emerald-400",
    SCHEDULED: "text-blue-600 dark:text-blue-400",
    CREATED: "text-amber-600 dark:text-amber-400",
    IDLE: "text-muted-foreground",
}

const TYPE_LABELS = {
    INSTANT: "Instant",
    SCHEDULED: "Scheduled",
}

function formatRelativeDate(dateStr) {
    if (!dateStr) return ""
    const d = new Date(dateStr)
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(today.getDate() + 1)

    if (d.toDateString() === today.toDateString()) return "Today"
    if (d.toDateString() === tomorrow.toDateString()) return "Tomorrow"
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}

function formatTime(dateStr) {
    if (!dateStr) return ""
    return new Date(dateStr).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}

export function UpcomingMeetings() {
    const navigate = useNavigate()
    const { data: meetings, isLoading } = useMeetings()

    const upcoming = useMemo(() => {
        if (!meetings) return []
        const now = new Date()
        return meetings
            .filter(
                (m) =>
                    m.scheduled_start &&
                    new Date(m.scheduled_start) > now &&
                    m.status !== "CANCELLED" &&
                    m.status !== "ENDED"
            )
            .sort((a, b) => new Date(a.scheduled_start) - new Date(b.scheduled_start))
            .slice(0, 5)
    }, [meetings])

    return (
        <Card size="sm">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-1.5 text-xs">
                        <Presentation className="size-3.5 text-muted-foreground" />
                        Upcoming Meetings
                    </CardTitle>
                    <button
                        onClick={() => navigate("/meetings")}
                        className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                    >
                        View all
                    </button>
                </div>
            </CardHeader>
            <CardContent className="space-y-1">
                {isLoading ? (
                    <div className="space-y-2 py-1">
                        <Skeleton className="h-10 w-full" />
                        <Skeleton className="h-10 w-full" />
                        <Skeleton className="h-10 w-3/4" />
                    </div>
                ) : upcoming.length > 0 ? (
                    upcoming.map((m) => (
                        <button
                            key={m.id}
                            onClick={() => navigate(`/meetings/${m.id}`)}
                            className="flex w-full items-center gap-3 rounded-sm px-2 py-1.5 text-left transition-colors hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        >
                            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-violet-500/10">
                                <Presentation className="size-3.5 text-violet-600 dark:text-violet-400" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium truncate">{m.title}</p>
                                <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground mt-0.5">
                                    <Clock className="size-3 shrink-0" />
                                    <span>{formatRelativeDate(m.scheduled_start)}</span>
                                    <span>·</span>
                                    <span>{formatTime(m.scheduled_start)}</span>
                                    {m.meeting_type && (
                                        <>
                                            <span>·</span>
                                            <span>{TYPE_LABELS[m.meeting_type] || m.meeting_type}</span>
                                        </>
                                    )}
                                </div>
                            </div>
                            <span className={`text-[10px] shrink-0 font-medium ${STATUS_CLASS[m.status] || "text-muted-foreground"}`}>
                                {STATUS_LABELS[m.status] || m.status}
                            </span>
                        </button>
                    ))
                ) : (
                    <p className="text-xs text-muted-foreground py-3 text-center">
                        No upcoming meetings
                    </p>
                )}
            </CardContent>
        </Card>
    )
}
