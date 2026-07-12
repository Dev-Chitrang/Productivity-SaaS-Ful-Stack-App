import { useNavigate } from "react-router-dom"
import {
    CheckSquare,
    ListTodo,
    Calendar,
    Presentation,
    FileText,
    PenSquare,
    AlertCircle,
    Paperclip,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useTasksAnalytics, useNotesAnalytics, useCalendarAnalytics, useRecentAttachments } from "../hooks/useDashboardApi"
import { useMeetings } from "@/features/meetings/hooks/useMeetingsApi"
import { useWhiteboards } from "@/features/whiteboards/hooks/useWhiteboardsApi"

function StatCard({ icon: Icon, title, value, subtitle, onClick, loading, accentClass }) {
    return (
        <button
            onClick={onClick}
            className="text-left w-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm"
            aria-label={`Navigate to ${title}`}
        >
            <Card size="sm" className="cursor-pointer transition-all hover:bg-accent/50 hover:shadow-sm">
                <CardHeader className="pb-1">
                    <CardTitle className="flex items-center gap-1.5 text-[11px] text-muted-foreground font-medium uppercase tracking-wide">
                        <Icon className={`size-3.5 ${accentClass || "text-muted-foreground"}`} />
                        {title}
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <Skeleton className="h-7 w-14" />
                    ) : (
                        <>
                            <div className="text-2xl font-semibold tracking-tight tabular-nums">{value ?? "—"}</div>
                            {subtitle && (
                                <div className="text-[11px] text-muted-foreground mt-0.5">{subtitle}</div>
                            )}
                        </>
                    )}
                </CardContent>
            </Card>
        </button>
    )
}

export function OverviewCards() {
    const navigate = useNavigate()
    const { data: tasksData, isLoading: tasksLoading } = useTasksAnalytics()
    const { data: notesData, isLoading: notesLoading } = useNotesAnalytics()
    const { data: calendarData, isLoading: calendarLoading } = useCalendarAnalytics()
    const { data: meetings, isLoading: meetingsLoading } = useMeetings()
    const { data: whiteboards, isLoading: whiteboardsLoading } = useWhiteboards()
    const { data: attachmentsData, isLoading: attachmentsLoading } = useRecentAttachments(50)

    // Tasks analytics: status_distribution keys are enum .value strings:
    //   TaskStatus.TODO = "TODO", TaskStatus.IN_PROGRESS = "IN PROGRESS", TaskStatus.DONE = "DONE"
    const statusDist = tasksData?.status_distribution || {}
    const pendingTasks = (statusDist["TODO"] ?? 0) + (statusDist["IN PROGRESS"] ?? 0)
    const completedTasks = statusDist["DONE"] ?? 0
    const overdueCount = tasksData?.overdue ?? 0

    // Upcoming meetings: status enum values are uppercase strings
    // MeetingStatus: CREATED, SCHEDULED, ACTIVE, IDLE, ENDED, CANCELLED
    const upcomingMeetings = meetings
        ? meetings.filter(
            (m) =>
                m.scheduled_start &&
                new Date(m.scheduled_start) > new Date() &&
                m.status !== "CANCELLED" &&
                m.status !== "ENDED"
        ).length
        : null

    // Calendar analytics: { total, today, upcoming, ... }
    const todayEvents = calendarData?.today ?? null

    // Notes analytics: { total, favorite, archived, recent_notes, monthly_created }
    const notesCount = notesData?.total ?? null

    const whiteboardsCount = whiteboards?.length ?? null

    // Attachments count from recent (total_count field from AttachmentListResponse)
    const attachmentsCount = attachmentsData?.total_count ?? null

    const cards = [
        {
            icon: ListTodo,
            title: "Pending",
            value: tasksLoading ? null : pendingTasks,
            subtitle: "active tasks",
            onClick: () => navigate("/tasks"),
            loading: tasksLoading,
            accentClass: "text-blue-500",
        },
        {
            icon: CheckSquare,
            title: "Completed",
            value: tasksLoading ? null : completedTasks,
            subtitle: "tasks done",
            onClick: () => navigate("/tasks"),
            loading: tasksLoading,
            accentClass: "text-emerald-500",
        },
        ...(overdueCount > 0
            ? [{
                icon: AlertCircle,
                title: "Overdue",
                value: tasksLoading ? null : overdueCount,
                subtitle: "past due",
                onClick: () => navigate("/tasks"),
                loading: tasksLoading,
                accentClass: "text-destructive",
            }]
            : []),
        {
            icon: Presentation,
            title: "Upcoming",
            value: meetingsLoading ? null : upcomingMeetings,
            subtitle: "meetings",
            onClick: () => navigate("/meetings"),
            loading: meetingsLoading,
            accentClass: "text-violet-500",
        },
        {
            icon: Calendar,
            title: "Today",
            value: calendarLoading ? null : todayEvents,
            subtitle: "events",
            onClick: () => navigate("/calendar"),
            loading: calendarLoading,
            accentClass: "text-emerald-500",
        },
        {
            icon: FileText,
            title: "Notes",
            value: notesLoading ? null : notesCount,
            subtitle: "total",
            onClick: () => navigate("/notes"),
            loading: notesLoading,
            accentClass: "text-amber-500",
        },
        {
            icon: PenSquare,
            title: "Boards",
            value: whiteboardsLoading ? null : whiteboardsCount,
            subtitle: "total",
            onClick: () => navigate("/whiteboards"),
            loading: whiteboardsLoading,
            accentClass: "text-rose-500",
        },
        {
            icon: Paperclip,
            title: "Files",
            value: attachmentsLoading ? null : attachmentsCount,
            subtitle: "uploaded",
            onClick: () => navigate("/tasks"),
            loading: attachmentsLoading,
            accentClass: "text-slate-500",
        },
    ]

    return (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-4 xl:grid-cols-8 gap-3">
            {cards.map((card) => (
                <StatCard key={card.title} {...card} />
            ))}
        </div>
    )
}
