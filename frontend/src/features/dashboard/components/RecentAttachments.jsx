import { useNavigate } from "react-router-dom"
import { Paperclip, FileImage, FileText, File, Archive } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useRecentAttachments } from "../hooks/useDashboardApi"

function getFileIcon(extension) {
    const img = ["png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico"]
    const doc = ["pdf", "doc", "docx", "txt", "md", "rtf", "odt"]
    const arch = ["zip", "rar", "7z", "tar", "gz", "bz2"]
    const ext = extension?.toLowerCase()
    if (img.includes(ext)) return { Icon: FileImage, colorClass: "text-blue-500" }
    if (doc.includes(ext)) return { Icon: FileText, colorClass: "text-amber-500" }
    if (arch.includes(ext)) return { Icon: Archive, colorClass: "text-slate-500" }
    return { Icon: File, colorClass: "text-muted-foreground" }
}

function formatSize(bytes) {
    if (!bytes) return ""
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

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

// Navigate to the owning entity based on attachment entity_type
function getEntityRoute(attachment) {
    const type = attachment.entity_type?.toUpperCase()
    if (type === "TASK") return `/tasks?task=${attachment.entity_id}`
    if (type === "CALENDAR_EVENT") return `/calendar`
    if (type === "MEETING_SESSION") return null // needs meeting_id, can't deep-link without it
    return null
}

const ENTITY_LABELS = {
    TASK: "Task",
    CALENDAR_EVENT: "Event",
    MEETING_SESSION: "Session",
}

export function RecentAttachments() {
    const navigate = useNavigate()
    const { data, isLoading } = useRecentAttachments(8)
    const attachments = data?.attachments || []

    return (
        <Card size="sm">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-1.5 text-xs">
                        <Paperclip className="size-3.5 text-muted-foreground" />
                        Recent Uploads
                    </CardTitle>
                </div>
            </CardHeader>
            <CardContent className="space-y-1">
                {isLoading ? (
                    <div className="space-y-2 py-1">
                        <Skeleton className="h-7 w-full" />
                        <Skeleton className="h-7 w-3/4" />
                        <Skeleton className="h-7 w-5/6" />
                    </div>
                ) : attachments.length > 0 ? (
                    attachments.map((a) => {
                        const { Icon, colorClass } = getFileIcon(a.extension)
                        const route = getEntityRoute(a)
                        const entityLabel = ENTITY_LABELS[a.entity_type?.toUpperCase()] || ""
                        const Row = route ? "button" : "div"
                        return (
                            <Row
                                key={a.id}
                                onClick={route ? () => navigate(route) : undefined}
                                className={[
                                    "flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left",
                                    route
                                        ? "transition-colors hover:bg-accent/50 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                                        : "",
                                ].join(" ")}
                            >
                                <Icon className={`size-3.5 shrink-0 ${colorClass}`} />
                                <span className="flex-1 text-xs truncate">{a.original_filename}</span>
                                {entityLabel && (
                                    <span className="text-[10px] text-muted-foreground shrink-0 hidden sm:inline">{entityLabel}</span>
                                )}
                                <span className="text-[10px] text-muted-foreground shrink-0">
                                    {formatRelative(a.created_at)}
                                </span>
                                {a.size > 0 && (
                                    <span className="text-[10px] text-muted-foreground shrink-0 hidden md:inline">
                                        {formatSize(a.size)}
                                    </span>
                                )}
                            </Row>
                        )
                    })
                ) : (
                    <p className="text-xs text-muted-foreground py-3 text-center">No recent uploads</p>
                )}
            </CardContent>
        </Card>
    )
}
