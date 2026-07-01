import { useEffect, useRef } from "react"
import { useParams, useNavigate, useLocation } from "react-router-dom"
import { useAuthContext } from "@/context/AuthContext"
import { useMeeting, useMeetingParticipants, useEndMeeting, useLeaveMeeting } from "../hooks/useMeetingsApi"
import { MeetingRoom } from "../components/MeetingRoom"
import { MeetingDetailSkeleton } from "../components/LoadingSkeleton"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Clock } from "@phosphor-icons/react"
import { saveGuestSession, clearGuestSession, getGuestSession, getGuestEmail } from "../utils/guestSession"

function MeetingRoomPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const { user, isAuthenticated, isLoading: authLoading } = useAuthContext()

  const { data: meeting, isLoading } = useMeeting(id)
  const { data: participants } = useMeetingParticipants(id)

  const endMeeting = useEndMeeting()
  const leaveMeeting = useLeaveMeeting()

  const guestName = location.state?.guestName || getGuestSession()?.guestName || null
  const guestEmail = location.state?.guestEmail || getGuestEmail() || null
  const sessionToken = location.state?.sessionToken || null
  const isHost = user?.id === meeting?.host_id
  const sessionSaved = useRef(false)

  useEffect(() => {
    if (guestName && !sessionSaved.current) {
      saveGuestSession({ meetingId: id, guestName, guestEmail, participantId: null })
      sessionSaved.current = true
    }
    if (location.state?.participantId) {
      saveGuestSession({ meetingId: id, guestName, guestEmail, participantId: location.state.participantId })
      sessionSaved.current = true
    }
  }, [guestName, guestEmail, id, location.state?.participantId])

  const handleLeave = () => {
    clearGuestSession()
    const payload = guestEmail ? { guest_email: guestEmail } : {}
    leaveMeeting.mutate({ id, ...payload })
    navigate(`/meetings/${id}`, { replace: true })
  }

  useEffect(() => {
    if (!authLoading && !isAuthenticated && !guestName) {
      navigate("/auth", { replace: true })
    }
  }, [authLoading, isAuthenticated, guestName, navigate])

  const handleEndMeeting = () => {
    endMeeting.mutate(id)
    clearGuestSession()
    navigate(`/meetings/${id}`, { replace: true })
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

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
      <div className="mb-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(`/meetings/${id}`)}
        >
          <ArrowLeft className="size-3.5" />
          Back to Details
        </Button>
      </div>

      <MeetingRoom
        meeting={meeting}
        participants={participants || []}
        hostId={meeting.host_id}
        guestName={guestName}
        guestEmail={guestEmail}
        currentUserId={user?.id}
        isHost={isHost}
        sessionToken={sessionToken}
        onLeave={handleLeave}
        onEndMeeting={handleEndMeeting}
        endMeetingPending={endMeeting.isPending}
      />
    </div>
  )
}

export default MeetingRoomPage
