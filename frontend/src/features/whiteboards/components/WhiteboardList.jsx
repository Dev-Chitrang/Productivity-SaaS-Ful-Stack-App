import { WhiteboardCard } from "./WhiteboardCard"
import { WhiteboardListSkeleton } from "./LoadingSkeleton"
import { EmptyState } from "./EmptyState"

export function WhiteboardList({
    boards,
    isLoading,
    selectedBoardId,
    onSelectBoard,
    onToggleFavorite,
    onArchive,
    onDelete,
    onRestore,
    onCreateBoard,
    emptyType = "no-boards",
}) {
    if (isLoading) return <WhiteboardListSkeleton />

    if (!boards || boards.length === 0) {
        return <EmptyState type={emptyType} onCreateBoard={onCreateBoard} />
    }

    return (
        <div className="flex flex-col">
            {boards.map((board) => (
                <WhiteboardCard
                    key={board.id}
                    board={board}
                    isSelected={selectedBoardId === board.id}
                    onSelect={onSelectBoard}
                    onToggleFavorite={onToggleFavorite}
                    onArchive={onArchive}
                    onDelete={onDelete}
                    onRestore={onRestore}
                />
            ))}
        </div>
    )
}
