import { useNavigate } from "react-router-dom"
import { PenSquare } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useWhiteboards } from "@/features/whiteboards/hooks/useWhiteboardsApi"
import { useMemo } from "react"

function formatRelative(dateStr) {
    if (!dateStr) return ""
    const d = new Date(dateStr)
    const now = new Date()
    const diffDays = Math.floor((now - d) / (1000 * 60 * 60 * 24))
    if (diffDays === 0) return "Today"
    if (diffDays === 1) return "Yesterday"
    if (diffDays < 7) return `${diffDays}d ago`
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}

export function RecentWhiteboards() {
    const navigate = useNavigate()
    const { data: whiteboards, isLoading } = useWhiteboards()

    const recent = useMemo(() => {
        if (!whiteboards) return []
        return [...whiteboards]
            .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
            .slice(0, 5)
    }, [whiteboards])

    return (
        <Card size="sm">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-1.5 text-xs">
                        <PenSquare className="size-3.5 text-muted-foreground" />
                        Recent Whiteboards
                    </CardTitle>
                    <button
                        onClick={() => navigate("/whiteboards")}
                        className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                    >
                        View all
                    </button>
                </div>
            </CardHeader>
            <CardContent className="space-y-1">
                {isLoading ? (
                    <div className="space-y-2 py-1">
                        <Skeleton className="h-7 w-full" />
                        <Skeleton className="h-7 w-3/4" />
                        <Skeleton className="h-7 w-5/6" />
                    </div>
                ) : recent.length > 0 ? (
                    recent.map((wb) => (
                        <button
                            key={wb.id}
                            onClick={() => navigate("/whiteboards")}
                            className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left transition-colors hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        >
                            <div className="flex size-5 shrink-0 items-center justify-center rounded bg-rose-500/10">
                                <PenSquare className="size-3 text-rose-600 dark:text-rose-400" />
                            </div>
                            <span className="flex-1 text-xs truncate">{wb.title || "Untitled"}</span>
                            <span className="text-[10px] text-muted-foreground shrink-0">
                                {formatRelative(wb.updated_at)}
                            </span>
                        </button>
                    ))
                ) : (
                    <p className="text-xs text-muted-foreground py-3 text-center">No whiteboards yet</p>
                )}
            </CardContent>
        </Card>
    )
}
