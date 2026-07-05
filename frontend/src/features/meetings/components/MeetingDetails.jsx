import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import {
  MEETING_STATUS_LABELS,
  MEETING_STATUS_CLASSES,
  MEETING_STATUS_DOTS,
  MEETING_TYPE_LABELS,
  MEETING_TYPE_CLASSES,
  MeetingType,
} from "../api/meetingTypes"
import { ParticipantList } from "./ParticipantList"
import {
  Stop,
  Prohibit,
  PencilSimple,
  Copy,
  Microphone,
  FileText,
  Trash,
} from "@phosphor-icons/react"
import toast from "react-hot-toast"

export function MeetingDetails({
  meeting,
  participants,
  isHost,
  connectionStates,
  onEnd,
  onCancel,
  onEdit,
  onDelete,
}) {
  const statusLabel = MEETING_STATUS_LABELS[meeting?.status] || ""
  const statusClass = MEETING_STATUS_CLASSES[meeting?.status] || ""
  const statusDot = MEETING_STATUS_DOTS[meeting?.status] || "bg-gray-500"

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(
        `${window.location.origin}/meetings/${meeting.id}`
      )
      toast.success("Meeting link copied.")
    } catch {
      toast.error("Failed to copy link.")
    }
  }

  const createdDate = meeting?.created_at
    ? new Date(meeting.created_at).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : ""

  const isScheduled = meeting?.meeting_type === MeetingType.SCHEDULED
  const isActive = meeting?.status === "ACTIVE"
  const isCreated = meeting?.status === "CREATED"
  const isIdle = meeting?.status === "IDLE"
  const isEnded = meeting?.status === "ENDED"
  const isCancelled = meeting?.status === "CANCELLED"
  const status = meeting?.status

  // INSTANT meeting actions
  const showEndMeeting = isHost && isActive
  const showCancelMeeting = isHost && isScheduled && (status === "SCHEDULED")
  const showEditMeeting = isHost && isScheduled && (status === "SCHEDULED")
  const showDeleteMeeting = isHost && (
    (isScheduled && isEnded) ||
    (!isScheduled && (isCreated || isIdle || isEnded)) ||
    isCancelled
  )

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <CardTitle className="text-base">{meeting?.title}</CardTitle>
              {meeting?.description && (
                <p className="mt-1 text-xs text-muted-foreground">
                  {meeting.description}
                </p>
              )}
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              {meeting?.meeting_type && (
                <span
                  className={`inline-flex items-center rounded-none border px-2 py-0.5 text-[10px] font-medium ${MEETING_TYPE_CLASSES[meeting.meeting_type] || ""}`}
                >
                  {MEETING_TYPE_LABELS[meeting.meeting_type] || meeting.meeting_type}
                </span>
              )}
              <span
                className={`inline-flex items-center gap-1.5 rounded-none border px-2 py-0.5 text-[10px] font-medium shrink-0 ${statusClass}`}
              >
                <span className={`size-1.5 rounded-full ${statusDot}`} />
                {statusLabel}
              </span>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-muted-foreground">Code</span>
              <p className="font-mono mt-0.5">{meeting?.meeting_code}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Created</span>
              <p className="mt-0.5">{createdDate}</p>
            </div>
          </div>

          {meeting?.meeting_type === "SCHEDULED" && (
            <div className="rounded border border-border bg-muted/30 p-3 space-y-2">
              <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                Scheduled Meeting
              </p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                {meeting.scheduled_date && meeting.scheduled_time && (
                  <div>
                    <span className="text-muted-foreground">Scheduled Time</span>
                    <p className="mt-0.5 font-medium">
                      {new Date(`${meeting.scheduled_date}T${meeting.scheduled_time}`).toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                )}
                {meeting.duration && (
                  <div>
                    <span className="text-muted-foreground">Duration</span>
                    <p className="mt-0.5 font-medium">{meeting.duration} min</p>
                  </div>
                )}
                {meeting.timezone && (
                  <div>
                    <span className="text-muted-foreground">Timezone</span>
                    <p className="mt-0.5 font-medium">{meeting.timezone}</p>
                  </div>
                )}
                {meeting.agenda && (
                  <div className="col-span-2">
                    <span className="text-muted-foreground">Agenda</span>
                    <p className="mt-0.5 whitespace-pre-wrap">{meeting.agenda}</p>
                  </div>
                )}
                {meeting.invited_participants_count != null && meeting.invited_participants_count > 0 && (
                  <div className="col-span-2">
                    <span className="text-muted-foreground">Invited Participants</span>
                    <p className="mt-0.5 font-medium">{meeting.invited_participants_count}</p>
                  </div>
                )}
                {meeting.enable_ai_analysis && (
                  <div className="col-span-2">
                    <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                      AI Analysis enabled
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Microphone className="size-3.5" />
              <span>Audio only</span>
            </div>
            {meeting?.enable_recording && (
              <span className="inline-flex items-center rounded border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground">
                Recording
              </span>
            )}
            {meeting?.enable_transcript && (
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <FileText className="size-3.5" />
                <span>Transcript</span>
              </div>
            )}
          </div>

          <Separator />

          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyLink}
              aria-label="Copy meeting link"
            >
              <Copy className="size-3.5" />
              Copy Link
            </Button>

            {showEndMeeting && (
              <Button
                variant="destructive"
                size="sm"
                onClick={onEnd}
                aria-label="End meeting"
              >
                <Stop className="size-3.5" />
                End Meeting
              </Button>
            )}

            {showCancelMeeting && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onCancel}
                aria-label="Cancel meeting"
              >
                <Prohibit className="size-3.5" />
                Cancel Meeting
              </Button>
            )}

            {showEditMeeting && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onEdit}
                aria-label="Edit meeting"
              >
                <PencilSimple className="size-3.5" />
                Edit
              </Button>
            )}

            {showDeleteMeeting && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onDelete}
                aria-label="Delete meeting"
              >
                <Trash className="size-3.5" />
                Delete
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-6">
            <div>
              <CardTitle className="text-sm">Participants</CardTitle>
              <p className="text-xs text-muted-foreground">
                {(participants || []).filter((p) => p.status === "WAITING" || p.status === "ADMITTED").length || 0}
              </p>
            </div>
            <div>
              <CardTitle className="text-sm">Invited Participants</CardTitle>
              <p className="text-xs text-muted-foreground">
                {meeting?.invited_participants_count ?? 0}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <ParticipantList
            participants={participants}
            hostId={meeting?.host_id}
            connectionStates={connectionStates}
          />
        </CardContent>
      </Card>
    </div>
  )
}
