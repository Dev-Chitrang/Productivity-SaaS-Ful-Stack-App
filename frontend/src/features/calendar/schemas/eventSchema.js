/**
 * eventSchema.js
 *
 * Zod validation schema for the Create / Edit Event form.
 *
 * Field names here represent the FORM state — they are converted to the
 * backend DTO by calendarMapper.toCreatePayload() / toUpdatePayload().
 *
 * Enum arrays use uppercase backend values (MEETING, BLUE, WEEKLY) so that
 * the mapper can forward them to the API without any transformation gap.
 */

import { z } from "zod"
import dayjs from "dayjs"
import customParseFormat from "dayjs/plugin/customParseFormat"
import isSameOrBefore from "dayjs/plugin/isSameOrBefore"
import {
    EVENT_TYPE_OPTIONS,
    EVENT_COLOR_OPTIONS,
    RECURRENCE_FREQUENCY_OPTIONS,
} from "../api/calendarTypes"

dayjs.extend(customParseFormat)
dayjs.extend(isSameOrBefore)

// Re-export for components that need to iterate over options
export { EVENT_TYPE_OPTIONS, EVENT_COLOR_OPTIONS, RECURRENCE_FREQUENCY_OPTIONS }

export const eventSchema = z
    .object({
        title: z
            .string()
            .min(1, "Title is required")
            .max(255, "Title must be 255 characters or fewer"),

        description: z
            .string()
            .max(2000, "Description too long")
            .optional()
            .or(z.literal("")),

        /** Matches backend EventType enum — uppercase */
        event_type: z.enum(
      /** @type {[string, ...string[]]} */(EVENT_TYPE_OPTIONS),
            { errorMap: () => ({ message: "Select a valid event type" }) },
        ),

        start_date: z.string().min(1, "Start date is required"),

        /** Internal HH:mm — never sent to backend directly */
        start_hhmm: z.string().min(1, "Start time is required"),

        end_date: z.string().min(1, "End date is required"),

        /** Internal HH:mm — never sent to backend directly */
        end_hhmm: z.string().min(1, "End time is required"),

        timezone: z.string().min(1, "Timezone is required"),

        is_all_day: z.boolean().default(false),

        location: z.string().max(500, "Location too long").optional().or(z.literal("")),

        /** Matches backend EventColor enum — uppercase */
        color: z.enum(
      /** @type {[string, ...string[]]} */(EVENT_COLOR_OPTIONS),
            { errorMap: () => ({ message: "Select a color" }) },
        ),

        is_recurring: z.boolean().default(false),

        /** Matches backend RecurrenceFrequency enum — uppercase */
        recurrence_frequency: z
            .enum(/** @type {[string, ...string[]]} */(RECURRENCE_FREQUENCY_OPTIONS))
            .optional(),

        recurrence_interval: z.coerce
            .number()
            .int()
            .min(1, "Interval must be at least 1")
            .max(99, "Interval too large")
            .optional(),

        /** YYYY-MM-DD date string — mapper converts to full ISO datetime */
        recurrence_end_date: z.string().optional().or(z.literal("")),
    })
    .superRefine((data, ctx) => {

        if (data.is_recurring && !data.recurrence_frequency) {
            ctx.addIssue({
                path: ["recurrence_frequency"],
                code: z.ZodIssueCode.custom,
                message: "Frequency is required for recurring events",
            })
        }

        if (
            data.is_recurring &&
            data.recurrence_end_date &&
            data.recurrence_end_date < data.start_date
        ) {
            ctx.addIssue({
                path: ["recurrence_end_date"],
                code: z.ZodIssueCode.custom,
                message: "Recurrence end date must be on or after the start date",
            })
        }

        // Start time must be before end time
        const startDT = dayjs(`${data.start_date}T${data.start_hhmm}`, "YYYY-MM-DDTHH:mm")
        const endDT = dayjs(`${data.end_date}T${data.end_hhmm}`, "YYYY-MM-DDTHH:mm")
        if (startDT.isValid() && endDT.isValid()) {
            if (endDT.isSameOrBefore(startDT)) {
                ctx.addIssue({
                    path: ["end_hhmm"],
                    code: z.ZodIssueCode.custom,
                    message: "End time must be after start time",
                })
            }
        }
    })
