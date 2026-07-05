import { useState, useEffect } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { useAuthContext } from "@/context/AuthContext"
import {
  useMeetingByCode,
  useJoinMeeting,
} from "../hooks/useMeetingsApi"
import { GuestNameForm } from "../components/GuestNameForm"
import { InvalidMeetingPage } from "./InvalidMeetingPage"
import { saveGuestSession } from "../utils/guestSession"
import { ThemeToggle } from "@/components/ThemeToggle"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { MeetingDetailSkeleton } from "../components/LoadingSkeleton"
import { MEETING_STATUS_LABELS, MEETING_STATUS_DOTS } from "../api/meetingTypes"
import {
  Video,
  User,
  ArrowLeft,
  Sparkle,
} from "@phosphor-icons/react"
import toast from "react-hot-toast"

function MeetingJoinPage() {
  const { meetingCode } = useParams()
  const navigate = useNavigate()
  const { isAuthenticated, isLoading: authLoading } = useAuthContext()

  const {
    data: meeting,
    isLoading: meetingLoading,
    isError,
  } = useMeetingByCode(meetingCode)

  const joinMeeting = useJoinMeeting()
  const [guestMode, setGuestMode] = useState(false)
  const [joinLoading, setJoinLoading] = useState(false)

  const handleJoin = async (guestName, guestEmail) => {
    setJoinLoading(true)
    try {
      const payload = {}
      if (guestName) payload.guest_name = guestName
      if (guestEmail) payload.guest_email = guestEmail
      await joinMeeting.mutateAsync({ id: meeting.id, ...payload })
      if (guestName) {
        saveGuestSession({ meetingId: meeting.id, guestName, guestEmail, participantId: null })
      }
      navigate(`/meetings/${meeting.id}/room`, {
        state: { guestName: guestName || null, guestEmail: guestEmail || null },
      })
    } catch (err) {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to join meeting.")
    } finally {
      setJoinLoading(false)
    }
  }

  useEffect(() => {
    if (!authLoading && isAuthenticated && meeting && !joinLoading) {
      handleJoin(null)
    }
  }, [authLoading, isAuthenticated, meeting, joinLoading])

  if (authLoading || meetingLoading) {
    return (
      <div className="mx-auto w-full max-w-lg px-4 py-12 sm:px-6">
        <MeetingDetailSkeleton />
      </div>
    )
  }

  if (isError || !meeting) {
    return <InvalidMeetingPage />
  }

  if (meeting.status === "CANCELLED") {
    return <InvalidMeetingPage message="This meeting has been cancelled." />
  }

  if (meeting.status === "ENDED") {
    return <InvalidMeetingPage message="This meeting has ended." />
  }

  if (isAuthenticated) {
    return (
      <div className="mx-auto w-full max-w-lg px-4 py-12 sm:px-6">
        <MeetingDetailSkeleton />
      </div>
    )
  }

  const statusDot = MEETING_STATUS_DOTS[meeting.status]
  const statusLabel = MEETING_STATUS_LABELS[meeting.status]

  return (
    <div className="relative min-h-screen bg-background flex flex-col items-center justify-center px-4 py-12">
      <div className="absolute top-0 left-0 right-0 flex items-center justify-between px-4 py-3">
        <Link
          to="/"
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Back to home"
        >
          <ArrowLeft className="size-3.5" />
          Home
        </Link>
        <ThemeToggle />
      </div>

      <Card className="w-full max-w-lg">
        <CardContent className="p-6 sm:p-8">
          {!guestMode ? (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10">
                  <Video className="size-5 text-primary" weight="fill" />
                </div>
                <div>
                  <p className="text-xs font-medium text-primary">
                    Meeting Invitation
                  </p>
                  <p className="text-xs text-muted-foreground">
                    You have been invited to join a meeting
                  </p>
                </div>
              </div>

              <div>
                <h1 className="text-xl font-semibold text-foreground">
                  {meeting.title}
                </h1>
                {meeting.description && (
                  <p className="mt-1.5 text-sm text-muted-foreground line-clamp-2">
                    {meeting.description}
                  </p>
                )}
              </div>

              <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-1.5">
                  <User className="size-4 text-muted-foreground" weight="fill" />
                  <span className="text-muted-foreground">Hosted by</span>
                  <span className="font-medium text-foreground">
                    {meeting.host_name}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className={`inline-block size-2 rounded-full ${statusDot}`} />
                  <span className="text-muted-foreground">{statusLabel}</span>
                </div>
              </div>

              <div className="space-y-3 pt-2">
                <Button
                  size="lg"
                  className="w-full gap-2"
                  onClick={() => setGuestMode(true)}
                >
                  <Sparkle className="size-4" weight="fill" />
                  Continue as Guest
                </Button>
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    className="flex-1"
                    asChild
                  >
                    <Link to={`/auth?redirect=/m/${meetingCode}`}>
                      Login
                    </Link>
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1"
                    asChild
                  >
                    <Link to={`/auth?mode=signup&redirect=/m/${meetingCode}`}>
                      Sign Up
                    </Link>
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-foreground">
                  Join as Guest
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Enter your name to join &ldquo;{meeting.title}&rdquo;
                </p>
              </div>
              <GuestNameForm
                onJoin={handleJoin}
                isPending={joinLoading}
                onCancel={() => setGuestMode(false)}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default MeetingJoinPage
