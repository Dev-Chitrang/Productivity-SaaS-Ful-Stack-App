export function NoteCardSkeleton() {
    return (
        <div className="animate-pulse border-b border-border px-4 py-3">
            <div className="h-3.5 bg-muted rounded w-3/4 mb-2" />
            <div className="h-2.5 bg-muted rounded w-1/2 mb-2" />
            <div className="h-2 bg-muted rounded w-1/4" />
        </div>
    )
}

export function NoteListSkeleton() {
    return (
        <div>
            <NoteCardSkeleton />
            <NoteCardSkeleton />
            <NoteCardSkeleton />
            <NoteCardSkeleton />
            <NoteCardSkeleton />
        </div>
    )
}

export function EditorSkeleton() {
    return (
        <div className="animate-pulse p-6 space-y-4">
            <div className="h-6 bg-muted rounded w-1/3" />
            <div className="h-3 bg-muted rounded w-1/4" />
            <div className="space-y-3 pt-6">
                <div className="h-3 bg-muted rounded w-full" />
                <div className="h-3 bg-muted rounded w-full" />
                <div className="h-3 bg-muted rounded w-5/6" />
                <div className="h-3 bg-muted rounded w-full" />
                <div className="h-3 bg-muted rounded w-4/5" />
            </div>
        </div>
    )
}
