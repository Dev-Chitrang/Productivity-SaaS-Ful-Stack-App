import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useAuthContext } from "@/context/AuthContext"
import {
  useMeeting,
  useMeetingParticipants,
  useEndMeeting,
  useCancelMeeting,
  useDeleteMeeting,
  useJoinMeeting,
} from "../hooks/useMeetingsApi"
import { MeetingDetails } from "../components/MeetingDetails"
import { SessionHistoryPanel } from "../components/SessionHistoryPanel"
import { EditMeetingDialog } from "../components/EditMeetingDialog"
import { JoinMeetingDialog } from "../components/JoinMeetingDialog"
import { MeetingDetailSkeleton } from "../components/LoadingSkeleton"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Video, Clock } from "@phosphor-icons/react"
import toast from "react-hot-toast"

function MeetingDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthContext()

  const { data: meeting, isLoading } = useMeeting(id)
  const { data: participants, refetch: refetchParticipants } = useMeetingParticipants(id)

  const endMeeting = useEndMeeting()
  const cancelMeeting = useCancelMeeting()
  const deleteMeeting = useDeleteMeeting()
  const joinMeeting = useJoinMeeting()

  const [editOpen, setEditOpen] = useState(false)
  const [joinOpen, setJoinOpen] = useState(false)
  const [joinLoading, setJoinLoading] = useState(false)

  const isHost = user?.id === meeting?.host_id
  const isScheduled = meeting?.meeting_type === "SCHEDULED"
  const isActive = meeting?.status === "ACTIVE"
  const isCreated = meeting?.status === "CREATED"
  const isIdle = meeting?.status === "IDLE"
  const isEnded = meeting?.status === "ENDED"

  useEffect(() => {
    if (meeting) {
      refetchParticipants()
    }
  }, [meeting?.id])

  const handleEnd = async () => {
    try {
      await endMeeting.mutateAsync(id)
    } catch { }
  }

  const handleCancel = async () => {
    try {
      await cancelMeeting.mutateAsync(id)
    } catch { }
  }

  const handleDelete = async () => {
    if (confirm("Delete this meeting? This action cannot be undone.")) {
      try {
        await deleteMeeting.mutateAsync(id)
        navigate("/meetings")
      } catch { }
    }
  }

  const handleJoin = async (guestName, guestEmail) => {
    setJoinLoading(true)
    try {
      const payload = {}
      if (guestName) payload.guest_name = guestName
      if (guestEmail) payload.guest_email = guestEmail
      const response = await joinMeeting.mutateAsync({ id, ...payload })
      setJoinOpen(false)
      navigate(`/meetings/${id}/room`, {
        state: {
          guestName: guestName || null,
          guestEmail: guestEmail || null,
          sessionToken: response.data.meeting_session_token,
        },
      })
    } catch (err) {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to join meeting.")
    } finally {
      setJoinLoading(false)
    }
  }

  const handleJoinRoom = () => {
    if (isAuthenticated) {
      handleJoin(null)
    } else {
      setJoinOpen(true)
    }
  }

  if (isLoading) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
        <MeetingDetailSkeleton />
      </div>
    )
  }

  if (!meeting) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-sm text-muted-foreground">Meeting not found.</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={() => navigate("/meetings")}
            >
              Back to Meetings
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const canJoinScheduled =
    !isScheduled ||
    meeting?.can_join === true ||
    (meeting?.can_join !== false &&
      (!meeting?.scheduled_date ||
        !meeting?.scheduled_time ||
        new Date() >= new Date(`${meeting.scheduled_date}T${meeting.scheduled_time}`)))

  const showJoin =
    (isActive || isCreated || isIdle || (!isScheduled && isEnded)) && canJoinScheduled
  const showJoinBlocked =
    isScheduled && (isActive || isCreated || isIdle) && !canJoinScheduled

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
      <div className="mb-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate("/meetings")}
          className="mb-2"
        >
          <ArrowLeft className="size-3.5" />
          Back
        </Button>
      </div>

      {showJoinBlocked && (
        <Card className="mb-4 border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950">
          <CardContent className="flex items-center justify-between py-3">
            <div className="flex items-center gap-2">
              <Clock className="size-4 text-amber-600 dark:text-amber-400" />
              <span className="text-xs font-medium text-amber-700 dark:text-amber-300">
                This meeting has not started yet.
              </span>
            </div>
            <Button size="sm" disabled variant="outline">
              <Video className="size-3.5" />
              Join Now
            </Button>
          </CardContent>
        </Card>
      )}

      {showJoin && (
        <Card className="mb-4 border-primary/20 bg-primary/5">
          <CardContent className="flex items-center justify-between py-3">
            <div className="flex items-center gap-2">
              <Video className="size-4 text-primary" />
              <span className="text-xs font-medium">
                {isActive
                  ? "Meeting is active"
                  : isEnded
                    ? "Meeting has ended. Start a new session"
                    : isIdle
                      ? "Meeting is idle. Join to continue"
                      : "Join to start the meeting"}
              </span>
            </div>
            <Button size="sm" onClick={handleJoinRoom}>
              <Video className="size-3.5" />
              {isEnded ? "Start New Session" : "Join Now"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Meeting-level information only */}
      <MeetingDetails
        meeting={meeting}
        participants={participants}
        isHost={isHost}
        onEnd={handleEnd}
        onCancel={handleCancel}
        onEdit={() => setEditOpen(true)}
        onDelete={handleDelete}
      />

      {/* Session History — registered users only; artifacts live inside each session */}
      <SessionHistoryPanel meetingId={id} isAuthenticated={isAuthenticated} />

      <EditMeetingDialog
        meeting={meeting}
        open={editOpen}
        onOpenChange={setEditOpen}
      />

      <JoinMeetingDialog
        open={joinOpen}
        onOpenChange={setJoinOpen}
        onJoin={handleJoin}
        isPending={joinLoading}
      />
    </div>
  )
}

export default MeetingDetailPage
