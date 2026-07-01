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
import { createMeetingSchema } from "../schemas/meetingSchema"
import { useCreateMeeting } from "../hooks/useMeetingsApi"
import { useState } from "react"

export function CreateMeetingDialog({ open, onOpenChange }) {
  const [recording, setRecording] = useState(false)
  const [transcript, setTranscript] = useState(false)
  const createMeeting = useCreateMeeting()

  const form = useForm({
    resolver: zodResolver(createMeetingSchema),
    defaultValues: {
      title: "",
      description: "",
      enable_recording: false,
      enable_transcript: false,
    },
  })

  const onSubmit = async (values) => {
    try {
      await createMeeting.mutateAsync(values)
      form.reset()
      onOpenChange(false)
    } catch {}
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create Meeting</DialogTitle>
          <DialogDescription>
            Set up a new audio meeting room.
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
                    <Input
                      placeholder="Weekly sync"
                      aria-label="Meeting title"
                      {...field}
                    />
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
                    <Input
                      placeholder="Brief description..."
                      aria-label="Meeting description"
                      {...field}
                    />
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
                    onChange={(e) => {
                      setRecording(e.target.checked)
                      form.setValue("enable_recording", e.target.checked)
                    }}
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
                    onChange={(e) => {
                      setTranscript(e.target.checked)
                      form.setValue("enable_transcript", e.target.checked)
                    }}
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
                disabled={createMeeting.isPending}
              >
                {createMeeting.isPending ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
