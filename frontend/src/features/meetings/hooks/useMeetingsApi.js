import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { meetingsApi } from "../api/meetingsApi"
import toast from "react-hot-toast"

export const meetingKeys = {
  all: () => ["meetings"],
  lists: () => [...meetingKeys.all(), "list"],
  list: (filters) => [...meetingKeys.lists(), filters],
  details: () => [...meetingKeys.all(), "detail"],
  detail: (id) => [...meetingKeys.details(), id],
  byCode: (code) => [...meetingKeys.all(), "by-code", code],
  participants: (id) => [...meetingKeys.all(), "participants", id],
}

export function useMeetings() {
  return useQuery({
    queryKey: meetingKeys.lists(),
    queryFn: async () => {
      const { data } = await meetingsApi.list()
      return Array.isArray(data) ? data : []
    },
    staleTime: 30_000,
  })
}

export function useMeeting(id) {
  return useQuery({
    queryKey: meetingKeys.detail(id),
    queryFn: async () => {
      const { data } = await meetingsApi.get(id)
      return data
    },
    enabled: !!id,
    staleTime: 15_000,
  })
}

export function useMeetingByCode(code) {
  return useQuery({
    queryKey: meetingKeys.byCode(code),
    queryFn: async () => {
      const { data } = await meetingsApi.getByCode(code)
      return data
    },
    enabled: !!code,
    retry: false,
    staleTime: 30_000,
  })
}

export function useCreateMeeting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload) => meetingsApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: meetingKeys.lists() })
      toast.success("Meeting created.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to create meeting.")
    },
  })
}

export function useCreateScheduledMeeting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload) => meetingsApi.createScheduled(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: meetingKeys.lists() })
      toast.success("Scheduled meeting created. Invitations sent.")
    },
  })
}

export function useUpdateMeeting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...payload }) => meetingsApi.update(id, payload),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: meetingKeys.detail(variables.id) })
      qc.invalidateQueries({ queryKey: meetingKeys.lists() })
      toast.success("Meeting updated.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to update meeting.")
    },
  })
}

export function useEndMeeting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id) => meetingsApi.end(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: meetingKeys.detail(id) })
      qc.invalidateQueries({ queryKey: meetingKeys.lists() })
      toast.success("Meeting ended.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to end meeting.")
    },
  })
}

export function useDeleteMeeting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id) => meetingsApi.delete(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: meetingKeys.detail(id) })
      qc.invalidateQueries({ queryKey: meetingKeys.lists() })
      toast.success("Meeting deleted.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to delete meeting.")
    },
  })
}

export function useCancelMeeting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id) => meetingsApi.cancel(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: meetingKeys.detail(id) })
      qc.invalidateQueries({ queryKey: meetingKeys.lists() })
      toast.success("Meeting cancelled.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to cancel meeting.")
    },
  })
}

export function useJoinMeeting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...payload }) => meetingsApi.join(id, payload),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: meetingKeys.participants(variables.id) })
      toast.success("Joined meeting.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to join meeting.")
    },
  })
}

export function useMeetingParticipants(id) {
  return useQuery({
    queryKey: meetingKeys.participants(id),
    queryFn: async () => {
      const { data } = await meetingsApi.participants(id)
      return Array.isArray(data) ? data : []
    },
    enabled: !!id,
    staleTime: 10_000,
  })
}

export function useLeaveMeeting() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...payload }) => meetingsApi.leave(id, payload),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: meetingKeys.participants(variables.id) })
      qc.invalidateQueries({ queryKey: meetingKeys.detail(variables.id) })
      toast.success("Left meeting.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to leave meeting.")
    },
  })
}

export function useWaitingCount(id) {
  return useQuery({
    queryKey: [...meetingKeys.all(), "waiting-count", id],
    queryFn: async () => {
      const { data } = await meetingsApi.waitingCount(id)
      return data.waiting_count ?? 0
    },
    enabled: !!id,
    staleTime: 10_000,
  })
}

// --- Recording & Transcript hooks ---

