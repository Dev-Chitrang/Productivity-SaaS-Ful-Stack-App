import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import toast from "react-hot-toast"
import { attachmentsApi } from "../api/attachmentsApi"

// ─── Query key factory ────────────────────────────────────────────────────────

export const attachmentKeys = {
    forTask: (taskId) => ["attachments", "task", taskId],
    forCalendarEvent: (eventId) => ["attachments", "calendar_event", eventId],
    forSession: (meetingId, sessionId) => ["attachments", "meeting_session", meetingId, sessionId],
}

// ─── Validation mirrors (frontend pre-flight) ─────────────────────────────────
// Mirror backend constants — only for UX; backend always re-validates.

const MAX_SIZE_BYTES = 50 * 1024 * 1024 // 50 MB

const ALLOWED_EXTENSIONS = new Set([
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "rtf", "csv", "odt",
    "jpg", "jpeg", "png", "gif", "webp", "svg", "bmp", "tiff",
    "mp3", "wav", "ogg", "m4a", "webm",
    "mp4", "mov", "avi", "mkv",
    "zip", "tar", "gz", "7z",
    "json", "xml", "md", "yaml", "yml",
])

/**
 * Validate a File object before upload.
 * Returns null if valid, or an error string if invalid.
 */
export function validateFile(file) {
    if (!file || file.size === 0) return "File is empty."
    if (file.size > MAX_SIZE_BYTES) return `File exceeds the 50 MB limit.`
    const ext = file.name.split(".").pop()?.toLowerCase() ?? ""
    if (!ext || !ALLOWED_EXTENSIONS.has(ext)) {
        return `File type ".${ext}" is not supported.`
    }
    return null
}

// ─── Task attachment hooks ────────────────────────────────────────────────────

export function useTaskAttachments(taskId) {
    return useQuery({
        queryKey: attachmentKeys.forTask(taskId),
        queryFn: async () => {
            const { data } = await attachmentsApi.listForTask(taskId)
            return Array.isArray(data?.attachments) ? data.attachments : []
        },
        enabled: !!taskId,
        staleTime: 15_000,
    })
}

export function useUploadTaskAttachment(taskId) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (file) => attachmentsApi.uploadForTask(taskId, file),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: attachmentKeys.forTask(taskId) })
            toast.success("Attachment uploaded.")
        },
        onError: (err) => {
            const detail = err?.response?.data?.detail
            toast.error(detail || "Failed to upload attachment.")
        },
    })
}

export function useDeleteTaskAttachment(taskId) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (attachmentId) =>
            attachmentsApi.deleteForTask(taskId, attachmentId),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: attachmentKeys.forTask(taskId) })
            toast.success("Attachment deleted.")
        },
        onError: (err) => {
            const detail = err?.response?.data?.detail
            toast.error(detail || "Failed to delete attachment.")
        },
    })
}

// ─── Calendar event attachment hooks ─────────────────────────────────────────

export function useCalendarEventAttachments(eventId) {
    return useQuery({
        queryKey: attachmentKeys.forCalendarEvent(eventId),
        queryFn: async () => {
            const { data } = await attachmentsApi.listForCalendarEvent(eventId)
            return Array.isArray(data?.attachments) ? data.attachments : []
        },
        enabled: !!eventId,
        staleTime: 15_000,
    })
}

export function useUploadCalendarEventAttachment(eventId) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (file) => attachmentsApi.uploadForCalendarEvent(eventId, file),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: attachmentKeys.forCalendarEvent(eventId) })
            toast.success("Attachment uploaded.")
        },
        onError: (err) => {
            const detail = err?.response?.data?.detail
            toast.error(detail || "Failed to upload attachment.")
        },
    })
}

export function useDeleteCalendarEventAttachment(eventId) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (attachmentId) =>
            attachmentsApi.deleteForCalendarEvent(eventId, attachmentId),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: attachmentKeys.forCalendarEvent(eventId) })
            toast.success("Attachment deleted.")
        },
        onError: (err) => {
            const detail = err?.response?.data?.detail
            toast.error(detail || "Failed to delete attachment.")
        },
    })
}

// ─── Meeting session attachment hooks ────────────────────────────────────────

export function useSessionAttachments(meetingId, sessionId) {
    return useQuery({
        queryKey: attachmentKeys.forSession(meetingId, sessionId),
        queryFn: async () => {
            const { data } = await attachmentsApi.listForSession(meetingId, sessionId)
            return Array.isArray(data?.attachments) ? data.attachments : []
        },
        enabled: !!(meetingId && sessionId),
        staleTime: 15_000,
    })
}

export function useUploadSessionAttachment(meetingId, sessionId) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (file) =>
            attachmentsApi.uploadForSession(meetingId, sessionId, file),
        onSuccess: () => {
            qc.invalidateQueries({
                queryKey: attachmentKeys.forSession(meetingId, sessionId),
            })
            toast.success("Attachment uploaded.")
        },
        onError: (err) => {
            const detail = err?.response?.data?.detail
            toast.error(detail || "Failed to upload attachment.")
        },
    })
}

export function useDeleteSessionAttachment(meetingId, sessionId) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (attachmentId) =>
            attachmentsApi.deleteForSession(meetingId, sessionId, attachmentId),
        onSuccess: () => {
            qc.invalidateQueries({
                queryKey: attachmentKeys.forSession(meetingId, sessionId),
            })
            toast.success("Attachment deleted.")
        },
        onError: (err) => {
            const detail = err?.response?.data?.detail
            toast.error(detail || "Failed to delete attachment.")
        },
    })
}
