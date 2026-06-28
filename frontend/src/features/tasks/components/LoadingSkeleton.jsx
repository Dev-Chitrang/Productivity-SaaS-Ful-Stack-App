export function TaskCardSkeleton() {
    return (
        <div className="animate-pulse border-b border-border px-4 py-3">
            <div className="flex items-center gap-2 mb-2">
                <div className="h-3.5 bg-muted rounded w-1/2" />
                <div className="h-5 bg-muted rounded w-14" />
            </div>
            <div className="flex items-center gap-2">
                <div className="h-2 bg-muted rounded w-16" />
                <div className="h-2 bg-muted rounded w-20" />
            </div>
        </div>
    )
}

export function TaskListSkeleton() {
    return (
        <div>
            <TaskCardSkeleton />
            <TaskCardSkeleton />
            <TaskCardSkeleton />
            <TaskCardSkeleton />
            <TaskCardSkeleton />
        </div>
    )
}

export function TaskEditorSkeleton() {
    return (
        <div className="animate-pulse p-6 space-y-4">
            <div className="h-6 bg-muted rounded w-1/2" />
            <div className="flex gap-2">
                <div className="h-7 bg-muted rounded w-24" />
                <div className="h-7 bg-muted rounded w-24" />
                <div className="h-7 bg-muted rounded w-28" />
            </div>
            <div className="h-3 bg-muted rounded w-1/3" />
            <div className="space-y-3 pt-4">
                <div className="h-3 bg-muted rounded w-full" />
                <div className="h-3 bg-muted rounded w-full" />
                <div className="h-3 bg-muted rounded w-5/6" />
            </div>
        </div>
    )
}
