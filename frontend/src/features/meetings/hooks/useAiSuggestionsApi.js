import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import toast from "react-hot-toast"
import { aiSuggestionsApi } from "../api/aiSuggestionsApi"

export const suggestionKeys = {
  all: (analysisId) => ["ai-suggestions", analysisId],
  list: (analysisId) => [...suggestionKeys.all(analysisId), "list"],
}

export function useAiSuggestions(analysisId) {
  return useQuery({
    queryKey: suggestionKeys.list(analysisId),
    queryFn: async () => {
      const { data } = await aiSuggestionsApi.list(analysisId)
      return data?.suggestions ?? []
    },
    enabled: !!analysisId,
    staleTime: 30_000,
  })
}

export function useCreateTaskFromSuggestion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ suggestionId, payload }) => aiSuggestionsApi.createTask(suggestionId, payload),
    onSuccess: (_, variables) => {
      const analysisId = variables.analysisId
      if (analysisId) {
        qc.invalidateQueries({ queryKey: suggestionKeys.all(analysisId) })
      }
      qc.invalidateQueries({ queryKey: ["tasks"] })
      toast.success("Task created from suggestion.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to create task from suggestion.")
    },
  })
}

export function useRejectSuggestion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ suggestionId, analysisId }) => aiSuggestionsApi.reject(suggestionId),
    onSuccess: (_, variables) => {
      if (variables.analysisId) {
        qc.invalidateQueries({ queryKey: suggestionKeys.all(variables.analysisId) })
      }
      toast.success("Suggestion rejected.")
    },
    onError: (err) => {
      const detail = err?.response?.data?.detail
      toast.error(detail || "Failed to reject suggestion.")
    },
  })
}
