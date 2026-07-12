import api from "@/lib/axios"

export const registerSubscription = (payload) =>
  api.post("/notifications/subscriptions", payload)

export const removeSubscription = (endpoint) =>
  api.delete("/notifications/subscriptions", { params: { endpoint } })

export const listNotifications = (params = {}) => {
  const clean = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""),
  )
  return api.get("/notifications", { params: clean })
}

export const getNotification = (id) => api.get(`/notifications/${id}`)

export const getUnreadCount = () => api.get("/notifications/unread-count")

export const getRecentNotifications = () => api.get("/notifications/recent")

export const markAsRead = (notification_ids) =>
  api.post("/notifications/mark-read", { notification_ids })

export const markAllAsRead = () => api.post("/notifications/mark-all-read")
