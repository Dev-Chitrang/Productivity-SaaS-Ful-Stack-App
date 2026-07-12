import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import toast from "react-hot-toast"
import * as notificationsApi from "../api/notificationsApi"
import { LIST_STALE_TIME, UNREAD_POLL_INTERVAL } from "../constants"

export const notificationKeys = {
  all: () => ["notifications"],
  lists: () => [...notificationKeys.all(), "list"],
  list: (filters) => [...notificationKeys.lists(), filters],
  details: () => [...notificationKeys.all(), "detail"],
  detail: (id) => [...notificationKeys.details(), id],
  unreadCount: () => [...notificationKeys.all(), "unread-count"],
  recent: () => [...notificationKeys.all(), "recent"],
}

export function useNotifications(filters = {}) {
  return useQuery({
    queryKey: notificationKeys.list(filters),
    queryFn: async () => {
      const { data } = await notificationsApi.listNotifications(filters)
      return data
    },
    staleTime: LIST_STALE_TIME,
  })
}

export function useNotification(id) {
  return useQuery({
    queryKey: notificationKeys.detail(id),
    queryFn: async () => {
      const { data } = await notificationsApi.getNotification(id)
      return data
    },
    enabled: !!id,
    staleTime: LIST_STALE_TIME,
  })
}

export function useUnreadCount() {
  return useQuery({
    queryKey: notificationKeys.unreadCount(),
    queryFn: async () => {
      const { data } = await notificationsApi.getUnreadCount()
      return data.count
    },
    refetchInterval: UNREAD_POLL_INTERVAL,
    staleTime: UNREAD_POLL_INTERVAL,
  })
}

export function useRecentNotifications() {
  return useQuery({
    queryKey: notificationKeys.recent(),
    queryFn: async () => {
      const { data } = await notificationsApi.getRecentNotifications()
      return data
    },
    staleTime: LIST_STALE_TIME,
  })
}

export function useMarkAsRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (notification_ids) => notificationsApi.markAsRead(notification_ids),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: notificationKeys.all() })
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail || "Failed to mark as read.")
    },
  })
}

export function useMarkAllAsRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => notificationsApi.markAllAsRead(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: notificationKeys.all() })
      toast.success("All notifications marked as read.")
    },
    onError: (err) => {
      toast.error(err?.response?.data?.detail || "Failed to mark all as read.")
    },
  })
}

export function useRegisterSubscription() {
  return useMutation({
    mutationFn: (payload) => notificationsApi.registerSubscription(payload),
    onError: () => {},
  })
}

export function useRemoveSubscription() {
  return useMutation({
    mutationFn: (endpoint) => notificationsApi.removeSubscription(endpoint),
    onError: () => {},
  })
}
