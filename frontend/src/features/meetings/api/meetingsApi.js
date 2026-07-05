import api from "@/lib/axios"

export const meetingsApi = {
  list: () => api.get("/meetings"),
  get: (id) => api.get(`/meetings/${id}`),
  getByCode: (code) => api.get(`/meetings/by-code/${encodeURIComponent(code)}`),
  create: (data) => api.post("/meetings", data),
  createScheduled: (data) => api.post("/meetings/scheduled", data),
  update: (id, data) => api.patch(`/meetings/${id}`, data),
  delete: (id) => api.delete(`/meetings/${id}`),
  end: (id) => api.post(`/meetings/${id}/end`),
  cancel: (id) => api.post(`/meetings/${id}/cancel`),
  copyLink: (id) => api.post(`/meetings/${id}/copy-link`),
  join: (id, data) => api.post(`/meetings/${id}/join`, data || {}),
  participants: (id) => api.get(`/meetings/${id}/participants`),
  admitParticipant: (meetingId, participantId) =>
    api.post(`/meetings/${meetingId}/participants/${participantId}/admit`),
  rejectParticipant: (meetingId, participantId) =>
    api.post(`/meetings/${meetingId}/participants/${participantId}/reject`),
  removeParticipant: (meetingId, participantId) =>
    api.post(`/meetings/${meetingId}/participants/${participantId}/remove`),
  muteParticipant: (meetingId, participantId) =>
    api.post(`/meetings/${meetingId}/participants/${participantId}/mute`),
  unmuteParticipant: (meetingId, participantId) =>
    api.post(`/meetings/${meetingId}/participants/${participantId}/unmute`),

  leave: (id, data) => api.post(`/meetings/${id}/leave`, data || {}),
  waitingCount: (id) => api.get(`/meetings/${id}/waiting-count`),

  requestScreenShare: (meetingId, participantId) =>
    api.post(`/meetings/${meetingId}/screen-share/request`, { participant_id: participantId }),
  approveScreenShare: (meetingId, participantId) =>
    api.post(`/meetings/${meetingId}/screen-share/approve/${participantId}`),
  rejectScreenShare: (meetingId, participantId) =>
    api.post(`/meetings/${meetingId}/screen-share/reject/${participantId}`),
  stopScreenShare: (meetingId) =>
    api.post(`/meetings/${meetingId}/screen-share/stop`),

  uploadRecording: (meetingId, file, duration) => {
    const form = new FormData()
    form.append("file", file)
    if (duration != null) form.append("duration", String(duration))
    return api.post(`/meetings/${meetingId}/recordings`, form)
  },

  listRecordings: (meetingId) => api.get(`/meetings/${meetingId}/recordings`),

  downloadRecording: (recordingId) =>
    api.get(`/meetings/recordings/${recordingId}/download`, {
      responseType: "blob",
    }),

  deleteRecording: (recordingId) =>
    api.delete(`/meetings/recordings/${recordingId}`),

  uploadTranscript: (meetingId, file, contentType = "text/plain") => {
    const form = new FormData()
    form.append("file", file)
    form.append("content_type", contentType)
    return api.post(`/meetings/${meetingId}/transcripts`, form)
  },

  listTranscripts: (meetingId) => api.get(`/meetings/${meetingId}/transcripts`),

  downloadTranscript: (transcriptId) =>
    api.get(`/meetings/transcripts/${transcriptId}/download`, {
      responseType: "blob",
    }),

  deleteTranscript: (transcriptId) =>
    api.delete(`/meetings/transcripts/${transcriptId}`),

  getAnalysis: (meetingId) => api.get(`/meetings/${meetingId}/analysis`),

  getAnalysisStatus: (meetingId) => api.get(`/meetings/${meetingId}/analysis/status`),

  // Session History (Phase 5)
  listSessions: (meetingId) => api.get(`/meetings/${meetingId}/sessions`),
  getSession: (meetingId, sessionId) => api.get(`/meetings/${meetingId}/sessions/${sessionId}`),
  listSessionRecordings: (meetingId, sessionId) =>
    api.get(`/meetings/${meetingId}/sessions/${sessionId}/recordings`),
  listSessionTranscripts: (meetingId, sessionId) =>
    api.get(`/meetings/${meetingId}/sessions/${sessionId}/transcripts`),
  getSessionAnalysis: (meetingId, sessionId) =>
    api.get(`/meetings/${meetingId}/sessions/${sessionId}/analysis`),
  getSessionAnalysisStatus: (meetingId, sessionId) =>
    api.get(`/meetings/${meetingId}/sessions/${sessionId}/analysis/status`),
}
