import { z } from "zod"

export const createMeetingSchema = z.object({
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
})

export const joinMeetingSchema = z.object({
  guest_name: z
    .string()
    .min(1, "Name is required")
    .max(100, "Name must be 100 characters or fewer"),
})
