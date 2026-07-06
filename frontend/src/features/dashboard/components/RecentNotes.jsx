import { useNavigate } from "react-router-dom"
import { FileText } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useNotesAnalytics } from "../hooks/useDashboardApi"

function formatRelative(dateStr) {
    if (!dateStr) return ""
    const d = new Date(dateStr)
    const now = new Date()
    const diffMs = now - d
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    if (diffDays === 0) return "Today"
    if (diffDays === 1) return "Yesterday"
    if (diffDays < 7) return `${diffDays}d ago`
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}

export function RecentNotes() {
    const navigate = useNavigate()
    const { data: notesData, isLoading } = useNotesAnalytics()
    // notes analytics: { total, favorite, archived, recent_notes: [{id, title, updated_at}], monthly_created }
    const recentNotes = notesData?.recent_notes || []

    return (
        <Card size="sm">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-1.5 text-xs">
                        <FileText className="size-3.5 text-muted-foreground" />
                        Recent Notes
                    </CardTitle>
                    <button
                        onClick={() => navigate("/notes")}
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
                ) : recentNotes.length > 0 ? (
                    recentNotes.slice(0, 5).map((n) => (
                        <button
                            key={n.id}
                            // Notes page doesn't deep-link by id — navigate to /notes which will load the list
                            // The user can select from the list
                            onClick={() => navigate("/notes")}
                            className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left transition-colors hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        >
                            <div className="flex size-5 shrink-0 items-center justify-center rounded bg-amber-500/10">
                                <FileText className="size-3 text-amber-600 dark:text-amber-400" />
                            </div>
                            <span className="flex-1 text-xs truncate">{n.title || "Untitled"}</span>
                            <span className="text-[10px] text-muted-foreground shrink-0">
                                {formatRelative(n.updated_at)}
                            </span>
                        </button>
                    ))
                ) : (
                    <p className="text-xs text-muted-foreground py-3 text-center">No notes yet</p>
                )}
            </CardContent>
        </Card>
    )
}
