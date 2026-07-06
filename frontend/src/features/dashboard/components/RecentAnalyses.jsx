import { useNavigate } from "react-router-dom"
import { Brain, CheckCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useRecentAnalyses } from "../hooks/useDashboardApi"

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

export function RecentAnalyses() {
    const navigate = useNavigate()
    const { data: analyses, isLoading } = useRecentAnalyses(5)

    // RecentAIAnalysisItem: { id, session_id, meeting_id, meeting_title, session_date, status, summary, agenda_coverage_percentage, processing_completed_at, created_at }
    const items = Array.isArray(analyses) ? analyses.filter((a) => a.status === "COMPLETED") : []

    return (
        <Card size="sm">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-1.5 text-xs">
                        <Brain className="size-3.5 text-muted-foreground" />
                        Recent AI Analyses
                    </CardTitle>
                    <button
                        onClick={() => navigate("/meetings")}
                        className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                    >
                        View meetings
                    </button>
                </div>
            </CardHeader>
            <CardContent className="space-y-1">
                {isLoading ? (
                    <div className="space-y-2 py-1">
                        <Skeleton className="h-12 w-full" />
                        <Skeleton className="h-12 w-3/4" />
                        <Skeleton className="h-12 w-5/6" />
                    </div>
                ) : items.length > 0 ? (
                    items.map((a) => (
                        <button
                            key={a.id}
                            onClick={() =>
                                navigate(`/meetings/${a.meeting_id}/sessions/${a.session_id}`)
                            }
                            className="flex w-full items-start gap-2 rounded-sm px-2 py-1.5 text-left transition-colors hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        >
                            <CheckCircle className="size-3.5 text-emerald-500 mt-0.5 shrink-0" />
                            <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium truncate">{a.meeting_title}</p>
                                {a.summary && (
                                    <p className="text-[10px] text-muted-foreground line-clamp-1 mt-0.5">
                                        {a.summary.length > 100 ? a.summary.slice(0, 100) + "…" : a.summary}
                                    </p>
                                )}
                                <div className="flex items-center gap-2 mt-0.5">
                                    {a.agenda_coverage_percentage != null && (
                                        <span className="text-[10px] text-muted-foreground">
                                            {a.agenda_coverage_percentage}% coverage
                                        </span>
                                    )}
                                    <span className="text-[10px] text-muted-foreground">
                                        {formatRelative(a.session_date || a.processing_completed_at)}
                                    </span>
                                </div>
                            </div>
                        </button>
                    ))
                ) : (
                    <p className="text-xs text-muted-foreground py-3 text-center">
                        No AI analyses yet
                    </p>
                )}
            </CardContent>
        </Card>
    )
}