export const artifactKeys = {
  recordings: (meetingId) => ["meetings", meetingId, "recordings"],
  transcripts: (meetingId) => ["meetings", meetingId, "transcripts"],
}

export function useAdmitParticipant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ meetingId, participantId }) =>
      meetingsApi.admitParticipant(meetingId, participantId),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: meetingKeys.participants(variables.meetingId) })
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to admit participant.")
    },
  })
}

export function useRejectParticipant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ meetingId, participantId }) =>
      meetingsApi.rejectParticipant(meetingId, participantId),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: meetingKeys.participants(variables.meetingId) })
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to reject participant.")
    },
  })
}

export function useRemoveParticipant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ meetingId, participantId }) =>
      meetingsApi.removeParticipant(meetingId, participantId),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: meetingKeys.participants(variables.meetingId) })
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to remove participant.")
    },
  })
}

export function useMuteParticipant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ meetingId, participantId }) =>
      meetingsApi.muteParticipant(meetingId, participantId),
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to mute participant.")
    },
  })
}

export function useUnmuteParticipant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ meetingId, participantId }) =>
      meetingsApi.unmuteParticipant(meetingId, participantId),
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to unmute participant.")
    },
  })
}

export function useRecordings(meetingId) {
  return useQuery({
    queryKey: artifactKeys.recordings(meetingId),
    queryFn: async () => {
      const { data } = await meetingsApi.listRecordings(meetingId)
      return Array.isArray(data) ? data : []
    },
    enabled: !!meetingId,
    staleTime: 10_000,
  })
}

export function useUploadRecording() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ meetingId, file, duration }) =>
      meetingsApi.uploadRecording(meetingId, file, duration),
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to upload recording.")
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({
        queryKey: artifactKeys.recordings(variables.meetingId),
      })
    },
  })
}

export function useDeleteRecording() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ recordingId }) => meetingsApi.deleteRecording(recordingId),
    onSuccess: (_, variables) => {
      if (variables.meetingId) {
        qc.invalidateQueries({ queryKey: artifactKeys.recordings(variables.meetingId) })
      }
      toast.success("Recording deleted.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to delete recording.")
    },
  })
}

export function useRequestScreenShare() {
  return useMutation({
    mutationFn: ({ meetingId, participantId }) =>
      meetingsApi.requestScreenShare(meetingId, participantId),
    onSuccess: () => {
      toast.success("Screen share request sent to host.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to request screen share.")
    },
  })
}

export function useApproveScreenShare() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ meetingId, participantId }) =>
      meetingsApi.approveScreenShare(meetingId, participantId),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: meetingKeys.participants(variables.meetingId) })
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to approve screen share.")
    },
  })
}

export function useRejectScreenShare() {
  return useMutation({
    mutationFn: ({ meetingId, participantId }) =>
      meetingsApi.rejectScreenShare(meetingId, participantId),
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to reject screen share.")
    },
  })
}

export function useStopScreenShare() {
  return useMutation({
    mutationFn: (meetingId) =>
      meetingsApi.stopScreenShare(meetingId),
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to stop screen share.")
    },
  })
}

export function useTranscripts(meetingId) {
  return useQuery({
    queryKey: artifactKeys.transcripts(meetingId),
    queryFn: async () => {
      const { data } = await meetingsApi.listTranscripts(meetingId)
      return Array.isArray(data) ? data : []
    },
    enabled: !!meetingId,
    staleTime: 10_000,
  })
}

export function useUploadTranscript() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ meetingId, file, contentType }) =>
      meetingsApi.uploadTranscript(meetingId, file, contentType),
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to upload transcript.")
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({
        queryKey: artifactKeys.transcripts(variables.meetingId),
      })
    },
  })
}

export function useDeleteTranscript() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ transcriptId }) => meetingsApi.deleteTranscript(transcriptId),
    onSuccess: (_, variables) => {
      if (variables.meetingId) {
        qc.invalidateQueries({ queryKey: artifactKeys.transcripts(variables.meetingId) })
      }
      toast.success("Transcript deleted.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to delete transcript.")
    },
  })
}
