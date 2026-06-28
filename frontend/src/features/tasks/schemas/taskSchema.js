import { z } from "zod"

export const taskSchema = z.object({
    title: z.string().min(1, "Title is required").max(255, "Title too long"),
    description: z.any().optional(),
    status: z.enum(["TODO", "IN PROGRESS", "DONE"]).default("TODO"),
    priority: z.enum(["LOW", "MEDIUM", "HIGH"]).default("MEDIUM"),
    due_date: z.string().nullable().optional(),
    labels: z.array(z.string()).default([]),
    checklist: z.array(z.object({
        id: z.string(),
        text: z.string().min(1, "Checklist item cannot be empty"),
        completed: z.boolean().default(false),
    })).default([]),
})
