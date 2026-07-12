const VAPID_PUBLIC_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/")
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

export async function registerServiceWorker() {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
    return null
  }
  try {
    const registration = await navigator.serviceWorker.register("/sw.js", {
      scope: "/",
    })
    return registration
  } catch (err) {
    console.warn("Service Worker registration failed:", err)
    return null
  }
}

export async function requestNotificationPermission() {
  if (!("Notification" in window)) return "denied"
  if (Notification.permission === "granted") return "granted"
  if (Notification.permission === "denied") return "denied"
  return await Notification.requestPermission()
}

export async function getPushSubscription(registration) {
  if (!registration) return null
  try {
    const subscription = await registration.pushManager.getSubscription()
    return subscription
  } catch {
    return null
  }
}

export async function subscribeToPush(registration) {
  if (!registration || !VAPID_PUBLIC_KEY) return null
  try {
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
    })
    return subscription
  } catch (err) {
    console.warn("Push subscription failed:", err)
    return null
  }
}

export function subscriptionToApiPayload(subscription) {
  if (!subscription) return null
  const endpoint = subscription.endpoint
  const keys = subscription.toJSON().keys
  return {
    endpoint,
    p256dh: keys.p256dh,
    auth: keys.auth,
    browser: detectBrowser(),
  }
}

function detectBrowser() {
  const ua = navigator.userAgent
  if (ua.includes("Firefox")) return "Firefox"
  if (ua.includes("Edg")) return "Edge"
  if (ua.includes("Chrome")) return "Chrome"
  if (ua.includes("Safari")) return "Safari"
  return "Unknown"
}
