import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useLinkedMeetings, useCreateEntityLink, useDeleteEntityLink } from "@/features/entityLinks/hooks/useEntityLinksApi"
import { useMeetings } from "@/features/meetings/hooks/useMeetingsApi"
import { Video, Link, LinkSimpleBreak, Plus, MagnifyingGlass, ArrowUpRight, CalendarBlank } from "@phosphor-icons/react"
import toast from "react-hot-toast"

function MeetingStatusBadge({ status }) {
  const classes = {
    CREATED: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800",
    ACTIVE: "bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-800",
    IDLE: "bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-300 dark:border-yellow-800",
    ENDED: "bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-950 dark:text-gray-300 dark:border-gray-800",
    CANCELLED: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800",
  }
  const cls = classes[status] || classes.ENDED
  return (
    <span className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-medium ${cls}`}>
      {status?.charAt(0) + status?.slice(1).toLowerCase()}
    </span>
  )
}

export function LinkedMeetingsPanel({ taskId }) {
  const navigate = useNavigate()
  const { data: linkedMeetings = [], isLoading } = useLinkedMeetings(taskId)
  const { data: allMeetings = [] } = useMeetings()
  const createLink = useCreateEntityLink()
  const deleteLink = useDeleteEntityLink()

  const [linkDialogOpen, setLinkDialogOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedMeetingId, setSelectedMeetingId] = useState(null)

  const linkedIds = new Set(linkedMeetings.map((m) => m.id))
  const filteredMeetings = allMeetings.filter((m) => !linkedIds.has(m.id))

  const availableMeetings = searchQuery
    ? filteredMeetings.filter((m) => m.title?.toLowerCase().includes(searchQuery.toLowerCase()))
    : filteredMeetings

  const handleLinkMeeting = async () => {
    if (!selectedMeetingId) {
      toast.error("Select a session to link.")
      return
    }
    try {
      await createLink.mutateAsync({
        source_type: "task",
        source_id: taskId,
        target_type: "meeting",
        target_id: selectedMeetingId,
      })
      setLinkDialogOpen(false)
      setSelectedMeetingId(null)
      setSearchQuery("")
    } catch {
      // error handled by hook
    }
  }

  const handleRemoveLink = async (meetingId) => {
    const link = linkedMeetings.find((m) => m.id === meetingId)
    if (!link) {
      toast.error("Link not found.")
      return
    }
    try {
      await deleteLink.mutateAsync(link.link_id)
    } catch {
      // error handled by hook
    }
  }

  const handleOpenMeeting = (meeting) => {
    if (meeting.session_id) {
      navigate(`/meetings/${meeting.id}/sessions/${meeting.session_id}`)
    } else {
      navigate(`/meetings/${meeting.id}`)
    }
  }

  return (
    <div className="border-t border-border px-4 py-3">
      <div className="flex items-center justify-between mb-3">
        <p className="text-[11px] font-medium text-muted-foreground flex items-center gap-1.5">
          <Video className="size-3.5" weight="light" />
          Related Sessions
          {linkedMeetings.length > 0 && (
            <span className="text-muted-foreground">({linkedMeetings.length})</span>
          )}
        </p>
        <Button variant="outline" size="sm" onClick={() => setLinkDialogOpen(true)}>
          <Link className="size-3.5" />
          Link Session
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          <div className="h-8 animate-pulse rounded bg-muted" />
          <div className="h-8 animate-pulse rounded bg-muted" />
        </div>
      ) : linkedMeetings.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-6 text-center">
          <Video className="size-8 text-muted-foreground/40 mb-2" weight="light" />
          <p className="text-xs text-muted-foreground">No linked sessions</p>
          <Button variant="ghost" size="sm" className="mt-2" onClick={() => setLinkDialogOpen(true)}>
            <Plus className="size-3.5" />
            Link a session
          </Button>
        </div>
      ) : (
        <div className="space-y-2">
          {linkedMeetings.map((meeting) => (
            <div
              key={meeting.id}
              role="button"
              tabIndex={0}
              onClick={() => handleOpenMeeting(meeting)}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); handleOpenMeeting(meeting) } }}
              className="flex items-center justify-between gap-2 rounded border border-border p-2.5 cursor-pointer hover:bg-muted/50 transition-colors"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="truncate text-xs font-medium text-foreground">
                    {meeting.title}
                  </span>
                  <ArrowUpRight className="size-3 shrink-0 text-muted-foreground" weight="bold" />
                </div>
                <div className="flex items-center gap-1.5 flex-wrap">
                  <MeetingStatusBadge status={meeting.status} />
                  <span className="text-[10px] font-mono text-muted-foreground">{meeting.meeting_code}</span>
                  {meeting.scheduled_start && (
                    <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                      <CalendarBlank className="size-2.5" />
                      {new Date(meeting.scheduled_start).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); handleRemoveLink(meeting.id) }}
                  className="shrink-0 p-1 text-muted-foreground hover:text-destructive transition-colors"
                  title="Remove link"
                  aria-label={`Remove link to ${meeting.title}`}
                >
                  <LinkSimpleBreak className="size-3.5" />
                </button>
            </div>
          ))}
        </div>
      )}

      <Dialog open={linkDialogOpen} onOpenChange={(v) => { if (!v) { setLinkDialogOpen(false); setSelectedMeetingId(null); setSearchQuery("") } }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-sm">Link a Session</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="relative">
              <MagnifyingGlass className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search meetings..."
                className="pl-8 text-xs h-8"
              />
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1">
              {availableMeetings.length === 0 ? (
                <p className="text-xs text-muted-foreground text-center py-4">
                  {searchQuery ? "No meetings match your search." : "No meetings available to link."}
                </p>
              ) : (
                availableMeetings.map((meeting) => (
                  <button
                    key={meeting.id}
                    type="button"
                    onClick={() => setSelectedMeetingId(meeting.id)}
                    className={`w-full text-left px-3 py-2 rounded text-xs border transition-colors ${
                      selectedMeetingId === meeting.id
                        ? "border-primary bg-primary/5 text-foreground"
                        : "border-border text-muted-foreground hover:bg-muted hover:text-foreground"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate font-medium">{meeting.title}</span>
                      <MeetingStatusBadge status={meeting.status} />
                    </div>
                    <span className="text-[10px] font-mono text-muted-foreground mt-0.5 block">
                      {meeting.meeting_code}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" size="sm" onClick={() => { setLinkDialogOpen(false); setSelectedMeetingId(null); setSearchQuery("") }}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleLinkMeeting} disabled={!selectedMeetingId || createLink.isPending}>
              {createLink.isPending ? "Linking..." : "Link Session"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
