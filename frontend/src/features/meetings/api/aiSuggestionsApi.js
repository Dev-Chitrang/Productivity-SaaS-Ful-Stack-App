import api from "@/lib/axios"

export const aiSuggestionsApi = {
  list: (analysisId) => api.get("/ai-suggestions", { params: { analysis_id: analysisId } }),
  createTask: (suggestionId, payload) => api.post(`/ai-suggestions/${suggestionId}/create-task`, payload || {}),
  reject: (suggestionId) => api.post(`/ai-suggestions/${suggestionId}/reject`),
}
