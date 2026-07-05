import { z } from "zod"

export const participantSchema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z
    .string()
    .min(1, "Email is required")
    .email("Invalid email format"),
})

export const createMeetingSchema = z.object({
  meeting_type: z.enum(["INSTANT", "SCHEDULED"]).default("INSTANT"),
  title: z
    .string()
    .min(1, "Title is required")
    .max(255, "Title must be 255 characters or fewer"),
  description: z
    .string()
    .max(2000, "Description too long")
    .optional()
    .or(z.literal("")),
  enable_recording: z.boolean().default(false),
  enable_transcript: z.boolean().default(false),
  scheduled_date: z.string().optional(),
  scheduled_time: z.string().optional(),
  duration: z.coerce.number().optional(),
  timezone: z.string().optional(),
  agenda: z
    .string()
    .max(5000, "Agenda too long")
    .optional()
    .or(z.literal("")),
  enable_ai_analysis: z.boolean().default(false),
  participants: z.array(participantSchema).optional(),
}).superRefine((data, ctx) => {
  if (data.enable_ai_analysis && (!data.agenda || !data.agenda.trim())) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["agenda"],
      message: "Agenda is required when AI Analysis is enabled",
    })
  }
  if (data.meeting_type === "SCHEDULED") {
    if (!data.scheduled_date) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["scheduled_date"],
        message: "Date is required",
      })
    }
    if (!data.scheduled_time) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["scheduled_time"],
        message: "Time is required",
      })
    }
    if (!data.duration || data.duration < 1) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["duration"],
        message: "Duration must be at least 1 minute",
      })
    }
    if (!data.timezone) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["timezone"],
        message: "Timezone is required",
      })
    }
    if (!data.participants || data.participants.length === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["participants"],
        message: "At least one participant is required",
      })
    }
  }
})

export const updateMeetingSchema = z.object({
  title: z
    .string()
    .min(1, "Title is required")
    .max(255, "Title must be 255 characters or fewer")
    .optional(),
  description: z
    .string()
    .max(2000, "Description too long")
    .optional()
    .or(z.literal("")),
  enable_recording: z.boolean().optional(),
  enable_transcript: z.boolean().optional(),
  scheduled_date: z.string().optional(),
  scheduled_time: z.string().optional(),
  duration: z.coerce.number().optional(),
  timezone: z.string().optional(),
  agenda: z
    .string()
    .max(5000, "Agenda too long")
    .optional()
    .or(z.literal("")),
  enable_ai_analysis: z.boolean().optional(),
}).superRefine((data, ctx) => {
  if (data.enable_ai_analysis && (!data.agenda || !data.agenda.trim())) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      path: ["agenda"],
      message: "Agenda is required when AI Analysis is enabled",
    })
  }
})

export const joinMeetingSchema = z.object({
  guest_name: z
    .string()
    .min(1, "Name is required")
    .max(100, "Name must be 100 characters or fewer"),
})
