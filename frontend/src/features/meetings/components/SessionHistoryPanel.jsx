import { useNavigate } from "react-router-dom"
import { useSessionHistory } from "../hooks/useMeetingsApi"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ClockCounterClockwise, CalendarBlank, Users, CaretRight } from "@phosphor-icons/react"

// ─── Helpers ────────────────────────────────────────────────────────────────

function formatDate(iso) {
    if (!iso) return "—"
    return new Date(iso).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    })
}

function formatTime(iso) {
    if (!iso) return "—"
    return new Date(iso).toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
    })
}

function formatDuration(seconds) {
    if (!seconds || seconds <= 0) return "—"
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = Math.floor(seconds % 60)
    if (h > 0) return `${h}h ${m}m`
    if (m > 0) return `${m}m ${s}s`
    return `${s}s`
}

const SESSION_STATUS_CLASSES = {
    ACTIVE: "bg-green-100 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-800",
    ENDED: "bg-muted text-muted-foreground border-border",
    CANCELLED: "bg-red-100 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800",
}

const SESSION_STATUS_LABELS = {
    ACTIVE: "Active",
    ENDED: "Ended",
    CANCELLED: "Cancelled",
}

// ─── Skeleton ────────────────────────────────────────────────────────────────

function SessionHistorySkeleton() {
    return (
        <div className="divide-y divide-border">
            {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-3 px-4 py-3">
                    <Skeleton className="size-8 rounded-full shrink-0" />
                    <div className="flex-1 space-y-1.5">
                        <Skeleton className="h-3 w-2/5" />
                        <Skeleton className="h-3 w-3/5" />
                    </div>
                    <Skeleton className="h-5 w-14 rounded" />
                </div>
            ))}
        </div>
    )
}

// ─── Session Row ─────────────────────────────────────────────────────────────

function SessionRow({ session, index, meetingId }) {
    const navigate = useNavigate()
    const statusClass = SESSION_STATUS_CLASSES[session.status] || SESSION_STATUS_CLASSES.ENDED
    const statusLabel = SESSION_STATUS_LABELS[session.status] || session.status

    return (
        <button
            type="button"
            onClick={() => navigate(`/meetings/${meetingId}/sessions/${session.id}`)}
            className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-muted/50 transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            aria-label={`View Session ${index} details`}
        >
            {/* Index badge */}
            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium text-muted-foreground">
                {index}
            </div>

            {/* Info */}
            <div className="min-w-0 flex-1 space-y-0.5">
                <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-medium text-foreground flex items-center gap-1">
                        <CalendarBlank className="size-3 shrink-0" />
                        {formatDate(session.started_at)}
                    </span>
                    <span className="text-xs text-muted-foreground">
                        {formatTime(session.started_at)}
                        {session.ended_at ? ` – ${formatTime(session.ended_at)}` : ""}
                    </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                        <ClockCounterClockwise className="size-3 shrink-0" />
                        {formatDuration(session.duration_seconds)}
                    </span>
                    <span className="flex items-center gap-1">
                        <Users className="size-3 shrink-0" />
                        {session.participant_count ?? 0}
                    </span>
                </div>
            </div>

            {/* Status badge */}
            <span
                className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-medium shrink-0 ${statusClass}`}
            >
                {statusLabel}
            </span>

            <CaretRight className="size-3.5 text-muted-foreground shrink-0" />
        </button>
    )
}

// ─── Main Panel ──────────────────────────────────────────────────────────────

export function SessionHistoryPanel({ meetingId, isAuthenticated }) {
    const { data: sessions, isLoading, isError, error } = useSessionHistory(
        isAuthenticated ? meetingId : null
    )

    // Guests and unauthenticated users never see session history
    if (!isAuthenticated) return null

    return (
        <Card className="mt-6">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <ClockCounterClockwise className="size-4 text-muted-foreground" />
                    Session History
                </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
                {isLoading ? (
                    <SessionHistorySkeleton />
                ) : isError ? (
                    <div className="px-4 py-8 text-center">
                        {error?.response?.status === 403 ? (
                            <p className="text-sm text-muted-foreground">
                                You do not have permission to access this session.
                            </p>
                        ) : (
                            <p className="text-sm text-muted-foreground">
                                Failed to load session history.
                            </p>
                        )}
                    </div>
                ) : !sessions || sessions.length === 0 ? (
                    <div className="flex flex-col items-center justify-center px-4 py-10 text-center">
                        <div className="mb-3 flex size-10 items-center justify-center rounded-full bg-muted">
                            <ClockCounterClockwise className="size-5 text-muted-foreground" weight="light" />
                        </div>
                        <p className="text-sm font-medium text-foreground mb-1">No sessions yet</p>
                        <p className="text-xs text-muted-foreground max-w-xs">
                            Session history will appear here after meetings have been held.
                        </p>
                    </div>
                ) : (
                    <div className="divide-y divide-border">
                        {sessions.map((session, idx) => (
                            <SessionRow
                                key={session.id}
                                session={session}
                                index={sessions.length - idx}
                                meetingId={meetingId}
                            />
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
