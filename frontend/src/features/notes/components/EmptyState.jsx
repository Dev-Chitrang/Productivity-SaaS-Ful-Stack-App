import { FileText, SearchX, Archive, StickyNote } from "lucide-react"
import { Button } from "@/components/ui/button"

export function EmptyState({ type = "no-notes", onCreateNote }) {
    const config = {
        "no-notes": {
            icon: StickyNote,
            title: "No notes yet",
            description: "Create your first note to get started.",
            action: "Create Note",
        },
        "no-search": {
            icon: SearchX,
            title: "No search results",
            description: "Try a different search term or clear filters.",
        },
        "no-archived": {
            icon: Archive,
            title: "No archived notes",
            description: "Archived notes will appear here.",
        },
        "no-deleted": {
            icon: FileText,
            title: "No deleted notes",
            description: "Deleted notes will appear here.",
        },
    }

    const { icon: Icon, title, description, action } = config[type] || config["no-notes"]

    return (
        <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
            <div className="flex size-12 items-center justify-center bg-muted mb-4">
                <Icon className="size-5 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-foreground mb-1">{title}</p>
            <p className="text-xs text-muted-foreground max-w-xs mb-5">{description}</p>
            {action && onCreateNote && (
                <Button size="sm" onClick={onCreateNote}>
                    {action}
                </Button>
            )}
        </div>
    )
}
