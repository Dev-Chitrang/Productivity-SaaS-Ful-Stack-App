import { z } from "zod"

export const noteSchema = z.object({
    title: z.string().max(255, "Title too long").optional(),
    content: z.string().min(1, "Content is required").max(50000, "Content too long"),
    category: z.string().max(100, "Category too long").optional(),
    tags: z.array(z.string()).optional(),
})
