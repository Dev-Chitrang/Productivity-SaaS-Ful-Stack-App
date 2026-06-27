import { cn } from "@/lib/utils"

function Skeleton({ className, ...props }) {
    return (
        <div
            aria-hidden="true"
            className={cn("animate-pulse rounded-none bg-muted", className)}
            {...props}
        />
    )
}

export function MonthViewSkeleton() {
    return (
        <div className="flex flex-col gap-0">
            {/* day-name header row */}
            <div className="grid grid-cols-7 border-b border-border">
                {Array.from({ length: 7 }).map((_, i) => (
                    <div key={i} className="py-2 px-3">
                        <Skeleton className="h-3 w-8" />
                    </div>
                ))}
            </div>
            {/* 6 weeks */}
            {Array.from({ length: 6 }).map((_, wi) => (
                <div key={wi} className="grid grid-cols-7 border-b border-border">
                    {Array.from({ length: 7 }).map((_, di) => (
                        <div key={di} className="min-h-[96px] border-r border-border p-2 last:border-r-0">
                            <Skeleton className="mb-1.5 h-5 w-5" />
                            {di % 3 === 0 && <Skeleton className="h-4 w-full mb-1" />}
                            {di % 5 === 0 && <Skeleton className="h-4 w-3/4" />}
                        </div>
                    ))}
                </div>
            ))}
        </div>
    )
}

export function WeekViewSkeleton() {
    return (
        <div className="flex flex-col gap-0">
            <div className="grid grid-cols-8 border-b border-border">
                <div className="py-2" />
                {Array.from({ length: 7 }).map((_, i) => (
                    <div key={i} className="py-2 px-3 flex flex-col gap-1">
                        <Skeleton className="h-3 w-8" />
                        <Skeleton className="h-6 w-6" />
                    </div>
                ))}
            </div>
            <div className="grid grid-cols-8">
                <div className="flex flex-col">
                    {Array.from({ length: 12 }).map((_, i) => (
                        <div key={i} className="h-12 border-b border-border px-2 flex items-start pt-1">
                            <Skeleton className="h-3 w-10" />
                        </div>
                    ))}
                </div>
                {Array.from({ length: 7 }).map((_, ci) => (
                    <div key={ci} className="border-l border-border">
                        {Array.from({ length: 12 }).map((_, ri) => (
                            <div key={ri} className="h-12 border-b border-border p-1">
                                {ci === 1 && ri === 2 && <Skeleton className="h-8 w-full" />}
                                {ci === 4 && ri === 5 && <Skeleton className="h-8 w-full" />}
                            </div>
                        ))}
                    </div>
                ))}
            </div>
        </div>
    )
}

export function AgendaSkeleton() {
    return (
        <div className="space-y-6 py-4">
            {Array.from({ length: 5 }).map((_, i) => (
                <div key={i}>
                    <Skeleton className="h-4 w-32 mb-3" />
                    <div className="space-y-2">
                        {Array.from({ length: i % 2 === 0 ? 2 : 1 }).map((_, j) => (
                            <div key={j} className="flex gap-3 p-3 border border-border">
                                <Skeleton className="h-3 w-16 mt-0.5 shrink-0" />
                                <div className="flex-1 space-y-1.5">
                                    <Skeleton className="h-4 w-48" />
                                    <Skeleton className="h-3 w-32" />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    )
}
