import { useForm, useFieldArray } from "react-hook-form"
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
import { useCreateMeeting, useCreateScheduledMeeting } from "../hooks/useMeetingsApi"
import { useState } from "react"
import dayjs from "dayjs"
import utc from "dayjs/plugin/utc"
import timezone from "dayjs/plugin/timezone"
import toast from "react-hot-toast"

dayjs.extend(utc)
dayjs.extend(timezone)
import { Plus, Trash, CalendarBlank, Clock, Globe, Note, Robot } from "@phosphor-icons/react"
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

function mapBackendFieldToFrontend(path) {
  if (!path) return null
  if (path === "title") return "title"
  if (path === "timezone") return "timezone"
  if (path.startsWith("invitations.")) {
    return path.replace("invitations.", "participants.")
  }
  return null
}

function handleApiError(err, form) {
  const data = err?.response?.data
  if (!data) {
    toast.error("An unexpected error occurred.")
    return
  }

  const detail = data.detail
  if (Array.isArray(detail)) {
    let hasFieldErrors = false
    for (const error of detail) {
      const loc = error.loc || []
      const fieldPath = loc.slice(1).join(".")
      const mapped = mapBackendFieldToFrontend(fieldPath)
      if (mapped) {
        form.setError(mapped, { message: error.msg })
        hasFieldErrors = true
      }
    }
    if (hasFieldErrors) {
      toast.error("Please fix the highlighted fields.")
    } else {
      const msgs = detail.map((d) => d.msg).filter(Boolean).join(". ")
      toast.error(msgs || "Validation failed.")
    }
  } else if (typeof detail === "string") {
    toast.error(detail)
  } else {
    toast.error("Failed to create scheduled meeting.")
  }
}

const defaultTimezone = (() => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone
  } catch {
    return "UTC"
  }
})()

