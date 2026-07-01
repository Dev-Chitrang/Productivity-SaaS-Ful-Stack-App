export function WhiteboardCardSkeleton() {
    return (
        <div className="animate-pulse border-b border-border px-4 py-3">
            <div className="flex items-center gap-2 mb-2">
                <div className="h-3.5 bg-muted rounded w-2/3" />
                <div className="h-3.5 bg-muted rounded w-4" />
            </div>
            <div className="h-2 bg-muted rounded w-24" />
        </div>
    )
}

export function WhiteboardListSkeleton() {
    return (
        <div>
            <WhiteboardCardSkeleton />
            <WhiteboardCardSkeleton />
            <WhiteboardCardSkeleton />
            <WhiteboardCardSkeleton />
            <WhiteboardCardSkeleton />
        </div>
    )
}
