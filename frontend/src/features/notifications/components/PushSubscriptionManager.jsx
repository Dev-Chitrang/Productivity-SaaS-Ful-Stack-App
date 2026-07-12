import { useEffect, useRef } from "react"
import {
  registerServiceWorker,
  requestNotificationPermission,
  getPushSubscription,
  subscribeToPush,
  subscriptionToApiPayload,
} from "../utils/pushManager"
import { useRegisterSubscription, useRemoveSubscription } from "../hooks/useNotificationsApi"

export default function PushSubscriptionManager() {
  const registerMutation = useRegisterSubscription()
  const removeMutation = useRemoveSubscription()
  const initialized = useRef(false)

  useEffect(() => {
    if (initialized.current) return
    initialized.current = true

    async function setup() {
      if (!("serviceWorker" in navigator) || !("PushManager" in window)) return

      try {
        const registration = await registerServiceWorker()
        if (!registration) return

        const permission = await requestNotificationPermission()
        if (permission !== "granted") return

        const existing = await getPushSubscription(registration)
        if (existing) {
          const payload = subscriptionToApiPayload(existing)
          if (payload) {
            registerMutation.mutate(payload)
          }
          return
        }

        const subscription = await subscribeToPush(registration)
        if (!subscription) return

        const payload = subscriptionToApiPayload(subscription)
        if (payload) {
          registerMutation.mutate(payload)
        }
      } catch (err) {
        console.warn("Push subscription setup failed:", err)
      }
    }

    setup()
  }, [])

  return null
}
