import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import toast from "react-hot-toast"
import { entityLinksApi } from "../api/entityLinksApi"

export const entityLinkKeys = {
  all: () => ["entity-links"],
  linkedTasks: (meetingId) => [...entityLinkKeys.all(), "linked-tasks", meetingId],
  sessionLinkedTasks: (meetingId, sessionId) => [...entityLinkKeys.all(), "session-linked-tasks", meetingId, sessionId],
  linkedMeetings: (taskId) => [...entityLinkKeys.all(), "linked-meetings", taskId],
  list: (params) => [...entityLinkKeys.all(), "list", params],
}

export function useLinkedTasks(meetingId) {
  return useQuery({
    queryKey: entityLinkKeys.linkedTasks(meetingId),
    queryFn: async () => {
      const { data } = await entityLinksApi.getLinkedTasks(meetingId)
      return Array.isArray(data) ? data : []
    },
    enabled: !!meetingId,
    staleTime: 15_000,
  })
}

export function useSessionLinkedTasks(meetingId, sessionId) {
  return useQuery({
    queryKey: entityLinkKeys.sessionLinkedTasks(meetingId, sessionId),
    queryFn: async () => {
      const { data } = await entityLinksApi.getSessionLinkedTasks(meetingId, sessionId)
      return Array.isArray(data) ? data : []
    },
    enabled: !!(meetingId && sessionId),
    staleTime: 15_000,
  })
}

export function useLinkedMeetings(taskId) {
  return useQuery({
    queryKey: entityLinkKeys.linkedMeetings(taskId),
    queryFn: async () => {
      const { data } = await entityLinksApi.getLinkedMeetings(taskId)
      return Array.isArray(data) ? data : []
    },
    enabled: !!taskId,
    staleTime: 15_000,
  })
}

export function useCreateEntityLink() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload) => entityLinksApi.create(payload),
    onSuccess: (_, variables) => {
      if (variables.source_type === "meeting") {
        qc.invalidateQueries({ queryKey: entityLinkKeys.linkedTasks(variables.source_id) })
      }
      if (variables.target_type === "meeting") {
        qc.invalidateQueries({ queryKey: entityLinkKeys.linkedTasks(variables.target_id) })
      }
      if (variables.source_type === "meeting_session") {
        qc.invalidateQueries({ queryKey: entityLinkKeys.all() })
      }
      if (variables.target_type === "meeting_session") {
        qc.invalidateQueries({ queryKey: entityLinkKeys.all() })
      }
      if (variables.source_type === "task") {
        qc.invalidateQueries({ queryKey: entityLinkKeys.linkedMeetings(variables.source_id) })
      }
      if (variables.target_type === "task") {
        qc.invalidateQueries({ queryKey: entityLinkKeys.linkedMeetings(variables.target_id) })
      }
      toast.success("Link created.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to create link.")
    },
  })
}

export function useDeleteEntityLink() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (linkId) => entityLinksApi.delete(linkId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: entityLinkKeys.all() })
      toast.success("Link removed.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to remove link.")
    },
  })
}
