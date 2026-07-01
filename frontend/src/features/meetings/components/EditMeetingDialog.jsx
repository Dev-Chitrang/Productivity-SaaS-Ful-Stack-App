import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { updateMeetingSchema } from "../schemas/meetingSchema"
import { useUpdateMeeting } from "../hooks/useMeetingsApi"

export function EditMeetingDialog({ meeting, open, onOpenChange }) {
  const [recording, setRecording] = useState(false)
  const [transcript, setTranscript] = useState(false)
  const updateMeeting = useUpdateMeeting()

  const form = useForm({
    resolver: zodResolver(updateMeetingSchema),
    defaultValues: {
      title: "",
      description: "",
    },
  })

  useEffect(() => {
    if (meeting) {
      form.reset({
        title: meeting.title || "",
        description: meeting.description || "",
      })
      setRecording(meeting.enable_recording || false)
      setTranscript(meeting.enable_transcript || false)
    }
  }, [meeting, form])

  const onSubmit = async (values) => {
    if (!meeting) return
    try {
      await updateMeeting.mutateAsync({
        id: meeting.id,
        ...values,
        enable_recording: recording,
        enable_transcript: transcript,
      })
      onOpenChange(false)
    } catch {}
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Meeting</DialogTitle>
          <DialogDescription>
            Update meeting details.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title</FormLabel>
                  <FormControl>
                    <Input aria-label="Meeting title" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description (optional)</FormLabel>
                  <FormControl>
                    <Input aria-label="Meeting description" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="space-y-3">
              <FormLabel>Meeting Settings</FormLabel>
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={recording}
                    onChange={(e) => setRecording(e.target.checked)}
                    className="size-3.5 accent-primary"
                  />
                  <span className="text-xs text-muted-foreground">
                    Enable Recording
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={transcript}
                    onChange={(e) => setTranscript(e.target.checked)}
                    className="size-3.5 accent-primary"
                  />
                  <span className="text-xs text-muted-foreground">
                    Enable Transcript
                  </span>
                </label>
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={updateMeeting.isPending}
              >
                {updateMeeting.isPending ? "Saving..." : "Save"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
