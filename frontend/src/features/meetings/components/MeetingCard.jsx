import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  MEETING_STATUS_LABELS,
  MEETING_STATUS_CLASSES,
  MEETING_STATUS_DOTS,
  MEETING_TYPE_LABELS,
  MEETING_TYPE_CLASSES,
} from "../api/meetingTypes"
import { useAuthContext } from "@/context/AuthContext"
import { Play, Copy, ArrowRight, Trash } from "@phosphor-icons/react"
import { DeleteMeetingDialog } from "./DeleteMeetingDialog"
import toast from "react-hot-toast"

export function MeetingCard({ meeting }) {
  const navigate = useNavigate()
  const { user } = useAuthContext()
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const isHost = user?.id === meeting?.host_id
  const statusLabel = MEETING_STATUS_LABELS[meeting.status] || meeting.status
  const statusClass = MEETING_STATUS_CLASSES[meeting.status] || ""
  const statusDot = MEETING_STATUS_DOTS[meeting.status] || "bg-gray-500"

  const handleCopyLink = async (e) => {
    e.stopPropagation()
    try {
      await navigator.clipboard.writeText(
        `${window.location.origin}/meetings/${meeting.id}`
      )
      toast.success("Link copied.")
    } catch {
      toast.error("Failed to copy link.")
    }
  }

  const createdDate = new Date(meeting.created_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })

  return (
    <Card
      size="sm"
      className="cursor-pointer transition-colors hover:bg-accent/50"
      onClick={() => navigate(`/meetings/${meeting.id}`)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          navigate(`/meetings/${meeting.id}`)
        }
      }}
      aria-label={`Meeting: ${meeting.title}`}
    >
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <CardTitle className="truncate">{meeting.title}</CardTitle>
            {meeting.description && (
              <CardDescription className="mt-0.5 line-clamp-1">
                {meeting.description}
              </CardDescription>
            )}
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            {meeting.meeting_type && (
              <span
                className={`inline-flex items-center rounded-none border px-2 py-0.5 text-[10px] font-medium ${MEETING_TYPE_CLASSES[meeting.meeting_type] || ""}`}
              >
                {MEETING_TYPE_LABELS[meeting.meeting_type] || meeting.meeting_type}
              </span>
            )}
            <span
              className={`inline-flex items-center gap-1.5 rounded-none border px-2 py-0.5 text-[10px] font-medium ${statusClass}`}
            >
              <span className={`size-1.5 rounded-full ${statusDot}`} />
              {statusLabel}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
            <span>{meeting.meeting_code}</span>
            <span>{createdDate}</span>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={handleCopyLink}
              aria-label="Copy meeting link"
            >
              <Copy />
            </Button>
            {(meeting.status === "ACTIVE" || meeting.status === "IDLE") && (
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={(e) => {
                  e.stopPropagation()
                  navigate(`/meetings/${meeting.id}/room`)
                }}
                aria-label="Join meeting"
              >
                <Play />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={(e) => {
                e.stopPropagation()
                navigate(`/meetings/${meeting.id}`)
              }}
              aria-label="View meeting details"
            >
              <ArrowRight />
            </Button>
            {isHost && (
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={(e) => {
                  e.stopPropagation()
                  setDeleteDialogOpen(true)
                }}
                aria-label="Delete meeting"
                className="text-destructive hover:text-destructive"
              >
                <Trash />
              </Button>
            )}
          </div>
        </div>
      </CardContent>

      <DeleteMeetingDialog
        meeting={meeting}
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
      />
    </Card>
  )
}
