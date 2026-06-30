import { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useAuthContext } from "@/context/AuthContext"
import {
  useMeeting,
  useMeetingParticipants,
  useEndMeeting,
  useCancelMeeting,
  useJoinMeeting,
  useRecordings,
  useTranscripts,
  useDeleteRecording,
  useDeleteTranscript,
} from "../hooks/useMeetingsApi"
import { MeetingDetails } from "../components/MeetingDetails"
import { EditMeetingDialog } from "../components/EditMeetingDialog"
import { JoinMeetingDialog } from "../components/JoinMeetingDialog"
import { MeetingDetailSkeleton } from "../components/LoadingSkeleton"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  ArrowLeft,
  Video,
  Microphone,
  FileText,
  DownloadSimple,
  Trash,
  Clock,
} from "@phosphor-icons/react"
import toast from "react-hot-toast"
import { meetingsApi } from "../api/meetingsApi"

function formatSize(bytes) {
  if (!bytes || bytes === 0) return "0 B"
  const units = ["B", "KB", "MB", "GB"]
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return "—"
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

function formatDate(dateStr) {
  if (!dateStr) return "—"
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function handleDownload(url, filename) {
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function MeetingDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user, isAuthenticated } = useAuthContext()

  const { data: meeting, isLoading } = useMeeting(id)
  const { data: participants, refetch: refetchParticipants } = useMeetingParticipants(id)
  const { data: recordings = [], isLoading: recordingsLoading } = useRecordings(id)
  const { data: transcripts = [], isLoading: transcriptsLoading } = useTranscripts(id)

  const endMeeting = useEndMeeting()
  const cancelMeeting = useCancelMeeting()
  const joinMeeting = useJoinMeeting()
  const deleteRecording = useDeleteRecording()
  const deleteTranscript = useDeleteTranscript()

  const [editOpen, setEditOpen] = useState(false)
  const [joinOpen, setJoinOpen] = useState(false)
  const [joinLoading, setJoinLoading] = useState(false)

  const isHost = user?.id === meeting?.host_id
  const isActive = meeting?.status === "ACTIVE"
  const isCreated = meeting?.status === "CREATED"
  const isIdle = meeting?.status === "IDLE"

  useEffect(() => {
    if (meeting) {
      refetchParticipants()
    }
  }, [meeting?.id])

  const handleEnd = async () => {
    try {
      await endMeeting.mutateAsync(id)
    } catch {}
  }

  const handleCancel = async () => {
    try {
      await cancelMeeting.mutateAsync(id)
    } catch {}
  }

  const handleJoin = async (guestName) => {
    setJoinLoading(true)
    try {
      const payload = guestName ? { guest_name: guestName } : {}
      const response = await joinMeeting.mutateAsync({ id, ...payload })
      setJoinOpen(false)
      navigate(`/meetings/${id}/room`, {
        state: { guestName: guestName || null, sessionToken: response.data.meeting_session_token },
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

  const handleDownloadRecording = async (rec) => {
    try {
      const { data } = await meetingsApi.downloadRecording(rec.id)
      const url = URL.createObjectURL(data)
      handleDownload(url, rec.filename)
    } catch {
      toast.error("Failed to download recording.")
    }
  }

  const handleDownloadTranscript = async (tx) => {
    try {
      const { data } = await meetingsApi.downloadTranscript(tx.id)
      const url = URL.createObjectURL(data)
      handleDownload(url, tx.filename)
    } catch {
      toast.error("Failed to download transcript.")
    }
  }

  const handleDeleteRecording = (rec) => {
    if (confirm("Delete this recording?")) {
      deleteRecording.mutate({ recordingId: rec.id, meetingId: id })
    }
  }

  const handleDeleteTranscript = (tx) => {
    if (confirm("Delete this transcript?")) {
      deleteTranscript.mutate({ transcriptId: tx.id, meetingId: id })
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

  const showJoin = isActive || isCreated || isIdle

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

      {showJoin && (
        <Card className="mb-4 border-primary/20 bg-primary/5">
          <CardContent className="flex items-center justify-between py-3">
            <div className="flex items-center gap-2">
              <Video className="size-4 text-primary" />
              <span className="text-xs font-medium">
                {isActive ? "Meeting is active" : "Join to start the meeting"}
              </span>
            </div>
            <Button size="sm" onClick={handleJoinRoom}>
              <Video className="size-3.5" />
              Join Now
            </Button>
          </CardContent>
        </Card>
      )}

      <MeetingDetails
        meeting={meeting}
        participants={participants}
        isHost={isHost}
        onEnd={handleEnd}
        onCancel={handleCancel}
        onEdit={() => setEditOpen(true)}
      />

      {/* Recordings Section */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Recordings</CardTitle>
        </CardHeader>
        <CardContent>
          {recordingsLoading ? (
            <p className="text-xs text-muted-foreground py-4 text-center">Loading...</p>
          ) : recordings.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="flex size-10 items-center justify-center rounded-full bg-muted mb-3">
                <Microphone className="size-5 text-muted-foreground" weight="light" />
              </div>
              <p className="text-sm font-medium text-foreground mb-1">No recordings yet</p>
              <p className="text-xs text-muted-foreground max-w-xs">
                Recordings will appear here after they are uploaded from a meeting session.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {recordings.map((rec) => (
                <div key={rec.id} className="flex items-center gap-3 py-2.5 text-xs">
                  <Microphone className="size-4 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">{rec.filename}</p>
                    <div className="flex items-center gap-3 text-muted-foreground mt-0.5">
                      {rec.duration != null && (
                        <span className="inline-flex items-center gap-1">
                          <Clock className="size-3" />
                          {formatDuration(rec.duration)}
                        </span>
                      )}
                      <span>{formatSize(rec.size)}</span>
                      <span>{formatDate(rec.created_at)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => handleDownloadRecording(rec)}
                      aria-label="Download recording"
                    >
                      <DownloadSimple className="size-3.5" />
                    </Button>
                    {isHost && (
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => handleDeleteRecording(rec)}
                        aria-label="Delete recording"
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash className="size-3.5" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Transcripts Section */}
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Transcript</CardTitle>
        </CardHeader>
        <CardContent>
          {transcriptsLoading ? (
            <p className="text-xs text-muted-foreground py-4 text-center">Loading...</p>
          ) : transcripts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="flex size-10 items-center justify-center rounded-full bg-muted mb-3">
                <FileText className="size-5 text-muted-foreground" weight="light" />
              </div>
              <p className="text-sm font-medium text-foreground mb-1">No transcripts yet</p>
              <p className="text-xs text-muted-foreground max-w-xs">
                Transcripts will appear here after they are generated and uploaded from a meeting session.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {transcripts.map((tx) => (
                <div key={tx.id} className="flex items-center gap-3 py-2.5 text-xs">
                  <FileText className="size-4 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">{tx.filename}</p>
                    <div className="flex items-center gap-3 text-muted-foreground mt-0.5">
                      <span>{formatSize(tx.size)}</span>
                      <span>{formatDate(tx.created_at)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => handleDownloadTranscript(tx)}
                      aria-label="Download transcript"
                    >
                      <DownloadSimple className="size-3.5" />
                    </Button>
                    {isHost && (
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => handleDeleteTranscript(tx)}
                        aria-label="Delete transcript"
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash className="size-3.5" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

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
