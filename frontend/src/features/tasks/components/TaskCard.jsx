import { Pin, Star, Archive, Trash2, RotateCcw, Circle } from "lucide-react"
import { cn } from "@/lib/utils"
import { TaskStatusColors, TaskPriorityColors } from "../api/tasksTypes"
import { formatRelativeTime, isOverdue, isDueToday } from "../utils/tasksUtils"

export function TaskCard({
    task,
    isSelected,
    onSelect,
    onTogglePin,
    onToggleFavorite,
    onArchive,
    onDelete,
    onRestore,
}) {
    const displayTitle = task.title || "Untitled"
    const isDeleted = !!task.deleted_at

    const handlePinClick = (e) => {
        e.stopPropagation()
        onTogglePin?.({ id: task.id, currentlyPinned: task.is_pinned })
    }

    const handleFavoriteClick = (e) => {
        e.stopPropagation()
        onToggleFavorite?.({ id: task.id, currentlyFavorited: task.is_favorite })
    }

    const handleArchiveClick = (e) => {
        e.stopPropagation()
        onArchive?.(task)
    }

    const handleDeleteClick = (e) => {
        e.stopPropagation()
        onDelete?.(task)
    }

    const handleRestoreClick = (e) => {
        e.stopPropagation()
        onRestore?.(task)
    }

    const handleClick = () => {
        onSelect?.(isSelected ? null : task.id)
    }

    const handleKeyDown = (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault()
            handleClick()
        }
    }

    const statusLabel = task.status === "TODO" ? "Todo" : task.status === "IN PROGRESS" ? "In Progress" : "Done"
    const priorityLabel = task.priority === "HIGH" ? "High" : task.priority === "MEDIUM" ? "Med" : "Low"

    const overdue = isOverdue(task.due_date)
    const dueToday = isDueToday(task.due_date)

    return (
        <div className="relative group">
            <div
                role="button"
                tabIndex={0}
                onClick={handleClick}
                onKeyDown={handleKeyDown}
                className={cn(
                    "w-full text-left border-b border-border px-4 py-3 transition-colors hover:bg-muted/50 cursor-pointer",
                    isSelected && "bg-muted",
                    isDeleted && "opacity-60",
                )}
            >
                <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-1.5 min-w-0">
                        <button
                            type="button"
                            onClick={handlePinClick}
                            className={cn(
                                "p-0.5 rounded-sm transition-colors",
                                task.is_pinned
                                    ? "text-muted-foreground fill-muted-foreground"
                                    : "text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-foreground",
                            )}
                            aria-label={task.is_pinned ? "Unpin task" : "Pin task"}
                        >
                            <Pin className="size-3 shrink-0" />
                        </button>
                        <span className="text-xs font-medium truncate text-foreground">
                            {displayTitle}
                        </span>
                    </div>
                </div>
                <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                    <span className={cn("inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded-sm", TaskStatusColors[task.status])}>
                        <Circle className={cn("size-1.5 mr-1", task.status === "TODO" ? "fill-gray-500" : task.status === "IN PROGRESS" ? "fill-blue-500" : "fill-green-500")} />
                        {statusLabel}
                    </span>
                    <span className={cn("inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded-sm", TaskPriorityColors[task.priority])}>
                        {priorityLabel}
                    </span>
                    {task.due_date && (
                        <span className={cn(
                            "text-[10px]",
                            overdue ? "text-red-500 font-medium" : dueToday ? "text-amber-500 font-medium" : "text-muted-foreground",
                        )}>
                            {formatRelativeTime(task.due_date)}
                        </span>
                    )}
                    {task.labels?.length > 0 && task.labels.slice(0, 2).map((label) => (
                        <span key={label} className="text-[10px] px-1.5 py-0.5 rounded-sm bg-muted text-muted-foreground">
                            {label}
                        </span>
                    ))}
                </div>
            </div>
            <div className="absolute top-1.5 right-2 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                {isDeleted ? (
                    <button
                        type="button"
                        onClick={handleRestoreClick}
                        className="p-1 rounded-sm text-muted-foreground hover:text-green-600"
                        aria-label="Restore task"
                        title="Restore"
                    >
                        <RotateCcw className="size-3" />
                    </button>
                ) : (
                    <>
                        <button
                            type="button"
                            onClick={handleFavoriteClick}
                            className="p-1 rounded-sm transition-colors hover:text-amber-500"
                            aria-label={task.is_favorite ? "Remove from favorites" : "Add to favorites"}
                            title={task.is_favorite ? "Remove from favorites" : "Add to favorites"}
                        >
                            <Star className={cn("size-3", task.is_favorite ? "text-amber-500 fill-amber-500" : "text-muted-foreground")} />
                        </button>
                        <button
                            type="button"
                            onClick={handleArchiveClick}
                            className="p-1 rounded-sm text-muted-foreground hover:text-foreground"
                            aria-label={task.is_archived ? "Unarchive task" : "Archive task"}
                            title={task.is_archived ? "Unarchive" : "Archive"}
                        >
                            <Archive className="size-3" />
                        </button>
                        <button
                            type="button"
                            onClick={handleDeleteClick}
                            className="p-1 rounded-sm text-muted-foreground hover:text-destructive"
                            aria-label="Delete task"
                            title="Delete"
                        >
                            <Trash2 className="size-3" />
                        </button>
                    </>
                )}
            </div>
        </div>
    )
}
