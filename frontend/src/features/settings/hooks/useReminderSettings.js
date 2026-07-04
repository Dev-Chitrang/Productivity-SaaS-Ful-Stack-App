import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import toast from "react-hot-toast"

import { reminderSettingsApi } from "@/features/settings/api/reminderSettingsApi"

export const reminderSettingsKeys = {
  all: () => ["reminder-settings"],
}

export function useReminderSettings() {
  return useQuery({
    queryKey: reminderSettingsKeys.all(),
    queryFn: async () => {
      const { data } = await reminderSettingsApi.get()
      return data
    },
    staleTime: 5 * 60 * 1000,
  })
}

export function useUpdateReminderSettings() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (payload) => reminderSettingsApi.update(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: reminderSettingsKeys.all() })
      toast.success("Reminder settings saved.")
    },
    onError: () => {
      toast.error("Failed to save reminder settings.")
    },
  })
}
