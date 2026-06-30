import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { useDeleteMeeting } from "../hooks/useMeetingsApi"

export function DeleteMeetingDialog({ meeting, open, onOpenChange }) {
  const deleteMeeting = useDeleteMeeting()

  const handleDelete = async (e) => {
    e?.stopPropagation()
    if (!meeting) return
    try {
      await deleteMeeting.mutateAsync(meeting.id)
      onOpenChange(false)
    } catch {}
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete Meeting</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete{" "}
            <span className="font-medium text-foreground">
              {meeting?.title}
            </span>
            ? This action removes the meeting from future use. This cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={(e) => { e.stopPropagation(); onOpenChange(false) }}
          >
            Keep Meeting
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={handleDelete}
            disabled={deleteMeeting.isPending}
          >
            {deleteMeeting.isPending ? "Deleting..." : "Delete Meeting"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
