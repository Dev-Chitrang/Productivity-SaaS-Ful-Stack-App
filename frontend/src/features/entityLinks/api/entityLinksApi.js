import api from "@/lib/axios"

export const entityLinksApi = {
  create: (payload) => api.post("/entity-links", payload),
  delete: (linkId) => api.delete(`/entity-links/${linkId}`),
  list: (params) => api.get("/entity-links", { params }),
  getLinkedTasks: (meetingId) => api.get(`/meetings/${meetingId}/linked-tasks`),
  getLinkedMeetings: (taskId) => api.get(`/tasks/${taskId}/linked-meetings`),
  getSessionLinkedTasks: (meetingId, sessionId) =>
    api.get(`/meetings/${meetingId}/sessions/${sessionId}/linked-tasks`),
}
