import api from "@/lib/axios"

export const getNotesAnalytics = () => api.get("/notes/analytics")

export const getTasksAnalytics = () => api.get("/tasks/analytics")

export const getCalendarAnalytics = () => api.get("/calendar/analytics")

export const getRecentAttachments = (limit = 10) =>
    api.get("/attachments/recent", { params: { limit } })

export const getRecentAnalyses = (limit = 5) =>
    api.get("/meetings/recent-analyses", { params: { limit } })
