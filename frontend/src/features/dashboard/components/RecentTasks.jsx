import { useNavigate } from "react-router-dom"
import { CheckSquare, Clock, Timer } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useTasks } from "@/features/tasks/hooks/useTasksApi"
import { useMemo } from "react"

// TaskPriority enum values: LOW, MEDIUM, HIGH (uppercase)
const PRIORITY_CLASS = {
    high: "text-orange-500",
    medium: "text-amber-500",
    low: "text-slate-400",
}

const PRIORITY_LABEL = {
    high: "High",
    medium: "Medium",
    low: "Low",
}

// TaskStatus enum values: "TODO", "IN PROGRESS" (note the space), "DONE"
function StatusIcon({ status }) {
    if (!status) return <Clock className="size-3.5 text-muted-foreground shrink-0" />
    const s = status.toUpperCase()
    if (s === "DONE") return <CheckSquare className="size-3.5 text-emerald-500 shrink-0" />
    if (s === "IN PROGRESS") return <Timer className="size-3.5 text-blue-500 shrink-0" />
    // TODO
    return <Clock className="size-3.5 text-muted-foreground shrink-0" />
}

function formatDue(dateStr) {
    if (!dateStr) return null
    const d = new Date(dateStr)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    d.setHours(0, 0, 0, 0)
    const diff = Math.floor((d - today) / (1000 * 60 * 60 * 24))
    if (diff < 0) return { label: `${Math.abs(diff)}d overdue`, className: "text-destructive" }
    if (diff === 0) return { label: "Due today", className: "text-amber-500" }
    if (diff === 1) return { label: "Due tomorrow", className: "text-muted-foreground" }
    return { label: `Due in ${diff}d`, className: "text-muted-foreground" }
}

export function RecentTasks() {
    const navigate = useNavigate()
    const { data: tasksData, isLoading } = useTasks({ sort_by: "updated_at", sort_order: "desc" })

    const recent = useMemo(() => {
        if (!tasksData?.tasks) return []
        // Filter out completed (DONE) tasks, show active ones
        return tasksData.tasks
            .filter((t) => t.status?.toUpperCase() !== "DONE")
            .slice(0, 6)
    }, [tasksData])

    return (
        <Card size="sm">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-1.5 text-xs">
                        <CheckSquare className="size-3.5 text-muted-foreground" />
                        Active Tasks
                    </CardTitle>
                    <button
                        onClick={() => navigate("/tasks")}
                        className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                    >
                        View all
                    </button>
                </div>
            </CardHeader>
            <CardContent className="space-y-1">
                {isLoading ? (
                    <div className="space-y-2 py-1">
                        <Skeleton className="h-7 w-full" />
                        <Skeleton className="h-7 w-3/4" />
                        <Skeleton className="h-7 w-5/6" />
                    </div>
                ) : recent.length > 0 ? (
                    recent.map((t) => {
                        const due = formatDue(t.due_date)
                        const priority = t.priority?.toLowerCase()
                        return (
                            <button
                                key={t.id}
                                onClick={() => navigate(`/tasks?task=${t.id}`)}
                                className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left transition-colors hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            >
                                <StatusIcon status={t.status} />
                                <span className="flex-1 text-xs truncate">{t.title}</span>
                                {due && (
                                    <span className={`text-[10px] shrink-0 ${due.className}`}>
                                        {due.label}
                                    </span>
                                )}
                                {priority && (
                                    <span className={`text-[10px] font-medium shrink-0 ${PRIORITY_CLASS[priority] || "text-muted-foreground"}`}>
                                        {PRIORITY_LABEL[priority] || t.priority}
                                    </span>
                                )}
                            </button>
                        )
                    })
                ) : (
                    <p className="text-xs text-muted-foreground py-3 text-center">No active tasks</p>
                )}
            </CardContent>
        </Card>
    )
}
