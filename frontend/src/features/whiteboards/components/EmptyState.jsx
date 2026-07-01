import { LayoutTemplate, SearchX, Archive, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"

export function EmptyState({ type = "no-boards", onCreateBoard }) {
    const config = {
        "no-boards": {
            icon: LayoutTemplate,
            title: "No whiteboards yet",
            description: "Create your first whiteboard to start drawing.",
            action: "Create Whiteboard",
        },
        "no-search": {
            icon: SearchX,
            title: "No search results",
            description: "Try a different search term or clear filters.",
        },
        "no-archived": {
            icon: Archive,
            title: "No archived whiteboards",
            description: "Archived whiteboards will appear here.",
        },
        "no-deleted": {
            icon: Trash2,
            title: "No deleted whiteboards",
            description: "Deleted whiteboards will appear here.",
        },
        "no-board-selected": {
            icon: LayoutTemplate,
            title: "Select a whiteboard",
            description: "Choose a whiteboard from the list or create a new one.",
            action: "Create Whiteboard",
        },
    }

    const { icon: Icon, title, description, action } = config[type] || config["no-boards"]

    return (
        <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
            <div className="flex size-12 items-center justify-center bg-muted mb-4">
                <Icon className="size-5 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-foreground mb-1">{title}</p>
            <p className="text-xs text-muted-foreground max-w-xs mb-5">{description}</p>
            {action && onCreateBoard && (
                <Button size="sm" onClick={onCreateBoard}>
                    {action}
                </Button>
            )}
        </div>
    )
}
