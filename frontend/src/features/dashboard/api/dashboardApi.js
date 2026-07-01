import api from "@/lib/axios"

export const getNotesAnalytics = () => api.get("/notes/analytics")

export const getTasksAnalytics = () => api.get("/tasks/analytics")

export const getCalendarAnalytics = () => api.get("/calendar/analytics")
