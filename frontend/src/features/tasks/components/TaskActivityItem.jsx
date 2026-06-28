import { useState } from "react"
import {
    Plus, Pencil, Trash2, RotateCcw, Archive, Pin, Star,
    ArrowUpFromLine, ChevronDown, ChevronUp,
} from "lucide-react"
import { formatDateTime, formatFieldName, formatActionLabel, formatFieldValue } from "../utils/tasksUtils"
import { cn } from "@/lib/utils"

const PREVIEW_MAX = 150

const actionIcons = {
    CREATED: { icon: Plus, color: "text-green-500" },
    UPDATED: { icon: Pencil, color: "text-blue-500" },
    DELETED: { icon: Trash2, color: "text-red-500" },
    RESTORED: { icon: RotateCcw, color: "text-green-500" },
    ARCHIVED: { icon: Archive, color: "text-amber-500" },
    UNARCHIVED: { icon: ArrowUpFromLine, color: "text-blue-500" },
    PINNED: { icon: Pin, color: "text-amber-500" },
    UNPINNED: { icon: Pin, color: "text-muted-foreground" },
    FAVORITED: { icon: Star, color: "text-amber-500" },
    UNFAVORITED: { icon: Star, color: "text-muted-foreground" },
}

function showValueChange(activity) {
    return activity.old_value !== undefined && activity.new_value !== undefined
}

function ValueDisplay({ field, value }) {
    const [expanded, setExpanded] = useState(false)
    const display = formatFieldValue(field, value)
    const isLong = field === "description" && display.length > PREVIEW_MAX

    if (!isLong) {
        return <span className="break-words whitespace-pre-wrap">{display}</span>
    }

    return (
        <span className="break-words whitespace-pre-wrap">
            {expanded ? display : display.slice(0, PREVIEW_MAX) + "\u2026"}
            <button
                type="button"
                onClick={() => setExpanded((p) => !p)}
                className="ml-1 inline-flex items-center gap-0.5 text-[10px] font-medium text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300"
            >
                {expanded ? (
                    <>Show less <ChevronUp className="size-2.5" /></>
                ) : (
                    <>Show more <ChevronDown className="size-2.5" /></>
                )}
            </button>
        </span>
    )
}

export function TaskActivityItem({ activity, isLast }) {
    const config = actionIcons[activity.action] || { icon: Pencil, color: "text-muted-foreground" }
    const Icon = config.icon
    const actionLabel = formatActionLabel(activity.action, activity.field_name)
    const userName = activity.user?.name || "Unknown"

    return (
        <div className="relative flex gap-3 pb-3">
            {!isLast && (
                <div className="absolute left-[11px] top-6 bottom-0 w-px bg-border" />
            )}
            <div className={cn(
                "flex size-6 shrink-0 items-center justify-center rounded-full border border-border bg-card z-10",
            )}>
                <Icon className={cn("size-3", config.color)} />
            </div>
            <div className="flex-1 min-w-0 pt-0.5">
                <div className="flex items-baseline gap-1.5 flex-wrap">
                    <span className="text-xs font-medium text-foreground">{actionLabel}</span>
                    <span className="text-[10px] text-muted-foreground">
                        by {userName} &middot; {formatDateTime(activity.created_at)}
                    </span>
                </div>
                {showValueChange(activity) && (
                    <div className="text-[11px] text-muted-foreground mt-0.5">
                        <span className="font-medium">{formatFieldName(activity.field_name)}</span>
                        {" "}
                        <span className="line-through text-destructive/70">
                            <ValueDisplay field={activity.field_name} value={activity.old_value} />
                        </span>
                        {" → "}
                        <span className="text-green-600 dark:text-green-400">
                            <ValueDisplay field={activity.field_name} value={activity.new_value} />
                        </span>
                    </div>
                )}
            </div>
        </div>
    )
}
