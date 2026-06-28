import { useMemo } from "react"
import { Star, Pin, Archive, Trash2, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { TaskStatus, TaskPriority } from "../api/tasksTypes"

export function FilterPanel({ filters, onChange, onClose }) {
    const quickFilters = [
        { key: "favorite", label: "Favorites", icon: Star, active: !!filters.favorite },
        { key: "pinned", label: "Pinned", icon: Pin, active: !!filters.pinned },
        { key: "archived", label: "Archived", icon: Archive, active: !!filters.archived },
        { key: "deleted", label: "Trash", icon: Trash2, active: !!filters.deleted },
    ]

    const handleQuickFilter = (key) => {
        const next = { ...filters }
        if (next[key]) {
            delete next[key]
        } else {
            next[key] = true
        }
        onChange(next)
    }

    const handleStatusFilter = (status) => {
        const next = { ...filters }
        if (next.status === status) {
            delete next.status
        } else {
            next.status = status
        }
        onChange(next)
    }

    const handlePriorityFilter = (priority) => {
        const next = { ...filters }
        if (next.priority === priority) {
            delete next.priority
        } else {
            next.priority = priority
        }
        onChange(next)
    }

    const handleDueDateFilter = () => {
        const next = { ...filters }
        if (next.due_date) {
            delete next.due_date
        } else {
            next.due_date = "today"
        }
        onChange(next)
    }

    const hasActiveFilters = useMemo(
        () => Object.values(filters).some(Boolean),
        [filters],
    )

    return (
        <div className="w-56 border-l border-border bg-card h-full overflow-y-auto">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                <span className="text-xs font-medium text-foreground">Filters</span>
                <div className="flex items-center gap-1">
                    {hasActiveFilters && (
                        <Button variant="ghost" size="xs" onClick={() => onChange({})}>
                            Clear
                        </Button>
                    )}
                    <Button variant="ghost" size="icon-xs" onClick={onClose} aria-label="Close filters">
                        <X className="size-3" />
                    </Button>
                </div>
            </div>

            <div className="px-3 py-3 space-y-1">
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
                    Quick Filters
                </p>
                {quickFilters.map(({ key, label, icon: Icon, active }) => (
                    <button
                        key={key}
                        type="button"
                        onClick={() => handleQuickFilter(key)}
                        className={cn(
                            "flex items-center gap-2 w-full px-2 py-1.5 text-xs rounded-sm transition-colors",
                            active
                                ? "bg-primary/10 text-primary"
                                : "text-muted-foreground hover:text-foreground hover:bg-muted",
                        )}
                    >
                        <Icon className={cn("size-3.5", active && "fill-current")} />
                        {label}
                    </button>
                ))}
            </div>

            <Separator />

            <div className="px-3 py-3 space-y-1">
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
                    Status
                </p>
                {Object.values(TaskStatus).map((status) => {
                    const label = status === "IN PROGRESS" ? "In Progress" : status.charAt(0) + status.slice(1).toLowerCase()
                    return (
                        <button
                            key={status}
                            type="button"
                            onClick={() => handleStatusFilter(status)}
                            className={cn(
                                "flex items-center gap-2 w-full px-2 py-1.5 text-xs rounded-sm transition-colors",
                                filters.status === status
                                    ? "bg-primary/10 text-primary"
                                    : "text-muted-foreground hover:text-foreground hover:bg-muted",
                            )}
                        >
                            {label}
                        </button>
                    )
                })}
            </div>

            <Separator />

            <div className="px-3 py-3 space-y-1">
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
                    Priority
                </p>
                {Object.values(TaskPriority).map((priority) => (
                    <button
                        key={priority}
                        type="button"
                        onClick={() => handlePriorityFilter(priority)}
                        className={cn(
                            "flex items-center gap-2 w-full px-2 py-1.5 text-xs rounded-sm transition-colors",
                            filters.priority === priority
                                ? "bg-primary/10 text-primary"
                                : "text-muted-foreground hover:text-foreground hover:bg-muted",
                        )}
                    >
                        {priority.charAt(0) + priority.slice(1).toLowerCase()}
                    </button>
                ))}
            </div>

            <Separator />

            <div className="px-3 py-3 space-y-1">
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
                    Due Date
                </p>
                <button
                    type="button"
                    onClick={handleDueDateFilter}
                    className={cn(
                        "flex items-center gap-2 w-full px-2 py-1.5 text-xs rounded-sm transition-colors",
                        filters.due_date
                            ? "bg-primary/10 text-primary"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted",
                    )}
                >
                    Due Today
                </button>
            </div>
        </div>
    )
}
