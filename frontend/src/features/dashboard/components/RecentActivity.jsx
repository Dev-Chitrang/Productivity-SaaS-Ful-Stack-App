import { useNavigate } from "react-router-dom"
import { Activity, CheckSquare, FileText, PenSquare, Presentation, Paperclip, Brain } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useTasks } from "@/features/tasks/hooks/useTasksApi"
import { useNotesAnalytics, useRecentAttachments, useRecentAnalyses } from "../hooks/useDashboardApi"
import { useMeetings } from "@/features/meetings/hooks/useMeetingsApi"
import { useWhiteboards } from "@/features/whiteboards/hooks/useWhiteboardsApi"
import { useMemo } from "react"

const ACTIVITY_CONFIG = {
    task: {
        icon: CheckSquare,
        colorClass: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
        label: "Task updated",
    },
    note: {
        icon: FileText,
        colorClass: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
        label: "Note updated",
    },
    meeting: {
        icon: Presentation,
        colorClass: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
        label: "Meeting",
    },
    whiteboard: {
        icon: PenSquare,
        colorClass: "bg-rose-500/10 text-rose-600 dark:text-rose-400",
        label: "Whiteboard updated",
    },
    attachment: {
        icon: Paperclip,
        colorClass: "bg-slate-500/10 text-slate-600 dark:text-slate-400",
        label: "File uploaded",
    },
    analysis: {
        icon: Brain,
        colorClass: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
        label: "AI analysis done",
    },
}

function formatRelative(dateStr) {
    if (!dateStr) return ""
    const d = new Date(dateStr)
    const now = new Date()
    const diffMs = now - d
    const diffMins = Math.floor(diffMs / 60_000)
    const diffHours = Math.floor(diffMs / 3_600_000)
    const diffDays = Math.floor(diffMs / 86_400_000)
    if (diffMins < 1) return "Just now"
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays === 1) return "Yesterday"
    if (diffDays < 7) return `${diffDays}d ago`
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}

export function RecentActivity() {
    const navigate = useNavigate()
    const { data: tasksData, isLoading: tasksLoading } = useTasks({ sort_by: "updated_at", sort_order: "desc" })
    const { data: notesData, isLoading: notesLoading } = useNotesAnalytics()
    const { data: meetings, isLoading: meetingsLoading } = useMeetings()
    const { data: whiteboardsData, isLoading: whiteboardsLoading } = useWhiteboards()
    const { data: attachmentsData, isLoading: attLoading } = useRecentAttachments(5)
    const { data: analysesData, isLoading: analysesLoading } = useRecentAnalyses(5)

    const loading = tasksLoading || notesLoading || meetingsLoading || whiteboardsLoading || attLoading || analysesLoading

    const activities = useMemo(() => {
        const items = []

        // Tasks
        if (tasksData?.tasks) {
            tasksData.tasks.slice(0, 4).forEach((t) => {
                items.push({
                    id: `task-${t.id}`,
                    type: "task",
                    title: t.title,
                    timestamp: t.updated_at,
                    onClick: () => navigate(`/tasks?task=${t.id}`),
                })
            })
        }

        // Notes — using analytics recent_notes
        const recentNotes = notesData?.recent_notes || []
        recentNotes.slice(0, 3).forEach((n) => {
            items.push({
                id: `note-${n.id}`,
                type: "note",
                title: n.title || "Untitled note",
                timestamp: n.updated_at,
                onClick: () => navigate("/notes"),
            })
        })

        // Meetings
        if (meetings) {
            meetings.slice(0, 3).forEach((m) => {
                items.push({
                    id: `meeting-${m.id}`,
                    type: "meeting",
                    title: m.title,
                    timestamp: m.updated_at || m.created_at,
                    onClick: () => navigate(`/meetings/${m.id}`),
                })
            })
        }

        // Whiteboards
        if (whiteboardsData) {
            const sorted = [...whiteboardsData]
                .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
                .slice(0, 3)
            sorted.forEach((wb) => {
                items.push({
                    id: `wb-${wb.id}`,
                    type: "whiteboard",
                    title: wb.title || "Untitled board",
                    timestamp: wb.updated_at,
                    onClick: () => navigate("/whiteboards"),
                })
            })
        }

        // Attachments
        const attachments = attachmentsData?.attachments || []
        attachments.slice(0, 3).forEach((a) => {
            // Navigate to owning entity
            let onClick
            const type = a.entity_type?.toUpperCase()
            if (type === "TASK") onClick = () => navigate(`/tasks?task=${a.entity_id}`)
            else if (type === "CALENDAR_EVENT") onClick = () => navigate("/calendar")
            else onClick = () => navigate("/meetings")
            items.push({
                id: `att-${a.id}`,
                type: "attachment",
                title: a.original_filename,
                timestamp: a.created_at,
                onClick,
            })
        })

        // AI analyses
        const analyses = Array.isArray(analysesData) ? analysesData : []
        analyses.slice(0, 3).forEach((a) => {
            items.push({
                id: `analysis-${a.id}`,
                type: "analysis",
                title: `${a.meeting_title} — analysis`,
                timestamp: a.processing_completed_at || a.created_at,
                onClick: () => navigate(`/meetings/${a.meeting_id}/sessions/${a.session_id}`),
            })
        })

        return items
            .filter((i) => i.timestamp)
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 10)
    }, [tasksData, notesData, meetings, whiteboardsData, attachmentsData, analysesData, navigate])

    return (
        <Card size="sm">
            <CardHeader>
                <CardTitle className="flex items-center gap-1.5 text-xs">
                    <Activity className="size-3.5 text-muted-foreground" />
                    Recent Activity
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
                {loading ? (
                    <div className="space-y-2 py-1">
                        <Skeleton className="h-8 w-full" />
                        <Skeleton className="h-8 w-3/4" />
                        <Skeleton className="h-8 w-5/6" />
                        <Skeleton className="h-8 w-2/3" />
                    </div>
                ) : activities.length > 0 ? (
                    activities.map((a) => {
                        const cfg = ACTIVITY_CONFIG[a.type] || ACTIVITY_CONFIG.task
                        const Icon = cfg.icon
                        return (
                            <button
                                key={a.id}
                                onClick={a.onClick}
                                className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left transition-colors hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            >
                                <div className={`flex size-6 shrink-0 items-center justify-center rounded-full ${cfg.colorClass}`}>
                                    <Icon className="size-3" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-xs truncate">{a.title}</p>
                                    <p className="text-[10px] text-muted-foreground">{cfg.label}</p>
                                </div>
                                <span className="text-[10px] text-muted-foreground shrink-0">
                                    {formatRelative(a.timestamp)}
                                </span>
                            </button>
                        )
                    })
                ) : (
                    <p className="text-xs text-muted-foreground py-3 text-center">No recent activity</p>
                )}
            </CardContent>
        </Card>
    )
}
