import { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useAuthContext } from "@/context/AuthContext"
import {
    useSessionDetail,
    useSessionRecordings,
    useSessionTranscripts,
    useSessionAnalysis,
    useSessionAnalysisStatus,
} from "../hooks/useMeetingsApi"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import {
    ArrowLeft,
    CalendarBlank,
    Clock,
    Users,
    Microphone,
    FileText,
    Robot,
    Paperclip,
    DownloadSimple,
    CheckCircle,
    XCircle,
    Spinner,
    User,
    UserCircle,
    Crown,
} from "@phosphor-icons/react"
import toast from "react-hot-toast"
import { meetingsApi } from "../api/meetingsApi"

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(iso) {
    if (!iso) return "—"
    return new Date(iso).toLocaleDateString("en-US", {
        weekday: "short",
        month: "long",
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
    if (h > 0) return `${h}h ${m}m ${s}s`
    if (m > 0) return `${m}m ${s}s`
    return `${s}s`
}

function formatSize(bytes) {
    if (!bytes || bytes === 0) return "0 B"
    const units = ["B", "KB", "MB", "GB"]
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
    return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

function formatFileDuration(seconds) {
    if (!seconds || seconds <= 0) return null
    const m = Math.floor(seconds / 60)
    const s = Math.floor(seconds % 60)
    if (m > 0) return `${m}m ${s}s`
    return `${s}s`
}

const SESSION_STATUS_CLASSES = {
    ACTIVE:
        "bg-green-100 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-800",
    ENDED: "bg-muted text-muted-foreground border-border",
    CANCELLED:
        "bg-red-100 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800",
}

const SESSION_STATUS_LABELS = {
    ACTIVE: "Active",
    ENDED: "Ended",
    CANCELLED: "Cancelled",
}

const PARTICIPANT_STATUS_LABELS = {
    ADMITTED: "Attended",
    LEFT: "Left",
    REMOVED: "Removed",
    REJECTED: "Rejected",
    WAITING: "Waiting",
}

// ─── Participants Section ─────────────────────────────────────────────────────

function ParticipantsSection({ participants, hostId }) {
    if (!participants || participants.length === 0) {
        return (
            <div className="py-6 text-center">
                <p className="text-xs text-muted-foreground">
                    No participant records for this session.
                </p>
            </div>
        )
    }

    // Sort: host first, then registered, then guests
    const sorted = [...participants].sort((a, b) => {
        const rank = (p) => {
            if (p.user_id === hostId) return 0
            if (p.participant_type === "REGISTERED") return 1
            return 2
        }
        return rank(a) - rank(b)
    })

    return (
        <div className="divide-y divide-border">
            {sorted.map((p) => {
                const isHost = p.user_id === hostId
                const isGuest = p.participant_type === "GUEST"
                const name = p.user_name || p.guest_name || "Unknown"
                const statusLabel = PARTICIPANT_STATUS_LABELS[p.status] || p.status
                const attended = p.status === "ADMITTED" || p.status === "LEFT"

                // Determine role label and icon
                let roleLabel, RoleIcon, roleClass
                if (isHost) {
                    roleLabel = "Host"
                    RoleIcon = Crown
                    roleClass =
                        "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800"
                } else if (isGuest) {
                    roleLabel = "Guest"
                    RoleIcon = UserCircle
                    roleClass = "bg-muted text-muted-foreground border-border"
                } else {
                    roleLabel = "Registered"
                    RoleIcon = User
                    roleClass = "bg-muted text-muted-foreground border-border"
                }

                return (
                    <div key={p.id} className="flex items-center gap-3 py-2.5 text-xs">
                        {/* Avatar */}
                        <div
                            className={`flex size-6 shrink-0 items-center justify-center rounded-full ${isHost
                                    ? "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
                                    : "bg-muted text-muted-foreground"
                                }`}
                        >
                            <RoleIcon className="size-3.5" weight={isHost ? "fill" : "regular"} />
                        </div>

                        {/* Name + join/leave times */}
                        <div className="min-w-0 flex-1">
                            <p className="font-medium truncate">{name}</p>
                            <p className="text-muted-foreground">
                                {roleLabel}
                                {p.joined_at && ` · Joined ${formatTime(p.joined_at)}`}
                                {p.left_at && ` · Left ${formatTime(p.left_at)}`}
                            </p>
                        </div>

                        {/* Role badge */}
                        <span
                            className={`inline-flex items-center gap-0.5 rounded border px-1.5 py-0.5 text-[10px] font-medium shrink-0 ${roleClass}`}
                        >
                            {isHost && <Crown className="size-2.5" weight="fill" />}
                            {roleLabel}
                        </span>

                        {/* Attendance badge */}
                        <span
                            className={`inline-flex items-center gap-0.5 rounded border px-1.5 py-0.5 text-[10px] font-medium shrink-0 ${attended
                                    ? "bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-800"
                                    : "bg-muted text-muted-foreground border-border"
                                }`}
                        >
                            {attended && <CheckCircle className="size-2.5" weight="fill" />}
                            {statusLabel}
                        </span>
                    </div>
                )
            })}
        </div>
    )
}

// ─── Recording Artifact ───────────────────────────────────────────────────────

function RecordingsArtifact({ meetingId, sessionId, hasRecording }) {
    const [open, setOpen] = useState(false)
    const { data: recordings = [], isLoading } = useSessionRecordings(
        meetingId,
        sessionId,
        open
    )

    const handleDownload = async (rec) => {
        try {
            const { data } = await meetingsApi.downloadRecording(rec.id)
            const url = URL.createObjectURL(data)
            const a = document.createElement("a")
            a.href = url
            a.download = rec.filename
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            URL.revokeObjectURL(url)
        } catch {
            toast.error("Failed to download recording.")
        }
    }

    return (
        <div>
            <button
                type="button"
                onClick={() => setOpen((v) => !v)}
                className="w-full flex items-center justify-between py-3 text-left"
                aria-expanded={open}
            >
                <div className="flex items-center gap-2">
                    <Microphone className="size-4 text-muted-foreground" />
                    <span className="text-xs font-medium">Recording</span>
                    {!hasRecording && (
                        <span className="text-[10px] text-muted-foreground">(none)</span>
                    )}
                </div>
                <span className="text-[10px] text-muted-foreground">{open ? "Hide" : "Show"}</span>
            </button>

            {open && (
                <div className="pb-3">
                    {isLoading ? (
                        <div className="space-y-2">
                            <Skeleton className="h-8 w-full" />
                            <Skeleton className="h-8 w-4/5" />
                        </div>
                    ) : recordings.length === 0 ? (
                        <p className="text-xs text-muted-foreground py-2 text-center">
                            No recordings for this session.
                        </p>
                    ) : (
                        <div className="divide-y divide-border rounded border border-border">
                            {recordings.map((rec) => (
                                <div
                                    key={rec.id}
                                    className="flex items-center gap-3 px-3 py-2.5 text-xs"
                                >
                                    <Microphone className="size-4 shrink-0 text-muted-foreground" />
                                    <div className="min-w-0 flex-1">
                                        <p className="truncate font-medium">{rec.filename}</p>
                                        <div className="flex items-center gap-3 text-muted-foreground mt-0.5">
                                            {rec.duration != null && (
                                                <span>{formatFileDuration(rec.duration)}</span>
                                            )}
                                            <span>{formatSize(rec.size)}</span>
                                        </div>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="icon-xs"
                                        onClick={() => handleDownload(rec)}
                                        aria-label="Download recording"
                                    >
                                        <DownloadSimple className="size-3.5" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

// ─── Transcript Artifact ──────────────────────────────────────────────────────

function TranscriptArtifact({ meetingId, sessionId, hasTranscript }) {
    const [open, setOpen] = useState(false)
    const { data: transcripts = [], isLoading } = useSessionTranscripts(
        meetingId,
        sessionId,
        open
    )

    const handleDownload = async (tx) => {
        try {
            const { data } = await meetingsApi.downloadTranscript(tx.id)
            const url = URL.createObjectURL(data)
            const a = document.createElement("a")
            a.href = url
            a.download = tx.filename
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            URL.revokeObjectURL(url)
        } catch {
            toast.error("Failed to download transcript.")
        }
    }

    return (
        <div>
            <button
                type="button"
                onClick={() => setOpen((v) => !v)}
                className="w-full flex items-center justify-between py-3 text-left"
                aria-expanded={open}
            >
                <div className="flex items-center gap-2">
                    <FileText className="size-4 text-muted-foreground" />
                    <span className="text-xs font-medium">Transcript</span>
                    {!hasTranscript && (
                        <span className="text-[10px] text-muted-foreground">(none)</span>
                    )}
                </div>
                <span className="text-[10px] text-muted-foreground">{open ? "Hide" : "Show"}</span>
            </button>

            {open && (
                <div className="pb-3">
                    {isLoading ? (
                        <div className="space-y-2">
                            <Skeleton className="h-8 w-full" />
                        </div>
                    ) : transcripts.length === 0 ? (
                        <p className="text-xs text-muted-foreground py-2 text-center">
                            No transcripts for this session.
                        </p>
                    ) : (
                        <div className="divide-y divide-border rounded border border-border">
                            {transcripts.map((tx) => (
                                <div
                                    key={tx.id}
                                    className="flex items-center gap-3 px-3 py-2.5 text-xs"
                                >
                                    <FileText className="size-4 shrink-0 text-muted-foreground" />
                                    <div className="min-w-0 flex-1">
                                        <p className="truncate font-medium">{tx.filename}</p>
                                        <p className="text-muted-foreground mt-0.5">{formatSize(tx.size)}</p>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="icon-xs"
                                        onClick={() => handleDownload(tx)}
                                        aria-label="Download transcript"
                                    >
                                        <DownloadSimple className="size-3.5" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

// ─── AI Analysis Artifact ─────────────────────────────────────────────────────

function PriorityBadge({ priority }) {
    const colors = {
        HIGH: "bg-red-100 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800",
        MEDIUM:
            "bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-300 dark:border-yellow-800",
        LOW: "bg-green-100 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-800",
    }
    return (
        <span
            className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-medium ${colors[priority] || colors.MEDIUM
                }`}
        >
            {priority}
        </span>
    )
}

function AIAnalysisArtifact({ meetingId, sessionId, hasAnalysis }) {
    const [open, setOpen] = useState(false)
    const { data: analysis, isLoading } = useSessionAnalysis(meetingId, sessionId, open)
    const { data: statusData } = useSessionAnalysisStatus(meetingId, sessionId, open)
    const status = statusData?.status || analysis?.status

    return (
        <div>
            <button
                type="button"
                onClick={() => setOpen((v) => !v)}
                className="w-full flex items-center justify-between py-3 text-left"
                aria-expanded={open}
            >
                <div className="flex items-center gap-2">
                    <Robot className="size-4 text-muted-foreground" />
                    <span className="text-xs font-medium">AI Analysis</span>
                    {!hasAnalysis && (
                        <span className="text-[10px] text-muted-foreground">(none)</span>
                    )}
                </div>
                <span className="text-[10px] text-muted-foreground">{open ? "Hide" : "Show"}</span>
            </button>

            {open && (
                <div className="pb-3">
                    {isLoading ? (
                        <div className="space-y-2">
                            <Skeleton className="h-4 w-full" />
                            <Skeleton className="h-4 w-3/4" />
                            <Skeleton className="h-4 w-1/2" />
                        </div>
                    ) : status === "PENDING" || status === "PROCESSING" ? (
                        <div className="flex items-center gap-2 py-3 text-xs text-muted-foreground">
                            <Spinner className="size-3.5 animate-spin" />
                            {status === "PENDING"
                                ? "Waiting to process AI analysis..."
                                : "Generating AI analysis..."}
                        </div>
                    ) : !analysis ? (
                        <p className="text-xs text-muted-foreground py-2 text-center">
                            No AI analysis for this session.
                        </p>
                    ) : status === "FAILED" ? (
                        <div className="flex items-center gap-2 py-3 text-xs text-destructive">
                            <XCircle className="size-4" />
                            AI analysis could not be generated.
                        </div>
                    ) : analysis.status === "COMPLETED" ? (
                        <div className="space-y-4 pt-1">
                            {analysis.summary && (
                                <div>
                                    <h4 className="mb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                                        Summary
                                    </h4>
                                    <p className="text-xs">{analysis.summary}</p>
                                </div>
                            )}
                            {analysis.agenda_coverage_percentage != null && (
                                <div>
                                    <h4 className="mb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                                        Agenda Coverage
                                    </h4>
                                    <div className="flex items-center gap-3">
                                        <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                                            <div
                                                className="h-full rounded-full bg-primary transition-all"
                                                style={{ width: `${analysis.agenda_coverage_percentage}%` }}
                                            />
                                        </div>
                                        <span className="text-xs font-medium tabular-nums">
                                            {analysis.agenda_coverage_percentage}%
                                        </span>
                                    </div>
                                </div>
                            )}
                            {analysis.covered_points?.length > 0 && (
                                <div>
                                    <h4 className="mb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                                        Covered Points
                                    </h4>
                                    <ul className="space-y-1">
                                        {analysis.covered_points.map((pt, i) => (
                                            <li key={i} className="flex items-start gap-2 text-xs">
                                                <CheckCircle
                                                    className="mt-0.5 size-3.5 shrink-0 text-green-500"
                                                    weight="fill"
                                                />
                                                {pt}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            {analysis.out_of_agenda_points?.length > 0 && (
                                <div>
                                    <h4 className="mb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                                        Out of Agenda
                                    </h4>
                                    <ul className="space-y-1">
                                        {analysis.out_of_agenda_points.map((pt, i) => (
                                            <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                                                <span className="mt-0.5 shrink-0">&bull;</span>
                                                {pt}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            {analysis.suggested_tasks?.length > 0 && (
                                <div>
                                    <h4 className="mb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                                        Suggested Tasks
                                    </h4>
                                    <div className="space-y-2">
                                        {analysis.suggested_tasks.map((task, i) => (
                                            <div key={i} className="space-y-1 rounded border border-border p-2.5">
                                                <div className="flex items-start justify-between gap-2">
                                                    <p className="text-xs font-medium">{task.title}</p>
                                                    <PriorityBadge priority={task.priority} />
                                                </div>
                                                {task.description && (
                                                    <p className="text-xs text-muted-foreground">{task.description}</p>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : null}
                </div>
            )}
        </div>
    )
}

// ─── Attachments Placeholder ──────────────────────────────────────────────────

function AttachmentsPlaceholder() {
    return (
        <div className="flex items-center gap-2 py-3">
            <Paperclip className="size-4 text-muted-foreground" />
            <span className="text-xs font-medium text-muted-foreground">Attachments</span>
            <span className="inline-flex items-center rounded border border-dashed border-border px-1.5 py-0.5 text-[10px] text-muted-foreground">
                Coming soon
            </span>
        </div>
    )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

function SessionDetailPage() {
    const { id: meetingId, sessionId } = useParams()
    const navigate = useNavigate()
    const { isAuthenticated } = useAuthContext()

    const { data: session, isLoading, isError, error } = useSessionDetail(
        meetingId,
        sessionId
    )

    // Guests never reach this page
    if (!isAuthenticated) {
        return (
            <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
                <Card>
                    <CardContent className="py-12 text-center">
                        <p className="text-sm text-muted-foreground">
                            Session history is only available for logged-in users.
                        </p>
                        <Button
                            variant="outline"
                            size="sm"
                            className="mt-4"
                            onClick={() => navigate(`/meetings/${meetingId}`)}
                        >
                            Back to Meeting
                        </Button>
                    </CardContent>
                </Card>
            </div>
        )
    }

    if (isLoading) {
        return (
            <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6 space-y-4">
                <Skeleton className="h-8 w-24" />
                <Skeleton className="h-40 w-full" />
                <Skeleton className="h-32 w-full" />
            </div>
        )
    }

    if (isError) {
        const is403 = error?.response?.status === 403
        return (
            <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate(`/meetings/${meetingId}`)}
                    className="mb-4"
                >
                    <ArrowLeft className="size-3.5" />
                    Back
                </Button>
                <Card>
                    <CardContent className="py-12 text-center">
                        <p className="text-sm text-muted-foreground">
                            {is403
                                ? "You do not have permission to access this session."
                                : "Session not found."}
                        </p>
                    </CardContent>
                </Card>
            </div>
        )
    }

    if (!session) return null

    const statusClass =
        SESSION_STATUS_CLASSES[session.status] || SESSION_STATUS_CLASSES.ENDED
    const statusLabel = SESSION_STATUS_LABELS[session.status] || session.status
    const { artifacts = {} } = session

    return (
        <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
            {/* Back nav */}
            <div className="mb-4">
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate(`/meetings/${meetingId}`)}
                >
                    <ArrowLeft className="size-3.5" />
                    Back to Meeting
                </Button>
            </div>

            {/* General info */}
            <Card>
                <CardHeader>
                    <div className="flex items-start justify-between gap-3">
                        <CardTitle className="text-base">Session Details</CardTitle>
                        <span
                            className={`inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-medium shrink-0 ${statusClass}`}
                        >
                            {statusLabel}
                        </span>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-xs">
                        <div>
                            <p className="text-muted-foreground flex items-center gap-1 mb-0.5">
                                <CalendarBlank className="size-3" /> Date
                            </p>
                            <p className="font-medium">{formatDate(session.started_at)}</p>
                        </div>
                        <div>
                            <p className="text-muted-foreground flex items-center gap-1 mb-0.5">
                                <Clock className="size-3" /> Start Time
                            </p>
                            <p className="font-medium">{formatTime(session.started_at)}</p>
                        </div>
                        <div>
                            <p className="text-muted-foreground flex items-center gap-1 mb-0.5">
                                <Clock className="size-3" /> End Time
                            </p>
                            <p className="font-medium">{formatTime(session.ended_at)}</p>
                        </div>
                        <div>
                            <p className="text-muted-foreground flex items-center gap-1 mb-0.5">
                                <Clock className="size-3" /> Duration
                            </p>
                            <p className="font-medium">{formatDuration(session.duration_seconds)}</p>
                        </div>
                    </div>

                    <Separator />

                    <div>
                        <h3 className="text-xs font-medium flex items-center gap-1.5 mb-3">
                            <Users className="size-3.5 text-muted-foreground" />
                            Participants
                        </h3>
                        <ParticipantsSection
                            participants={session.participants}
                            hostId={session.host_id}
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Artifacts — lazy-loaded on expand */}
            <Card className="mt-4">
                <CardHeader>
                    <CardTitle className="text-sm">Artifacts</CardTitle>
                </CardHeader>
                <CardContent className="divide-y divide-border">
                    <RecordingsArtifact
                        meetingId={meetingId}
                        sessionId={sessionId}
                        hasRecording={artifacts.has_recording}
                    />
                    <TranscriptArtifact
                        meetingId={meetingId}
                        sessionId={sessionId}
                        hasTranscript={artifacts.has_transcript}
                    />
                    <AIAnalysisArtifact
                        meetingId={meetingId}
                        sessionId={sessionId}
                        hasAnalysis={artifacts.has_ai_analysis}
                    />
                    <AttachmentsPlaceholder />
                </CardContent>
            </Card>
        </div>
    )
}

export default SessionDetailPage
