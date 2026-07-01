export function getWebSocketUrl(meetingId, guestName, guestEmail) {
  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"
  const host = apiUrl.replace(/^https?:\/\//, "").replace("/api/v1", "")
  const protocol = apiUrl.startsWith("https") ? "wss" : "ws"
  const params = new URLSearchParams()
  const token = localStorage.getItem("access_token")
  if (token) {
    params.set("token", token)
  } else if (guestName) {
    params.set("guest_name", guestName)
    if (guestEmail) {
      params.set("guest_email", guestEmail)
    }
  }
  const qs = params.toString()
  return `${protocol}://${host}/ws/meetings/${meetingId}${qs ? "?" + qs : ""}`
}

export class SignalingClient {
  constructor(meetingId, guestName, guestEmail) {
    this.meetingId = meetingId
    this.guestName = guestName || null
    this.guestEmail = guestEmail || null
    this.ws = null
    this.listeners = new Map()
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 2000
    this.intentionalClose = false
    this.connectionId = null
    this._pendingQueue = []
  }

  connect() {
    const url = getWebSocketUrl(this.meetingId, this.guestName, this.guestEmail)
    this.intentionalClose = false
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      this._flushQueue()
      this._emit("connected")
    }

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        this._handleMessage(message)
      } catch (e) {
        console.error("Failed to parse WS message:", e)
      }
    }

    this.ws.onclose = (event) => {
      if (this.ws !== event.target && this.ws !== null) {
        return
      }
      this._emit("disconnected", { code: event.code })
      if (this.intentionalClose || event.code === 4000) {
        return
      }
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts)
        this.reconnectAttempts++
        console.log("[Signaling] reconnect in " + delay + "ms (attempt " + this.reconnectAttempts + "/" + this.maxReconnectAttempts + ")")
        setTimeout(() => this.connect(), delay)
      } else {
        console.log("[Signaling] max reconnect attempts reached")
        this._emit("send_error", { type: "reconnect_failed", message: "Could not reconnect to server." })
      }
    }

    this.ws.onerror = () => {
      console.log("[Signaling] websocket error")
    }
  }

  disconnect() {
    this.intentionalClose = true
    this._pendingQueue = []
    if (this.ws) {
      const ws = this.ws
      this.ws = null
      ws.close(1000)
    }
  }

  send(type, targetConnectionId, payload) {
    const message = {
      type,
      target_connection_id: targetConnectionId || null,
      payload: payload || null,
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
      return
    }

    if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
      this._pendingQueue.push(message)
      console.log("[Signaling] queued: " + type + " (readyState=CONNECTING)")
      return
    }

    console.log("[Signaling] send failed: " + type + " (readyState=" + (this.ws ? this.ws.readyState : "null") + ")")
    this._emit("send_error", { type, message: "WebSocket is not connected." })
  }

  _flushQueue() {
    if (this._pendingQueue.length === 0) return
    const queue = this._pendingQueue
    this._pendingQueue = []
    for (const msg of queue) {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(msg))
      }
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event).add(callback)
    return () => this.listeners.get(event)?.delete(callback)
  }

  _emit(event, data) {
    const callbacks = this.listeners.get(event)
    if (callbacks) {
      callbacks.forEach((cb) => {
        try {
          cb(data)
        } catch (e) {
          console.error("WS listener error:", e)
        }
      })
    }
  }

  _handleMessage(message) {
    const { event, data, sender_connection_id, payload } = message

    switch (event) {
      case "participant_joined":
        this._emit("participant_joined", {
          connectionId: data?.connection_id,
          participantId: data?.participant_id,
          participantStatus: data?.participant_status,
          guestName: data?.guest_name,
          userId: data?.user_id,
          type: data?.type,
          isMuted: data?.is_muted,
        })
        break

      case "participant_waiting":
        this._emit("participant_waiting", {
          connectionId: data?.connection_id,
          participantId: data?.participant_id,
          guestName: data?.guest_name,
          userId: data?.user_id,
          type: data?.type,
        })
        break

      case "participant_left":
        this._emit("participant_left", {
          connectionId: data?.connection_id,
          userId: data?.user_id,
        })
        break

      case "participant_admitted":
        this._emit("participant_admitted", {
          connectionId: data?.connection_id,
          participantId: data?.participant_id,
          guestName: data?.guest_name,
          userId: data?.user_id,
          message: data?.message,
        })
        break

      case "participant_removed":
        this._emit("participant_removed", {
          message: data?.message,
        })
        break

      case "participant_rejected":
        this._emit("participant_rejected", {
          message: data?.message,
        })
        break

      case "mute_changed":
        this._emit("mute_changed", {
          participantId: data?.participant_id,
          isMuted: data?.is_muted,
        })
        break

      case "meeting_ended":
        this._emit("meeting_ended", {
          meetingId: data?.meeting_id,
          message: data?.message,
        })
        break

      case "host_left":
        this._emit("host_left", {
          hostId: data?.host_id,
          hostName: data?.host_name,
          timestamp: data?.timestamp,
        })
        break

      case "waiting_room_status":
        this._emit("waiting_room_status", {
          message: data?.message,
        })
        break

      case "status_check":
        this._emit("status_check", {
          status: data?.status,
        })
        break

      case "muted":
        this._emit("muted", {
          message: data?.message,
        })
        break

      case "offer":
        this._emit("offer", {
          senderConnectionId: sender_connection_id,
          sdp: payload?.sdp,
        })
        break

      case "answer":
        this._emit("answer", {
          senderConnectionId: sender_connection_id,
          sdp: payload?.sdp,
        })
        break

      case "ice-candidate":
        this._emit("ice-candidate", {
          senderConnectionId: sender_connection_id,
          candidate: payload?.candidate,
        })
        break

      case "screen_share_requested":
        this._emit("screen_share_requested", {
          participantId: data?.participant_id,
          connectionId: data?.connection_id,
          guestName: data?.guest_name,
          userId: data?.user_id,
        })
        break

      case "screen_share_permission_granted":
        this._emit("screen_share_permission_granted", {
          participantId: data?.participant_id,
          connectionId: data?.connection_id,
          guestName: data?.guest_name,
          userId: data?.user_id,
        })
        break

      case "screen_share_permission_denied":
        this._emit("screen_share_permission_denied", {
          message: data?.message,
        })
        break

      case "screen_share_started":
        this._emit("screen_share_started", {
          participantId: data?.participant_id,
          connectionId: data?.connection_id,
          guestName: data?.guest_name,
          userId: data?.user_id,
        })
        break

      case "screen_share_stopped":
        this._emit("screen_share_stopped", {
          participantId: data?.participant_id,
          connectionId: data?.connection_id,
        })
        break

      case "host_stopped_screen_share":
        this._emit("host_stopped_screen_share", {
          meetingId: data?.meeting_id,
        })
        break

      case "error":
        this._emit("error", {
          message: message?.message,
        })
        break

      default:
        this._emit("message", message)
    }
  }
}
