import { Star, Archive, Trash2, RotateCcw, PenSquare } from "lucide-react"
import { cn } from "@/lib/utils"
import { formatRelativeTime } from "../utils/whiteboardUtils"

export function WhiteboardCard({
    board,
    isSelected,
    onSelect,
    onToggleFavorite,
    onArchive,
    onDelete,
    onRestore,
}) {
    const displayTitle = board.title || "Untitled"
    const isDeleted = !!board.deleted_at

    const handleFavoriteClick = (e) => {
        e.stopPropagation()
        onToggleFavorite?.({ id: board.id, currentlyFavorited: board.is_favorite })
    }

    const handleArchiveClick = (e) => {
        e.stopPropagation()
        onArchive?.(board)
    }

    const handleDeleteClick = (e) => {
        e.stopPropagation()
        onDelete?.(board)
    }

    const handleRestoreClick = (e) => {
        e.stopPropagation()
        onRestore?.(board)
    }

    const handleClick = () => {
        onSelect?.(isSelected ? null : board.id)
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
                <div className="flex items-center gap-2 min-w-0">
                    <PenSquare className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-xs font-medium truncate text-foreground">
                        {displayTitle}
                    </span>
                </div>
                <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                    <span className="text-[10px] text-muted-foreground">
                        {formatRelativeTime(board.updated_at)}
                    </span>
                </div>
            </div>
            <div className="absolute top-1.5 right-2 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                {isDeleted ? (
                    <button
                        type="button"
                        onClick={handleRestoreClick}
                        className="p-1 rounded-sm text-muted-foreground hover:text-green-600"
                        aria-label="Restore whiteboard"
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
                            aria-label={board.is_favorite ? "Remove from favorites" : "Add to favorites"}
                            title={board.is_favorite ? "Remove from favorites" : "Add to favorites"}
                        >
                            <Star className={cn("size-3", board.is_favorite ? "text-amber-500 fill-amber-500" : "text-muted-foreground")} />
                        </button>
                        <button
                            type="button"
                            onClick={handleArchiveClick}
                            className="p-1 rounded-sm text-muted-foreground hover:text-foreground"
                            aria-label={board.is_archived ? "Unarchive whiteboard" : "Archive whiteboard"}
                            title={board.is_archived ? "Unarchive" : "Archive"}
                        >
                            <Archive className="size-3" />
                        </button>
                        <button
                            type="button"
                            onClick={handleDeleteClick}
                            className="p-1 rounded-sm text-muted-foreground hover:text-destructive"
                            aria-label="Delete whiteboard"
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
