import { useTaskHistory } from "../hooks/useTasksApi"
import { TaskActivityItem } from "./TaskActivityItem"
import { History } from "lucide-react"

export function TaskActivityTimeline({ taskId }) {
    const { data, isLoading } = useTaskHistory(taskId)

    if (!taskId) return null

    if (isLoading) {
        return (
            <div className="px-4 py-3 space-y-3">
                <div className="animate-pulse h-3 bg-muted rounded w-20" />
                <div className="animate-pulse h-3 bg-muted rounded w-full" />
                <div className="animate-pulse h-3 bg-muted rounded w-3/4" />
            </div>
        )
    }

    const history = data?.history || []

    if (history.length === 0) {
        return (
            <div className="border-t border-border px-4 py-4">
                <p className="text-[11px] font-medium text-muted-foreground mb-2 flex items-center gap-1.5">
                    <History className="size-3" />
                    Activity
                </p>
                <p className="text-[11px] text-muted-foreground/60 italic">No activity recorded yet.</p>
            </div>
        )
    }

    return (
        <div className="border-t border-border px-4 py-3">
            <p className="text-[11px] font-medium text-muted-foreground mb-3 flex items-center gap-1.5">
                <History className="size-3" />
                Activity
            </p>
            <div className="max-h-48 overflow-y-auto">
                {history.map((item, idx) => (
                    <TaskActivityItem
                        key={item.id}
                        activity={item}
                        isLast={idx === history.length - 1}
                    />
                ))}
            </div>
        </div>
    )
}
