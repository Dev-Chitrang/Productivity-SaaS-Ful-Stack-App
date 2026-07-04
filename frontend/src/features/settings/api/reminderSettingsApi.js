import api from "@/lib/axios"

export const reminderSettingsApi = {
  get: () => api.get("/settings/reminders"),
  update: (data) => api.put("/settings/reminders", data),
}
