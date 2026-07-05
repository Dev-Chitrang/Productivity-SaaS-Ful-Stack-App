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
import { CalendarBlank, Clock, Globe, Note, Robot } from "@phosphor-icons/react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const COMMON_TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "America/Anchorage",
  "Pacific/Honolulu",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Europe/Moscow",
  "Asia/Dubai",
  "Asia/Kolkata",
  "Asia/Shanghai",
  "Asia/Tokyo",
  "Asia/Seoul",
  "Australia/Sydney",
  "Pacific/Auckland",
]

export function EditMeetingDialog({ meeting, open, onOpenChange }) {
  const [recording, setRecording] = useState(false)
  const [transcript, setTranscript] = useState(false)
  const [aiAnalysis, setAiAnalysis] = useState(false)
  const updateMeeting = useUpdateMeeting()
  const isScheduled = meeting?.meeting_type === "SCHEDULED"

  const form = useForm({
    resolver: zodResolver(updateMeetingSchema),
    defaultValues: {
      title: "",
      description: "",
      scheduled_date: "",
      scheduled_time: "",
      duration: "",
      timezone: "",
      agenda: "",
      enable_ai_analysis: false,
    },
  })

  useEffect(() => {
    if (meeting) {
      form.reset({
        title: meeting.title || "",
        description: meeting.description || "",
        scheduled_date: meeting.scheduled_date || "",
        scheduled_time: meeting.scheduled_time || "",
        duration: meeting.duration || "",
        timezone: meeting.timezone || "",
        agenda: meeting.agenda || "",
        enable_ai_analysis: meeting.enable_ai_analysis || false,
      })
      setRecording(meeting.enable_recording || false)
      setTranscript(meeting.enable_transcript || false)
      setAiAnalysis(meeting.enable_ai_analysis || false)
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
        enable_ai_analysis: aiAnalysis,
      })
      onOpenChange(false)
    } catch { }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
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

            {isScheduled && (
              <div className="space-y-4 rounded border border-border p-3">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Schedule Details
                </p>

                <div className="grid grid-cols-2 gap-3">
                  <FormField
                    control={form.control}
                    name="scheduled_date"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          <span className="inline-flex items-center gap-1">
                            <CalendarBlank className="size-3" />
                            Date
                          </span>
                        </FormLabel>
                        <FormControl>
                          <Input type="date" aria-label="Scheduled date" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="scheduled_time"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          <span className="inline-flex items-center gap-1">
                            <Clock className="size-3" />
                            Time
                          </span>
                        </FormLabel>
                        <FormControl>
                          <Input type="time" aria-label="Scheduled time" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <FormField
                    control={form.control}
                    name="duration"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          <span className="inline-flex items-center gap-1">
                            <Clock className="size-3" />
                            Duration (min)
                          </span>
                        </FormLabel>
                        <FormControl>
                          <Input type="number" min="1" aria-label="Duration in minutes" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="timezone"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          <span className="inline-flex items-center gap-1">
                            <Globe className="size-3" />
                            Timezone
                          </span>
                        </FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select timezone" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {COMMON_TIMEZONES.map((tz) => (
                              <SelectItem key={tz} value={tz}>{tz}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="agenda"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        <span className="inline-flex items-center gap-1">
                          <Note className="size-3" />
                          Agenda (optional)
                        </span>
                      </FormLabel>
                      <FormControl>
                        <textarea
                          aria-label="Meeting agenda"
                          rows={3}
                          placeholder="Topics to cover..."
                          className="flex w-full rounded border border-border bg-transparent px-3 py-2 text-xs shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 resize-none"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={aiAnalysis}
                    onChange={(e) => {
                      const enabled = e.target.checked
                      setAiAnalysis(enabled)
                      if (enabled) {
                        setTranscript(true)
                      }
                    }}
                    className="size-3.5 accent-primary"
                  />
                  <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                    <Robot className="size-3" />
                    Enable AI Analysis
                  </span>
                </label>
              </div>
            )}

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
                <label className={`flex items-center gap-2 ${aiAnalysis ? "" : "cursor-pointer"}`}>
                  <input
                    type="checkbox"
                    checked={transcript}
                    disabled={aiAnalysis}
                    onChange={(e) => setTranscript(e.target.checked)}
                    className="size-3.5 accent-primary"
                  />
                  <span className={`text-xs ${aiAnalysis ? "text-muted-foreground/50" : "text-muted-foreground"}`}>
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
