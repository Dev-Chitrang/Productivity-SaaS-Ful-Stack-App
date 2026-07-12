import api from "@/lib/axios"

/**
 * Module-centric attachment endpoints.
 * Never exposes storage paths — all file access goes through backend download URLs.
 * S3 migration requires no changes here: only the backend download endpoint changes.
 */
export const attachmentsApi = {
    // ── Tasks ──────────────────────────────────────────────────────────────────
    uploadForTask: (taskId, file) => {
        const form = new FormData()
        form.append("file", file)
        return api.post(`/tasks/${taskId}/attachments`, form)
    },
    listForTask: (taskId) => api.get(`/tasks/${taskId}/attachments`),
    downloadForTask: (taskId, attachmentId) =>
        api.get(`/tasks/${taskId}/attachments/${attachmentId}/download`, {
            responseType: "blob",
        }),
    deleteForTask: (taskId, attachmentId) =>
        api.delete(`/tasks/${taskId}/attachments/${attachmentId}`),

    // ── Calendar Events ────────────────────────────────────────────────────────
    uploadForCalendarEvent: (eventId, file) => {
        const form = new FormData()
        form.append("file", file)
        return api.post(`/calendar/events/${eventId}/attachments`, form)
    },
    listForCalendarEvent: (eventId) =>
        api.get(`/calendar/events/${eventId}/attachments`),
    downloadForCalendarEvent: (eventId, attachmentId) =>
        api.get(`/calendar/events/${eventId}/attachments/${attachmentId}/download`, {
            responseType: "blob",
        }),
    deleteForCalendarEvent: (eventId, attachmentId) =>
        api.delete(`/calendar/events/${eventId}/attachments/${attachmentId}`),

    // ── Meeting Sessions ───────────────────────────────────────────────────────
    uploadForSession: (meetingId, sessionId, file) => {
        const form = new FormData()
        form.append("file", file)
        return api.post(
            `/meetings/${meetingId}/sessions/${sessionId}/attachments`,
            form,
        )
    },
    listForSession: (meetingId, sessionId) =>
        api.get(`/meetings/${meetingId}/sessions/${sessionId}/attachments`),
    downloadForSession: (meetingId, sessionId, attachmentId) =>
        api.get(
            `/meetings/${meetingId}/sessions/${sessionId}/attachments/${attachmentId}/download`,
            { responseType: "blob" },
        ),
    deleteForSession: (meetingId, sessionId, attachmentId) =>
        api.delete(
            `/meetings/${meetingId}/sessions/${sessionId}/attachments/${attachmentId}`,
        ),
}
