import { useState, useEffect, useRef, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { ParticipantList } from "./ParticipantList"
import { AudioControls } from "./AudioControls"
import { RecordingControls } from "./RecordingControls"
import { TranscriptPanel } from "./TranscriptPanel"
import { SignalingClient } from "../utils/websocket"
import { RTCMeshManager } from "../utils/webrtc"
import { RecordingManager } from "../utils/recording"
import { TranscriptManager } from "../utils/transcript"
import {
  useUploadRecording,
  useUploadTranscript,
  useAdmitParticipant,
  useRejectParticipant,
  useRemoveParticipant,
  useMuteParticipant,
  useUnmuteParticipant,
  useRequestScreenShare,
  useApproveScreenShare,
  useRejectScreenShare,
  useStopScreenShare,
} from "../hooks/useMeetingsApi"
import { Copy, Clock, DoorOpen, Desktop, Stop, Monitor, Check, X } from "@phosphor-icons/react"
import toast from "react-hot-toast"

export function MeetingRoom({
  meeting,
  participants: initialParticipants,
  hostId,
  guestName,
  guestEmail,
  currentUserId,
  isHost,
  sessionToken,
  onLeave,
  onEndMeeting,
  endMeetingPending,
  onNavigateOnEnded,
}) {
  const uploadRecording = useUploadRecording()
  const uploadTranscript = useUploadTranscript()
  const admitParticipant = useAdmitParticipant()
  const rejectParticipant = useRejectParticipant()
  const removeParticipant = useRemoveParticipant()
  const muteParticipant = useMuteParticipant()
  const unmuteParticipant = useUnmuteParticipant()
  const requestScreenShare = useRequestScreenShare()
  const approveScreenShare = useApproveScreenShare()
  const rejectScreenShare = useRejectScreenShare()
  const stopScreenShareApi = useStopScreenShare()

  const [myParticipant, setMyParticipant] = useState(null)
  const [participants, setParticipants] = useState(
    (initialParticipants || []).filter(
      (p) => p.status === "WAITING" || p.status === "ADMITTED"
    )
  )
  const [connectionStates, setConnectionStates] = useState({})
  const [isMuted, setIsMuted] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [hasRecording, setHasRecording] = useState(false)
  const [transcriptActive, setTranscriptActive] = useState(false)
  const [transcriptData, setTranscriptData] = useState({ entries: [], interim: "" })
  const [audioError, setAudioError] = useState(null)
  const [actionPending, setActionPending] = useState(null)
  const [speechSupported] = useState(
    typeof window !== "undefined" && !!(window.SpeechRecognition || window.webkitSpeechRecognition)
  )

  const [screenShareRequests, setScreenShareRequests] = useState([])
  const [isScreenSharing, setIsScreenSharing] = useState(false)
  const [screenSharerId, setScreenSharerId] = useState(null)
  const [screenSharerName, setScreenSharerName] = useState(null)
  const [hasScreenSharePermission, setHasScreenSharePermission] = useState(false)
  const remoteVideoElsRef = useRef({})

  const signalingRef = useRef(null)
  const rtcRef = useRef(null)
  const recordingRef = useRef(null)
  const transcriptRef = useRef(null)
  const destroyedRef = useRef(false)
  const meetingEndedRef = useRef(false)
  const connMapRef = useRef({})
  const remoteAudioElsRef = useRef({})

  const isHostRef = useRef(isHost)
  const currentUserIdRef = useRef(currentUserId)
  const guestNameRef = useRef(guestName)
  const onLeaveRef = useRef(onLeave)
  const onNavigateOnEndedRef = useRef(onNavigateOnEnded)

  useEffect(() => {
    isHostRef.current = isHost
    currentUserIdRef.current = currentUserId
    guestNameRef.current = guestName
    onLeaveRef.current = onLeave
    onNavigateOnEndedRef.current = onNavigateOnEnded
  }, [isHost, currentUserId, guestName, onLeave, onNavigateOnEnded])

  const cleanupAll = useCallback(() => {
    if (recordingRef.current) {
      recordingRef.current.stopRecording()
    }
    if (transcriptRef.current) {
      transcriptRef.current.stop()
    }
    if (signalingRef.current) {
      signalingRef.current.disconnect()
    }
    if (rtcRef.current) {
      rtcRef.current.destroy()
    }
    Object.values(remoteAudioElsRef.current).forEach((el) => {
      el.pause()
      el.srcObject = null
      el.remove()
    })
    remoteAudioElsRef.current = {}
    Object.values(remoteVideoElsRef.current).forEach((el) => {
      el.pause()
      el.srcObject = null
      el.remove()
    })
    remoteVideoElsRef.current = {}
    destroyedRef.current = true
  }, [])

  useEffect(() => {
    const matches = (initialParticipants || []).filter(
      (p) => guestName ? p.guest_name === guestName : p.user_id === currentUserId
    )
    const terminalStatuses = ["LEFT", "REMOVED", "REJECTED"]
    const nonTerminal = matches.filter((p) => !terminalStatuses.includes(p.status))
    const candidates = nonTerminal.length > 0 ? nonTerminal : matches
    const me = candidates.reduce((best, p) => {
      if (!best) return p
      return new Date(p.joined_at || 0) > new Date(best.joined_at || 0) ? p : best
    }, null)
    setMyParticipant(me || null)
  }, [initialParticipants, guestName, currentUserId])

  useEffect(() => {
    if (meeting?.active_screen_sharer_id) {
      const sharer = (initialParticipants || []).find((p) => p.id === meeting.active_screen_sharer_id)
      if (sharer) {
        setScreenSharerId(sharer.id)
        setScreenSharerName(sharer.guest_name || sharer.user_name || "Someone")
        const isMe = guestName ? sharer.guest_name === guestName : sharer.user_id === currentUserId
        if (isMe) {
          setIsScreenSharing(true)
        }
      }
    }
  }, [meeting?.active_screen_sharer_id])

  useEffect(() => {
    const me = myParticipant
    if (me?.can_start_screen_share) {
      setHasScreenSharePermission(true)
    }
  }, [myParticipant?.can_start_screen_share])

  const handleParticipantJoined = useCallback((data) => {
    if (destroyedRef.current) return
    const isMe = guestNameRef.current
      ? data.guestName === guestNameRef.current
      : data.userId === currentUserIdRef.current

    const newParticipant = {
      id: data.participantId,
      connection_id: data.connectionId,
      guest_name: data.guestName,
      user_name: data.userName,
      user_id: data.userId,
      participant_type: data.userId ? "REGISTERED" : "GUEST",
      status: data.participantStatus || "WAITING",
      is_muted: data.isMuted || false,
      is_reconnecting: false,
    }

    connMapRef.current[data.connectionId] = data.participantId

    if (isMe) {
      setMyParticipant((prev) => {
        if (prev && prev.id === newParticipant.id) {
          return { ...prev, ...newParticipant }
        }
        return newParticipant
      })
    }

    setParticipants((prev) => {
      const idx = prev.findIndex((p) => p.id === newParticipant.id)
      if (idx >= 0) {
        const updated = [...prev]
        updated[idx] = { ...updated[idx], ...newParticipant }
        return updated
      }
      return [...prev, newParticipant]
    })
  }, [])

  const handleParticipantLeft = useCallback((data) => {
    if (destroyedRef.current) return
    setParticipants((prev) =>
      prev.filter((p) => p.connection_id !== data.connectionId)
    )
    if (rtcRef.current) {
      rtcRef.current.removePeer(data.connectionId)
    }
  }, [])

  const handleParticipantDisconnected = useCallback((data) => {
    if (destroyedRef.current) return
    setParticipants((prev) =>
      prev.map((p) =>
        p.connection_id === data.connectionId
          ? { ...p, is_reconnecting: true }
          : p
      )
    )
  }, [])

  const handleParticipantAdmitted = useCallback((data) => {
    if (destroyedRef.current) return
    const isMe = guestNameRef.current
      ? data.guestName === guestNameRef.current
      : data.userId === currentUserIdRef.current
    if (isMe) {
      setMyParticipant((prev) => {
        if (prev) return { ...prev, status: "ADMITTED" }
        return {
          id: data.participantId,
          guest_name: data.guestName,
          user_name: data.userName,
          user_id: data.userId,
          status: "ADMITTED",
          participant_type: data.userId ? "REGISTERED" : "GUEST",
        }
      })
    }
    setParticipants((prev) =>
      prev.map((p) =>
        p.id === data.participantId ? { ...p, status: "ADMITTED" } : p
      )
    )
  }, [])

  const handleParticipantWaiting = useCallback((data) => {
    if (destroyedRef.current) return
    setParticipants((prev) => {
      const exists = prev.some((p) => p.id === data.participantId)
      if (exists) return prev
      return [...prev, {
        id: data.participantId,
        connection_id: data.connectionId,
        guest_name: data.guestName,
        user_name: data.userName,
        user_id: data.userId,
        participant_type: data.userId ? "REGISTERED" : "GUEST",
        status: "WAITING",
        is_muted: false,
      }]
    })
  }, [])

  const handleMuteChanged = useCallback((data) => {
    if (destroyedRef.current) return
    setParticipants((prev) =>
      prev.map((p) =>
        p.id === data.participantId ? { ...p, is_muted: data.isMuted } : p
      )
    )
  }, [])

  const handleHostLeft = useCallback((data) => {
    if (destroyedRef.current) return
    if (data?.isTemporary) {
      toast(`${data?.hostName || "Host"} is reconnecting...`, { icon: "\u23f3" })
    } else {
      toast.success(`${data?.hostName || "Host"} has left the meeting.`)
    }
  }, [])

  const handleMeetingEnded = useCallback(() => {
    if (destroyedRef.current || meetingEndedRef.current) return
    meetingEndedRef.current = true
    cleanupAll()
    if (onNavigateOnEndedRef.current) {
      onNavigateOnEndedRef.current()
    }
  }, [cleanupAll])

  const handleParticipantRejected = useCallback(() => {
    if (destroyedRef.current) return
    toast.error("You have been rejected from the meeting.")
    cleanupAll()
    onLeaveRef.current()
  }, [cleanupAll])

  const handleParticipantRemoved = useCallback(() => {
    if (destroyedRef.current) return
    toast.error("You have been removed from the meeting.")
    cleanupAll()
    onLeaveRef.current()
  }, [cleanupAll])

  const handleScreenShareRequested = useCallback((data) => {
    if (destroyedRef.current) return
    if (isHostRef.current) {
      setScreenShareRequests((prev) => {
        if (prev.some((r) => r.participantId === data.participantId)) return prev
        return [...prev, { participantId: data.participantId, connectionId: data.connectionId, guestName: data.guestName, userId: data.userId }]
      })
    }
  }, [])

  const handleScreenSharePermissionGranted = useCallback((data) => {
    if (destroyedRef.current) return
    const isMe = guestNameRef.current ? data.guestName === guestNameRef.current : data.userId === currentUserIdRef.current
    if (isMe) {
      setHasScreenSharePermission(true)
      toast.success("Host granted screen share permission.")
    }
  }, [])

  const handleScreenSharePermissionDenied = useCallback(() => {
    if (destroyedRef.current) return
    toast.error("Screen share request denied.")
  }, [])

  const handleScreenShareStarted = useCallback((data) => {
    if (destroyedRef.current) return
    const isMe = guestNameRef.current ? data.guestName === guestNameRef.current : data.userId === currentUserIdRef.current
    if (isMe) {
      setIsScreenSharing(true)
      setScreenSharerId(data.participantId)
    } else {
      const name = data.guestName || "Someone"
      setScreenSharerId(data.participantId)
      setScreenSharerName(name)
    }
    setScreenShareRequests((prev) => prev.filter((r) => r.participantId !== data.participantId))
  }, [])

  const handleScreenShareStopped = useCallback((data) => {
    if (destroyedRef.current) return
    setScreenSharerId((prevId) => {
      if (prevId === data.participantId || !data.participantId) {
        if (rtcRef.current && rtcRef.current.isSharingScreen) {
          rtcRef.current.stopScreenShare()
        }
        return null
      }
      return null
    })
    setScreenSharerName(null)
    setIsScreenSharing(false)
    const el = remoteVideoElsRef.current[data.connectionId]
    if (el) {
      el.pause()
      el.srcObject = null
      el.remove()
      delete remoteVideoElsRef.current[data.connectionId]
    }
  }, [])

  const handleError = useCallback((data) => {
    if (destroyedRef.current) return
    if (data?.message) {
      toast.error(data.message)
    }
  }, [])

  const handleHostStoppedScreenShare = useCallback(async () => {
    if (destroyedRef.current) return
    setIsScreenSharing(false)
    setScreenSharerId(null)
    setScreenSharerName(null)
    if (rtcRef.current && rtcRef.current.isSharingScreen) {
      rtcRef.current.isSharingScreen = false
      if (rtcRef.current.screenTrack) {
        rtcRef.current.screenTrack.stop()
        rtcRef.current.screenTrack = null
      }
      if (rtcRef.current.screenStream) {
        rtcRef.current.screenStream.getTracks().forEach((t) => t.stop())
        rtcRef.current.screenStream = null
      }
      for (const [connectionId, pc] of rtcRef.current.peers) {
        const senders = pc.getSenders()
        for (const sender of senders) {
          if (sender.track && sender.track.kind === "video") {
            try { pc.removeTrack(sender) } catch (e) { }
          }
        }
        try {
          const offer = await pc.createOffer()
          await pc.setLocalDescription(offer)
          signalingRef.current?.send("offer", connectionId, { sdp: pc.localDescription })
        } catch (err) {
          console.error("Failed to renegotiate after host stop:", connectionId, err)
        }
      }
      toast.error("Host stopped your screen share.")
    }
    Object.values(remoteVideoElsRef.current).forEach((el) => {
      el.pause()
      el.srcObject = null
      el.remove()
    })
    remoteVideoElsRef.current = {}
  }, [])

  const handleOffer = useCallback((data) => {
    if (destroyedRef.current) return
    if (rtcRef.current) {
      rtcRef.current.handleOffer(data.senderConnectionId, data.sdp)
    }
  }, [])

  const handleAnswer = useCallback((data) => {
    if (destroyedRef.current) return
    if (rtcRef.current) {
      rtcRef.current.handleAnswer(data.senderConnectionId, data.sdp)
    }
  }, [])

  const handleIceCandidate = useCallback((data) => {
    if (destroyedRef.current) return
    if (rtcRef.current) {
      rtcRef.current.handleIceCandidate(data.senderConnectionId, data.candidate)
    }
  }, [])


  const initMediaAndRTC = useCallback(async () => {
    if (destroyedRef.current || !signalingRef.current) {
      return
    }
    let rtc, recorder, transcriber
    try {
      rtc = new RTCMeshManager(signalingRef.current)
    } catch (e) {
      console.error(e)
      return
    }
    try {
      recorder = new RecordingManager()
    } catch (e) {
      console.error(e)
      return
    }
    try {
      transcriber = new TranscriptManager()
    } catch (e) {
      console.error(e)
      return
    }

    rtcRef.current = rtc
    recordingRef.current = recorder
    transcriptRef.current = transcriber

    rtc.onParticipantStream = (connectionId, stream) => {
      if (destroyedRef.current) return
      const hasVideo = stream.getVideoTracks().length > 0
      let el = remoteVideoElsRef.current[connectionId] || remoteAudioElsRef.current[connectionId]
      if (el) {
        el.srcObject = stream
      } else {
        el = document.createElement(hasVideo ? "video" : "audio")
        el.autoplay = true
        el.playsInline = true
        el.srcObject = stream
        if (!hasVideo) {
          el.style.display = "none"
        }
        document.body.appendChild(el)
        el.play().catch(() => { })
        if (hasVideo) {
          remoteVideoElsRef.current[connectionId] = el
        } else {
          remoteAudioElsRef.current[connectionId] = el
        }
      }
    }

    rtc.onParticipantDisconnect = (connectionId) => {
      if (destroyedRef.current) return
      const audio = remoteAudioElsRef.current[connectionId]
      if (audio) {
        audio.pause()
        audio.srcObject = null
        audio.remove()
        delete remoteAudioElsRef.current[connectionId]
      }
      setParticipants((prev) =>
        prev.filter((p) => p.connection_id !== connectionId)
      )
    }

    rtc.onConnectionState = (connectionId, state) => {
      if (destroyedRef.current) return
      const pid = connMapRef.current[connectionId]
      if (pid) {
        setConnectionStates((prev) => ({ ...prev, [pid]: state }))
      }
    }

    rtc.onScreenShareStopped = () => {
      if (destroyedRef.current) return
      setIsScreenSharing(false)
      setScreenSharerId(null)
      setScreenSharerName(null)
      if (signalingRef.current) {
        signalingRef.current.send("screen_share_stopped", null, null)
      }
    }

    recorder.onStop = (blob, duration) => {
      if (destroyedRef.current) return
      setIsRecording(false)
      setHasRecording(true)
      toast.success("Recording finished.")
      if (blob) {
        const title = meeting.title.replace(/\s+/g, "-").toLowerCase()
        const ext = recorder.mimeType.includes("mp4") ? "mp4" : "webm"
        const file = new File([blob], `${title}-recording.${ext}`, {
          type: recorder.mimeType,
        })
        uploadRecording.mutate({ meetingId: meeting.id, file, duration })
      }
    }

    recorder.onError = (err) => {
      if (destroyedRef.current) return
      toast.error("Recording error: " + err.message)
      setIsRecording(false)
    }

    transcriber.onTranscriptUpdate = (data) => {
      if (destroyedRef.current) return
      setTranscriptData(data)
    }

    transcriber.onError = (err) => {
      if (destroyedRef.current) return
      toast.error(err.message)
    }

    try {
      await rtc.initLocalStream()
      setAudioError(null)
    } catch (err) {
      console.error("getUserMedia failed:", err)
      setAudioError(err.message)
      toast.error(err.message)
    }
  }, [meeting.id, meeting.title, uploadRecording, uploadTranscript])

  useEffect(() => {
    destroyedRef.current = false

    const signal = new SignalingClient(meeting.id, guestName, guestEmail)
    signalingRef.current = signal

    signal.on("participant_joined", handleParticipantJoined)
    signal.on("participant_waiting", handleParticipantWaiting)
    signal.on("participant_left", handleParticipantLeft)
    signal.on("participant_disconnected", handleParticipantDisconnected)
    signal.on("participant_admitted", handleParticipantAdmitted)
    signal.on("participant_removed", handleParticipantRemoved)
    signal.on("participant_rejected", handleParticipantRejected)
    signal.on("mute_changed", handleMuteChanged)
    signal.on("meeting_ended", handleMeetingEnded)
    signal.on("host_left", handleHostLeft)
    signal.on("offer", handleOffer)
    signal.on("answer", handleAnswer)
    signal.on("ice-candidate", handleIceCandidate)
    signal.on("screen_share_requested", handleScreenShareRequested)
    signal.on("screen_share_permission_granted", handleScreenSharePermissionGranted)
    signal.on("screen_share_permission_denied", handleScreenSharePermissionDenied)
    signal.on("screen_share_started", handleScreenShareStarted)
    signal.on("screen_share_stopped", handleScreenShareStopped)
    signal.on("host_stopped_screen_share", handleHostStoppedScreenShare)
    signal.on("error", handleError)
    signal.on("send_error", (data) => {
      if (destroyedRef.current) return
      toast.error(data.message || "Failed to send message.")
    })
    signal.on("connected", () => {
      if (destroyedRef.current) return
      toast.dismiss("ws-connecting")
    })
    signal.on("disconnected", () => { if (destroyedRef.current) return })

    signal.connect()

    return () => {
      cleanupAll()
    }
  }, [meeting.id])

  useEffect(() => {
    if (myParticipant?.status !== "ADMITTED") {
      return
    }
    if (!signalingRef.current) {
      return
    }
    if (rtcRef.current) {
      return
    }

    initMediaAndRTC()
  }, [myParticipant?.status, initMediaAndRTC])

  const handleRequestScreenShare = useCallback(() => {
    if (!myParticipant?.id) {
      toast.error("Not connected to meeting.")
      return
    }
    requestScreenShare.mutate({
      meetingId: meeting.id,
      participantId: myParticipant.id,
    })
  }, [meeting.id, myParticipant?.id, requestScreenShare])

  const handleStartScreenShare = useCallback(async () => {
    if (!rtcRef.current || !signalingRef.current) {
      toast.error("Connection not ready.")
      return
    }
    try {
      await rtcRef.current.startScreenShare()
      setIsScreenSharing(true)
      signalingRef.current.send("screen_share_started", null, null)
    } catch (err) {
      toast.error(err.message)
    }
  }, [])

  const handleToggleMute = useCallback(() => {
    if (!rtcRef.current) {
      return
    }
    if (isMuted) {
      rtcRef.current.unmute()
      setIsMuted(false)
      signalingRef.current?.send("self_unmute", null, null)
    } else {
      rtcRef.current.mute()
      setIsMuted(true)
      signalingRef.current?.send("self_mute", null, null)
    }
  }, [isMuted])

  const uploadTranscriptData = () => {
    const t = transcriptRef.current
    if (!t) return
    t.stop()
    const blob = t.getBlob()
    if (blob && t.transcriptEntries.length > 0) {
      const title = meeting.title.replace(/\s+/g, "-").toLowerCase()
      const file = new File([blob], `${title}-transcript.txt`, {
        type: "text/plain",
      })
      uploadTranscript.mutate({ meetingId: meeting.id, file, contentType: "text/plain" })
    }
  }

  const handleLeave = () => {
    if (recordingRef.current) recordingRef.current.stopRecording()
    uploadTranscriptData()
    cleanupAll()
    onLeave()
  }

  const handleStartRecording = async () => {
    if (!rtcRef.current?.localStream) {
      toast.error("No audio stream available.")
      return
    }
    recordingRef.current.startRecording(rtcRef.current.localStream)
    setIsRecording(true)
    toast.success("Recording started.")
  }

  const handleStopRecording = () => {
    recordingRef.current.stopRecording()
  }

  const handleDownloadRecording = () => {
    const title = meeting.title.replace(/\s+/g, "-").toLowerCase()
    recordingRef.current.download(`${title}-recording`)
  }

  const handleStartTranscript = () => {
    if (!transcriptRef.current) {
      toast.error("Transcript is not yet initialized.")
      return
    }
    const started = transcriptRef.current.start()
    if (started) {
      setTranscriptActive(true)
    }
  }

  const handleStopTranscript = () => {
    setTranscriptActive(false)
  }

  const handleDownloadTranscript = () => {
    const title = meeting.title.replace(/\s+/g, "-").toLowerCase()
    transcriptRef.current.download(`${title}-transcript`)
  }

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(
        `${window.location.origin}/meetings/${meeting.id}`
      )
      toast.success("Link copied.")
    } catch {
      toast.error("Failed to copy link.")
    }
  }

  const handleAdmit = async (participantId) => {
    setActionPending(participantId)
    try {
      await admitParticipant.mutateAsync({ meetingId: meeting.id, participantId })
      setParticipants((prev) =>
        prev.map((p) => (p.id === participantId ? { ...p, status: "ADMITTED" } : p))
      )
    } catch { }
    setActionPending(null)
  }

  const handleReject = async (participantId) => {
    setActionPending(participantId)
    try {
      await rejectParticipant.mutateAsync({ meetingId: meeting.id, participantId })
      setParticipants((prev) => prev.filter((p) => p.id !== participantId))
    } catch { }
    setActionPending(null)
  }

  const handleRemove = async (participantId) => {
    setActionPending(participantId)
    try {
      await removeParticipant.mutateAsync({ meetingId: meeting.id, participantId })
      setParticipants((prev) => prev.filter((p) => p.id !== participantId))
    } catch { }
    setActionPending(null)
  }

  const handleMute = async (participantId) => {
    setActionPending(participantId)
    try {
      await muteParticipant.mutateAsync({ meetingId: meeting.id, participantId })
      setParticipants((prev) =>
        prev.map((p) => (p.id === participantId ? { ...p, is_muted: true } : p))
      )
    } catch { }
    setActionPending(null)
  }

  const handleUnmute = async (participantId) => {
    setActionPending(participantId)
    try {
      await unmuteParticipant.mutateAsync({ meetingId: meeting.id, participantId })
      setParticipants((prev) =>
        prev.map((p) => (p.id === participantId ? { ...p, is_muted: false } : p))
      )
    } catch { }
    setActionPending(null)
  }

  if (myParticipant?.status === "WAITING") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{meeting.title}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="flex size-16 items-center justify-center rounded-full bg-amber-50 dark:bg-amber-950 mb-4">
              <Clock className="size-8 text-amber-500" weight="fill" />
            </div>
            <h2 className="text-lg font-semibold text-foreground mb-2">
              Waiting Room
            </h2>
            <p className="text-sm text-muted-foreground max-w-sm">
              Waiting for host to admit you...
            </p>
            <Button
              variant="outline"
              size="sm"
              className="mt-6 gap-2"
              onClick={handleLeave}
            >
              <DoorOpen className="size-4" />
              Leave Meeting
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">{meeting.title}</CardTitle>
            <Button variant="ghost" size="icon-sm" onClick={handleCopyLink} aria-label="Copy meeting link">
              <Copy className="size-3.5" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {audioError && (
            <div
              className="rounded border border-destructive/50 bg-destructive/10 px-3 py-2 text-xs text-destructive"
              role="alert"
            >
              {audioError}
            </div>
          )}

          <ParticipantList
            participants={participants}
            hostId={hostId}
            currentUserId={currentUserId}
            connectionStates={connectionStates}
            isHost={isHost}
            onAdmit={isHost ? handleAdmit : undefined}
            onReject={isHost ? handleReject : undefined}
            onRemove={isHost ? handleRemove : undefined}
            onMute={isHost ? handleMute : undefined}
            onUnmute={isHost ? handleUnmute : undefined}
            actionPending={actionPending}
          />

          <Separator />

          <AudioControls
            isMuted={isMuted}
            onToggleMute={handleToggleMute}
            onLeave={handleLeave}
          />

          <Separator />

          <div className="space-y-3">
            <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
              Screen Share
            </p>

            {isHost && (
              <div className="space-y-2">
                {screenSharerId && screenSharerId !== myParticipant?.id ? (
                  <div className="flex items-center justify-between gap-2 rounded bg-muted/50 px-3 py-2">
                    <span className="text-xs text-muted-foreground truncate">
                      <Monitor className="inline size-3 mr-1" weight="fill" />
                      {screenSharerName || "Someone"} is sharing
                    </span>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={async () => {
                        await stopScreenShareApi.mutateAsync(meeting.id)
                      }}
                      disabled={stopScreenShareApi.isPending}
                    >
                      <Stop className="size-3.5 mr-1" />
                      Stop
                    </Button>
                  </div>
                ) : isScreenSharing ? (
                  <Button
                    variant="secondary"
                    size="sm"
                    className="w-full gap-2"
                    onClick={async () => {
                      if (rtcRef.current) {
                        await rtcRef.current.stopScreenShare()
                      }
                    }}
                  >
                    <Stop className="size-4" />
                    Stop Sharing
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full gap-2"
                    onClick={handleStartScreenShare}
                  >
                    <Desktop className="size-4" />
                    Share Screen
                  </Button>
                )}
              </div>
            )}

            {!isHost && (
              <div className="space-y-2">
                {screenSharerId && screenSharerId !== myParticipant?.id ? (
                  <div className="flex items-center gap-2 rounded bg-muted/50 px-3 py-2">
                    <Monitor className="size-4 text-muted-foreground shrink-0" weight="fill" />
                    <span className="text-xs text-muted-foreground">
                      Currently sharing: <strong>{screenSharerName || "Someone"}</strong>
                    </span>
                  </div>
                ) : isScreenSharing ? (
                  <Button
                    variant="secondary"
                    size="sm"
                    className="w-full gap-2"
                    onClick={async () => {
                      if (rtcRef.current) {
                        await rtcRef.current.stopScreenShare()
                      }
                    }}
                  >
                    <Stop className="size-4" />
                    Stop Sharing
                  </Button>
                ) : hasScreenSharePermission ? (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full gap-2"
                    onClick={handleStartScreenShare}
                  >
                    <Desktop className="size-4" />
                    Share Screen
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full gap-2"
                    onClick={handleRequestScreenShare}
                  >
                    <Desktop className="size-4" />
                    Request Screen Share
                  </Button>
                )}
              </div>
            )}

            {isHost && screenShareRequests.length > 0 && (
              <div className="space-y-2 pt-1">
                <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                  Pending Requests ({screenShareRequests.length})
                </p>
                {screenShareRequests.map((req) => {
                  const rName = req.guestName || req.userId?.slice(0, 8) || "Unknown"
                  return (
                    <div key={req.participantId} className="flex items-center justify-between gap-2 rounded bg-muted/50 px-3 py-2">
                      <span className="text-xs truncate">{rName}</span>
                      <div className="flex gap-1 shrink-0">
                        <Button
                          variant="ghost"
                          size="icon-xs"
                          onClick={async () => {
                            await approveScreenShare.mutateAsync({ meetingId: meeting.id, participantId: req.participantId })
                            setScreenShareRequests((prev) => prev.filter((r) => r.participantId !== req.participantId))
                          }}
                          disabled={approveScreenShare.isPending}
                          className="text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-950"
                        >
                          <Check className="size-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-xs"
                          onClick={async () => {
                            await rejectScreenShare.mutateAsync({ meetingId: meeting.id, participantId: req.participantId })
                            setScreenShareRequests((prev) => prev.filter((r) => r.participantId !== req.participantId))
                          }}
                          disabled={rejectScreenShare.isPending}
                          className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        >
                          <X className="size-3.5" />
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {isHost && (
            <div className="flex justify-center">
              <Button
                variant="destructive"
                size="sm"
                onClick={onEndMeeting}
                disabled={endMeetingPending}
                aria-label="End meeting for all"
              >
                {endMeetingPending ? "Ending..." : "End Meeting"}
              </Button>
            </div>
          )}

          {isHost && meeting.enable_recording && (
            <>
              <Separator />
              <RecordingControls
                isRecording={isRecording}
                hasRecording={hasRecording}
                onStartRecording={handleStartRecording}
                onStopRecording={handleStopRecording}
                onDownload={handleDownloadRecording}
              />
            </>
          )}

          {isHost && meeting.enable_transcript && (
            <>
              <Separator />
              <TranscriptPanel
                isActive={transcriptActive}
                entries={transcriptData.entries}
                interimText={transcriptData.interim}
                onStart={handleStartTranscript}
                onStop={handleStopTranscript}
                onDownload={handleDownloadTranscript}
                speechSupported={speechSupported}
              />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
