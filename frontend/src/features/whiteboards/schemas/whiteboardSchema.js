import { z } from "zod"

export const whiteboardSchema = z.object({
    title: z.string().min(1, "Title is required").max(255, "Title too long"),
})

export const createWhiteboardSchema = z.object({
    title: z.string().min(1, "Title is required").max(255, "Title too long"),
})
