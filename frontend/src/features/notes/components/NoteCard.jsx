import { Pin, Star, Archive, Trash2, RotateCcw } from "lucide-react"
import { cn } from "@/lib/utils"
import { formatRelativeTime } from "../utils/notesUtils"

export function NoteCard({ note, isSelected, onSelect, onTogglePin, onToggleFavorite, onArchive, onDelete, onRestore }) {
    const displayTitle = note.title || "Untitled"
    const isDeleted = !!note.deleted_at

    const handlePinClick = (e) => {
        e.stopPropagation()
        onTogglePin?.({ id: note.id, currentlyPinned: note.is_pinned })
    }

    const handleFavoriteClick = (e) => {
        e.stopPropagation()
        onToggleFavorite?.({ id: note.id, currentlyFavorited: note.is_favorite })
    }

    const handleArchiveClick = (e) => {
        e.stopPropagation()
        onArchive?.(note)
    }

    const handleDeleteClick = (e) => {
        e.stopPropagation()
        onDelete?.(note)
    }

    const handleRestoreClick = (e) => {
        e.stopPropagation()
        onRestore?.(note)
    }

    const handleClick = () => {
        onSelect?.(isSelected ? null : note.id)
    }

    const handleKeyDown = (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault()
            handleClick()
        }
    }

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
                                note.is_pinned
                                    ? "text-muted-foreground fill-muted-foreground"
                                    : "text-muted-foreground opacity-0 group-hover:opacity-100 hover:text-foreground",
                            )}
                            aria-label={note.is_pinned ? "Unpin note" : "Pin note"}
                        >
                            <Pin className="size-3 shrink-0" />
                        </button>
                        <span className="text-xs font-medium truncate text-foreground">
                            {displayTitle}
                        </span>
                    </div>
                </div>
                <p className="text-[11px] text-muted-foreground mt-1 line-clamp-2">
                    {note.content ? stripContent(note.content) : "No content"}
                </p>
                <div className="flex items-center gap-2 mt-1.5">
                    <span className="text-[10px] text-muted-foreground">
                        {formatRelativeTime(note.updated_at)}
                    </span>
                    {note.category && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-sm bg-muted text-muted-foreground">
                            {note.category}
                        </span>
                    )}
                </div>
            </div>
            <div className="absolute top-1.5 right-2 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                {isDeleted ? (
                    <button
                        type="button"
                        onClick={handleRestoreClick}
                        className="p-1 rounded-sm text-muted-foreground hover:text-green-600"
                        aria-label="Restore note"
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
                            aria-label={note.is_favorite ? "Remove from favorites" : "Add to favorites"}
                            title={note.is_favorite ? "Remove from favorites" : "Add to favorites"}
                        >
                            <Star className={cn("size-3", note.is_favorite ? "text-amber-500 fill-amber-500" : "text-muted-foreground")} />
                        </button>
                        <button
                            type="button"
                            onClick={handleArchiveClick}
                            className="p-1 rounded-sm text-muted-foreground hover:text-foreground"
                            aria-label={note.is_archived ? "Unarchive note" : "Archive note"}
                            title={note.is_archived ? "Unarchive" : "Archive"}
                        >
                            <Archive className="size-3" />
                        </button>
                        <button
                            type="button"
                            onClick={handleDeleteClick}
                            className="p-1 rounded-sm text-muted-foreground hover:text-destructive"
                            aria-label="Delete note"
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

function stripContent(content) {
    if (!content) return ""
    try {
        const parsed = JSON.parse(content)
        let text = ""
        const walk = (nodes) => {
            if (!nodes) return
            for (const node of nodes) {
                if (node.type === "text" && node.text) text += node.text + " "
                if (node.content) walk(node.content)
            }
        }
        if (parsed.content) walk(parsed.content)
        return text.trim() || "No content"
    } catch {
        return content.trim() || "No content"
    }
}
