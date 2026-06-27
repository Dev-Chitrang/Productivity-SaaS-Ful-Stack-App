import { NoteCard } from "./NoteCard"
import { NoteListSkeleton } from "./LoadingSkeleton"
import { EmptyState } from "./EmptyState"

export function NoteList({
    notes,
    isLoading,
    selectedNoteId,
    onSelectNote,
    onTogglePin,
    onToggleFavorite,
    onArchive,
    onDelete,
    onRestore,
    onCreateNote,
    emptyType = "no-notes",
}) {
    if (isLoading) return <NoteListSkeleton />

    if (!notes || notes.length === 0) {
        return <EmptyState type={emptyType} onCreateNote={onCreateNote} />
    }

    return (
        <div className="flex flex-col">
            {notes.map((note) => (
                <NoteCard
                    key={note.id}
                    note={note}
                    isSelected={selectedNoteId === note.id}
                    onSelect={onSelectNote}
                    onTogglePin={onTogglePin}
                    onToggleFavorite={onToggleFavorite}
                    onArchive={onArchive}
                    onDelete={onDelete}
                    onRestore={onRestore}
                />
            ))}
        </div>
    )
}