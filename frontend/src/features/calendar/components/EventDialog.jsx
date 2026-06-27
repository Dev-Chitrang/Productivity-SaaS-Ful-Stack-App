import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { EventForm } from "./EventForm"
import { buildCreateDefaults, buildEditDefaults, toCreatePayload, toUpdatePayload } from "../api/calendarMapper"
import { useCreateEvent, useUpdateEvent } from "../hooks/useCalendarApi"
import { dayjs } from "../utils/dateUtils"
import toast from "react-hot-toast"

/**
 * Unified Create / Edit dialog.
 *
 * @param {Object} props
 * @param {boolean} props.open
 * @param {"create"|"edit"} props.mode
 * @param {import("../api/calendarTypes").CalendarEventResponse|null} [props.event]
 * @param {string} [props.anchorDate]   - "YYYY-MM-DD", used in create mode
 * @param {number} [props.anchorHour]   - 0–23, used in create mode
 * @param {() => void} props.onClose
 */
export function EventDialog({ open, mode = "create", event = null, anchorDate, anchorHour, onClose }) {
    // Build the HH:mm string for the anchor hour if provided
    const anchorHHmm = anchorHour != null
        ? `${String(anchorHour).padStart(2, "0")}:00`
        : null

    const defaultValues =
        mode === "edit" && event
            ? buildEditDefaults(event)
            : buildCreateDefaults(anchorDate ?? null, anchorHHmm)

    const createMutation = useCreateEvent(onClose)
    const updateMutation = useUpdateEvent(onClose)
    const isPending = mode === "create" ? createMutation.isPending : updateMutation.isPending

    function handleSubmit(formValues) {
        if (mode === "create") {
            // Frontend past-time guard — never send past events to the API
            const tz = formValues.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone
            const startDT = dayjs.tz(`${formValues.start_date}T${formValues.start_hhmm}`, tz)
            if (startDT.isBefore(dayjs())) {
                toast.error("Cannot create events in the past. Please select a future start time.")
                return
            }
            createMutation.mutate(toCreatePayload(formValues))
        } else {
            updateMutation.mutate({ id: event.id, payload: toUpdatePayload(formValues) })
        }
    }

    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="max-w-lg">
                <DialogHeader>
                    <DialogTitle>
                        {mode === "create" ? "Create event" : "Edit event"}
                    </DialogTitle>
                </DialogHeader>

                <EventForm
                    key={mode === "edit" ? (event?.id ?? "edit") : "new"}
                    defaultValues={defaultValues}
                    onSubmit={handleSubmit}
                    isPending={isPending}
                    mode={mode}
                />

                <DialogFooter className="mt-2">
                    <Button variant="outline" size="sm" onClick={onClose} disabled={isPending}>
                        Cancel
                    </Button>
                    <Button size="sm" type="submit" form="event-form" disabled={isPending}>
                        {isPending
                            ? mode === "create" ? "Creating…" : "Saving…"
                            : mode === "create" ? "Create event" : "Save changes"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
