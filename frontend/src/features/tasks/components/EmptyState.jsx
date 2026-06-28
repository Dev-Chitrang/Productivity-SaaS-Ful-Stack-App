import { ListTodo, SearchX, Archive, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"

export function EmptyState({ type = "no-tasks", onCreateTask }) {
    const config = {
        "no-tasks": {
            icon: ListTodo,
            title: "No tasks yet",
            description: "Create your first task to get started.",
            action: "Create Task",
        },
        "no-search": {
            icon: SearchX,
            title: "No search results",
            description: "Try a different search term or clear filters.",
        },
        "no-archived": {
            icon: Archive,
            title: "No archived tasks",
            description: "Archived tasks will appear here.",
        },
        "no-deleted": {
            icon: Trash2,
            title: "No deleted tasks",
            description: "Deleted tasks will appear here.",
        },
    }

    const { icon: Icon, title, description, action } = config[type] || config["no-tasks"]

    return (
        <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
            <div className="flex size-12 items-center justify-center bg-muted mb-4">
                <Icon className="size-5 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-foreground mb-1">{title}</p>
            <p className="text-xs text-muted-foreground max-w-xs mb-5">{description}</p>
            {action && onCreateTask && (
                <Button size="sm" onClick={onCreateTask}>
                    {action}
                </Button>
            )}
        </div>
    )
}
