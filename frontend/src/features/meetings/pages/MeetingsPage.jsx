import { useState } from "react"
import { useMeetings } from "../hooks/useMeetingsApi"
import { MeetingList } from "../components/MeetingList"
import { CreateMeetingDialog } from "../components/CreateMeetingDialog"
import { Button } from "@/components/ui/button"
import { Plus, Video } from "@phosphor-icons/react"

function MeetingsPage() {
  const [createOpen, setCreateOpen] = useState(false)
  const { data: meetings, isLoading } = useMeetings()

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-base font-heading font-semibold text-foreground">
            Meetings
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Manage your audio meetings
          </p>
        </div>
        <Button size="sm" onClick={() => setCreateOpen(true)}>
          <Plus className="size-3.5" />
          New Meeting
        </Button>
      </div>

      <MeetingList meetings={meetings} isLoading={isLoading} />

      <CreateMeetingDialog open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  )
}

export default MeetingsPage