export function CreateMeetingDialog({ open, onOpenChange }) {
  const [meetingType, setMeetingType] = useState("INSTANT")
  const [recording, setRecording] = useState(false)
  const [transcript, setTranscript] = useState(false)
  const [aiAnalysis, setAiAnalysis] = useState(false)
  const createMeeting = useCreateMeeting()
  const createScheduledMeeting = useCreateScheduledMeeting()

  const form = useForm({
    resolver: zodResolver(createMeetingSchema),
    defaultValues: {
      meeting_type: "INSTANT",
      title: "",
      description: "",
      enable_recording: false,
      enable_transcript: false,
      scheduled_date: "",
      scheduled_time: "",
      duration: 30,
      timezone: defaultTimezone,
      agenda: "",
      enable_ai_analysis: false,
      participants: [],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "participants",
  })

  const switchMeetingType = (type) => {
    setMeetingType(type)
    form.setValue("meeting_type", type)
    if (type === "SCHEDULED" && fields.length === 0) {
      append({ name: "", email: "" })
    }
  }

  const onSubmit = async (values) => {
    try {
      if (values.meeting_type === "INSTANT") {
        const payload = { title: values.title, description: values.description, enable_recording: values.enable_recording, enable_transcript: values.enable_transcript, enable_ai_analysis: values.enable_ai_analysis, agenda: values.agenda || null }
        await createMeeting.mutateAsync(payload)
      } else {
        const scheduledStart = dayjs.tz(
          `${values.scheduled_date}T${values.scheduled_time}`,
          values.timezone
        ).utc().toISOString()

        const payload = {
          title: values.title,
          description: values.description || null,
          enable_recording: values.enable_recording,
          enable_transcript: values.enable_transcript,
          enable_ai_analysis: values.enable_ai_analysis,
          agenda: values.agenda || null,
          scheduled_start: scheduledStart,
          timezone: values.timezone,
          invitations: (values.participants || []).map((p) => ({ name: p.name, email: p.email })),
        }
        await createScheduledMeeting.mutateAsync(payload)
      }
      form.reset()
      setMeetingType("INSTANT")
      setRecording(false)
      setTranscript(false)
      setAiAnalysis(false)
      onOpenChange(false)
    } catch (err) {
      handleApiError(err, form)
    }
  }

  const handleCancel = () => {
    form.reset()
    setMeetingType("INSTANT")
    setRecording(false)
    setTranscript(false)
    setAiAnalysis(false)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Meeting</DialogTitle>
          <DialogDescription>
            Set up a new audio meeting room.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <FormLabel>Meeting Type</FormLabel>
              <div className="mt-1.5 flex gap-3">
                <label
                  className={`flex flex-1 cursor-pointer items-center justify-center gap-2 rounded border px-3 py-2 text-xs font-medium transition-colors ${meetingType === "INSTANT"
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border text-muted-foreground hover:bg-accent"
                    }`}
                >
                  <input
                    type="radio"
                    name="meeting_type"
                    value="INSTANT"
                    checked={meetingType === "INSTANT"}
                    onChange={() => switchMeetingType("INSTANT")}
                    className="sr-only"
                  />
                  Instant
                </label>
                <label
                  className={`flex flex-1 cursor-pointer items-center justify-center gap-2 rounded border px-3 py-2 text-xs font-medium transition-colors ${meetingType === "SCHEDULED"
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border text-muted-foreground hover:bg-accent"
                    }`}
                >
                  <input
                    type="radio"
                    name="meeting_type"
                    value="SCHEDULED"
                    checked={meetingType === "SCHEDULED"}
                    onChange={() => switchMeetingType("SCHEDULED")}
                    className="sr-only"
                  />
                  Scheduled
                </label>
              </div>
            </div>

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

            {/* Agenda — shown for both meeting types when AI is available */}
            <FormField
              control={form.control}
              name="agenda"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    <span className="inline-flex items-center gap-1">
                      <Note className="size-3" />
                      Agenda{aiAnalysis ? " *" : " (optional)"}
                    </span>
                  </FormLabel>
                  <FormControl>
                    <textarea
                      aria-label="Meeting agenda"
                      rows={3}
                      placeholder={aiAnalysis ? "Agenda is required for AI analysis..." : "Topics to cover..."}
                      className="flex w-full rounded border border-border bg-transparent px-3 py-2 text-xs shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 resize-none"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* AI Analysis toggle — shown for both meeting types */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={aiAnalysis}
                onChange={(e) => {
                  const enabled = e.target.checked
                  setAiAnalysis(enabled)
                  form.setValue("enable_ai_analysis", enabled)
                  if (enabled) {
                    setTranscript(true)
                    form.setValue("enable_transcript", true)
                  }
                }}
                className="size-3.5 accent-primary"
              />
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                <Robot className="size-3" />
                Enable AI Analysis
              </span>
            </label>

            {meetingType === "SCHEDULED" && (
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
                          <Input
                            type="number"
                            min="1"
                            aria-label="Duration in minutes"
                            {...field}
                          />
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
                              <SelectItem key={tz} value={tz}>
                                {tz}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <FormLabel>
                      <span className="inline-flex items-center gap-1">
                        Participants
                      </span>
                    </FormLabel>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => append({ name: "", email: "" })}
                      aria-label="Add participant"
                    >
                      <Plus className="size-3" />
                      Add
                    </Button>
                  </div>
                  {fields.length === 0 && (
                    <p className="text-xs text-muted-foreground">
                      No participants added. Add at least one.
                    </p>
                  )}
                  <div className="space-y-2">
                    {fields.map((field, index) => (
                      <div
                        key={field.id}
                        className="flex items-start gap-2 rounded border border-border p-2"
                      >
                        <div className="flex-1 space-y-2">
                          <FormField
                            control={form.control}
                            name={`participants.${index}.name`}
                            render={({ field }) => (
                              <FormItem>
                                <FormControl>
                                  <Input
                                    placeholder="Name"
                                    aria-label={`Participant ${index + 1} name`}
                                    {...field}
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <FormField
                            control={form.control}
                            name={`participants.${index}.email`}
                            render={({ field }) => (
                              <FormItem>
                                <FormControl>
                                  <Input
                                    placeholder="Email"
                                    aria-label={`Participant ${index + 1} email`}
                                    {...field}
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-xs"
                          onClick={() => remove(index)}
                          aria-label={`Remove participant ${index + 1}`}
                          className="mt-1 text-destructive hover:text-destructive shrink-0"
                        >
                          <Trash className="size-3.5" />
                        </Button>
                      </div>
                    ))}
                  </div>
                  {form.formState.errors.participants && (
                    <p className="text-[10px] font-medium text-destructive">
                      {form.formState.errors.participants.message || form.formState.errors.participants.root?.message}
                    </p>
                  )}
                </div>
              </div>
            )}

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
                <label className={`flex items-center gap-2 ${aiAnalysis ? "" : "cursor-pointer"}`}>
                  <input
                    type="checkbox"
                    checked={transcript}
                    disabled={aiAnalysis}
                    onChange={(e) => {
                      setTranscript(e.target.checked)
                      form.setValue("enable_transcript", e.target.checked)
                    }}
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
                onClick={handleCancel}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createMeeting.isPending || createScheduledMeeting.isPending}
              >
                {(createMeeting.isPending || createScheduledMeeting.isPending) ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
