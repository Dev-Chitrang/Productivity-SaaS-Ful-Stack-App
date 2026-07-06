import { useState } from "react"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
import {
    fmtDisplayTime,
    fmtDisplayTimeRange,
    fmtDisplayDate,
    fmtRecurrenceLabel,
} from "../api/calendarMapper"
import { getEventFaintStyle, getEventColorHex } from "../utils/colorUtils"
import { EVENT_TYPE_LABELS } from "../api/calendarTypes"
import { MapPin, RefreshCw, Globe, Tag, CalendarDays, Edit2, Trash2 } from "lucide-react"
import { dayjs } from "../utils/dateUtils"
import { AttachmentPanelContainer } from "@/features/attachments/components/AttachmentPanel"
import {
    useCalendarEventAttachments,
    useUploadCalendarEventAttachment,
    useDeleteCalendarEventAttachment,
} from "@/features/attachments/hooks/useAttachmentsApi"
import { attachmentsApi } from "@/features/attachments/api/attachmentsApi"

/**
 * @param {Object} props
 * @param {boolean} props.open
 * @param {import("../api/calendarTypes").CalendarOccurrence|null} props.event
 * @param {() => void} props.onClose
 * @param {() => void} props.onEdit
 * @param {() => void} props.onDelete
 */
export function EventDetailDialog({ open, event, onClose, onEdit, onDelete }) {
    // Attachment hooks — always called, guarded by enabled:!!eventId inside each hook
    const eventId = event?.id ?? null
    const calendarAttachments = useCalendarEventAttachments(eventId)
    const uploadCalendarAttachment = useUploadCalendarEventAttachment(eventId)
    const deleteCalendarAttachment = useDeleteCalendarEventAttachment(eventId)

    const [showAttachments, setShowAttachments] = useState(false)

    if (!event) return null

    const faint = getEventFaintStyle(event.color)
    const colorHex = getEventColorHex(event.color)
    const recurrence = fmtRecurrenceLabel(event)

    const dateDisplay = (() => {
        if (event.is_all_day) {
            const s = dayjs(event.start_time)
            const e = dayjs(event.end_time)
            if (s.isSame(e, "day")) return fmtDisplayDate(event.start_time)
            return `${fmtDisplayDate(event.start_time)} – ${fmtDisplayDate(event.end_time)}`
        }
        const s = dayjs(event.start_time)
        const e = dayjs(event.end_time)
        if (s.isSame(e, "day")) {
            return `${fmtDisplayDate(event.start_time)}, ${fmtDisplayTimeRange(event.start_time, event.end_time)}`
        }
        return `${fmtDisplayDate(event.start_time)} – ${fmtDisplayDate(event.end_time)}, ${fmtDisplayTimeRange(event.start_time, event.end_time)}`
    })()

    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            {/* Wider to accommodate attachment panel */}
            <DialogContent className="max-w-md">
                {/* Color accent strip */}
                <div
                    className="h-1.5 -mx-4 -mt-4 mb-2"
                    style={{ backgroundColor: colorHex }}
                />

                <DialogHeader>
                    <div className="flex items-start gap-2">
                        <span
                            className="mt-0.5 size-3 shrink-0 rounded-full"
                            style={{ backgroundColor: colorHex }}
                        />
                        <DialogTitle className="text-sm font-semibold leading-snug">
                            {event.title}
                        </DialogTitle>
                    </div>
                </DialogHeader>

                <div className="space-y-2.5 text-xs">
                    {/* Date / time */}
                    <div className="flex items-start gap-2.5 text-muted-foreground">
                        <CalendarDays className="size-3.5 shrink-0 mt-0.5" />
                        <span>{dateDisplay}</span>
                    </div>

                    {/* Timezone */}
                    {event.timezone && (
                        <div className="flex items-center gap-2.5 text-muted-foreground">
                            <Globe className="size-3.5 shrink-0" />
                            <span>{event.timezone}</span>
                        </div>
                    )}

                    {/* Location */}
                    {event.location && (
                        <div className="flex items-center gap-2.5 text-muted-foreground">
                            <MapPin className="size-3.5 shrink-0" />
                            <span>{event.location}</span>
                        </div>
                    )}

                    {/* Event type */}
                    <div className="flex items-center gap-2.5 text-muted-foreground">
                        <Tag className="size-3.5 shrink-0" />
                        <span>{EVENT_TYPE_LABELS[event.event_type] ?? event.event_type}</span>
                    </div>

                    {/* Recurrence */}
                    {recurrence && (
                        <div className="flex items-center gap-2.5 text-muted-foreground">
                            <RefreshCw className="size-3.5 shrink-0" />
                            <span>{recurrence}</span>
                            {event.recurrence_end_date && (
                                <span>(until {fmtDisplayDate(event.recurrence_end_date)})</span>
                            )}
                        </div>
                    )}

                    {/* Event Notes */}
                    {event.description && (
                        <div>
                            <p className="text-[11px] font-medium text-muted-foreground mb-1.5 flex items-center gap-1.5">
                                Notes
                            </p>
                            <div className={cn("px-3 py-2.5 border text-xs leading-relaxed", faint)}>
                                {event.description}
                            </div>
                        </div>
                    )}
                </div>

                {/* ── Attachments ─────────────────────────────────────────── */}
                <Separator />

                <div>
                    <button
                        type="button"
                        onClick={() => setShowAttachments((v) => !v)}
                        className="flex w-full items-center justify-between py-1 text-left focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                        aria-expanded={showAttachments}
                        aria-controls="event-attachments"
                    >
                        <span className="text-xs font-medium text-foreground">Attachments</span>
                        <span className="text-[10px] text-muted-foreground">
                            {showAttachments ? "Hide" : "Show"}
                        </span>
                    </button>

                    {showAttachments && (
                        <div id="event-attachments" className="mt-2">
                            <AttachmentPanelContainer
                                attachments={calendarAttachments.data}
                                isLoading={calendarAttachments.isLoading}
                                isError={calendarAttachments.isError}
                                uploadMutation={uploadCalendarAttachment}
                                deleteMutation={deleteCalendarAttachment}
                                downloadFn={async (attachmentId) => {
                                    const { data } = await attachmentsApi.downloadForCalendarEvent(
                                        eventId,
                                        attachmentId,
                                    )
                                    return data
                                }}
                            />
                        </div>
                    )}
                </div>

                <DialogFooter>
                    <Button variant="outline" size="sm" onClick={onClose}>
                        Close
                    </Button>
                    <Button variant="outline" size="sm" onClick={onEdit} aria-label="Edit event">
                        <Edit2 className="size-3.5" />
                        Edit
                    </Button>
                    <Button variant="destructive" size="sm" onClick={onDelete} aria-label="Delete event">
                        <Trash2 className="size-3.5" />
                        Delete
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
