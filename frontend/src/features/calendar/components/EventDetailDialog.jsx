import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
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

/**
 * @param {Object} props
 * @param {boolean} props.open
 * @param {import("../api/calendarTypes").CalendarOccurrence|null} props.event
 * @param {() => void} props.onClose
 * @param {() => void} props.onEdit
 * @param {() => void} props.onDelete
 */
export function EventDetailDialog({ open, event, onClose, onEdit, onDelete }) {
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
            <DialogContent className="max-w-sm">
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

                    {/* Description */}
                    {event.description && (
                        <div className={cn("px-3 py-2.5 border text-xs leading-relaxed", faint)}>
                            {event.description}
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
