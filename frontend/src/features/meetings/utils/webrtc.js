const RTC_CONFIG = {
  iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
}

export class RTCMeshManager {
  constructor(signalingClient) {
    this.signaling = signalingClient
    this.peers = new Map()
    this.localStream = null
    this.screenStream = null
    this.screenTrack = null
    this.audioEnabled = true
    this.isSharingScreen = false
    this.onTrack = null
    this.onParticipantStream = null
    this.onParticipantDisconnect = null
    this.onConnectionState = null
    this.onScreenShareStarted = null
    this.onScreenShareStopped = null
    this._cleanups = []
  }

  async initLocalStream() {
    try {
      this.localStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false,
      })
      this.audioEnabled = true
      return true
    } catch (err) {
      if (err.name === "NotAllowedError") {
        throw new Error("Microphone permission denied. Please allow microphone access.")
      }
      if (err.name === "NotFoundError") {
        throw new Error("No microphone found. Please connect a microphone.")
      }
      throw new Error("Could not access microphone.")
    }
  }

  createPeerConnection(connectionId) {
    if (this.peers.has(connectionId)) return this.peers.get(connectionId)

    const pc = new RTCPeerConnection(RTC_CONFIG)
    this.peers.set(connectionId, pc)

    if (this.localStream) {
      this.localStream.getTracks().forEach((track) => {
        pc.addTrack(track, this.localStream)
      })
    }

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        this.signaling.send("ice-candidate", connectionId, {
          candidate: event.candidate.toJSON(),
        })
      }
    }

    pc.ontrack = (event) => {
      if (this.onParticipantStream) {
        this.onParticipantStream(connectionId, event.streams[0])
      }
    }

    pc.oniceconnectionstatechange = () => {
      if (this.onConnectionState) {
        this.onConnectionState(connectionId, pc.iceConnectionState)
      }
      if (
        pc.iceConnectionState === "disconnected" ||
        pc.iceConnectionState === "failed"
      ) {
        this.removePeer(connectionId)
      }
    }

    pc.onconnectionstatechange = () => {
      if (this.onConnectionState) {
        this.onConnectionState(connectionId, pc.connectionState)
      }
    }

    return pc
  }

  async createOffer(targetConnectionId) {
    const pc = this.createPeerConnection(targetConnectionId)
    try {
      const offer = await pc.createOffer()
      await pc.setLocalDescription(offer)
      this.signaling.send("offer", targetConnectionId, {
        sdp: pc.localDescription,
      })
    } catch (err) {
      console.error("Failed to create offer:", err)
    }
  }

  async handleOffer(senderConnectionId, sdp) {
    const pc = this.createPeerConnection(senderConnectionId)
    try {
      await pc.setRemoteDescription(new RTCSessionDescription(sdp))
      const answer = await pc.createAnswer()
      await pc.setLocalDescription(answer)
      this.signaling.send("answer", senderConnectionId, {
        sdp: pc.localDescription,
      })
    } catch (err) {
      console.error("Failed to handle offer:", err)
    }
  }

  async handleAnswer(senderConnectionId, sdp) {
    const pc = this.peers.get(senderConnectionId)
    if (!pc) return
    try {
      await pc.setRemoteDescription(new RTCSessionDescription(sdp))
    } catch (err) {
      console.error("Failed to handle answer:", err)
    }
  }

  async handleIceCandidate(senderConnectionId, candidate) {
    const pc = this.peers.get(senderConnectionId)
    if (!pc) return
    try {
      await pc.addIceCandidate(new RTCIceCandidate(candidate))
    } catch (err) {
      console.error("Failed to add ICE candidate:", err)
    }
  }

  mute() {
    if (this.localStream) {
      this.localStream.getAudioTracks().forEach((track) => {
        track.enabled = false
      })
    }
    this.audioEnabled = false
  }

  unmute() {
    if (this.localStream) {
      this.localStream.getAudioTracks().forEach((track) => {
        track.enabled = true
      })
    }
    this.audioEnabled = true
  }

  async startScreenShare() {
    try {
      this.screenStream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: false,
      })
    } catch (err) {
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        throw new Error("Screen share permission denied.")
      }
      if (err.name === "NotFoundError") {
        throw new Error("No screen source found.")
      }
      throw new Error("Could not start screen share.")
    }

    this.screenTrack = this.screenStream.getVideoTracks()[0]
    this.isSharingScreen = true

    this.screenTrack.onended = () => {
      this.stopScreenShare()
    }

    for (const [connectionId, pc] of this.peers) {
      pc.addTrack(this.screenTrack, this.screenStream)
      try {
        const offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        this.signaling.send("offer", connectionId, {
          sdp: pc.localDescription,
        })
      } catch (err) {
        console.error("Failed to renegotiate with peer:", connectionId, err)
      }
    }

    return true
  }

  async stopScreenShare() {
    if (!this.isSharingScreen) return

    this.isSharingScreen = false

    if (this.screenTrack) {
      this.screenTrack.stop()
      this.screenTrack = null
    }

    if (this.screenStream) {
      this.screenStream.getTracks().forEach((t) => t.stop())
      this.screenStream = null
    }

    for (const [connectionId, pc] of this.peers) {
      const senders = pc.getSenders()
      for (const sender of senders) {
        if (sender.track && sender.track.kind === "video") {
          try {
            pc.removeTrack(sender)
          } catch (e) {
          }
        }
      }
      try {
        const offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        this.signaling.send("offer", connectionId, {
          sdp: pc.localDescription,
        })
      } catch (err) {
        console.error("Failed to renegotiate after stop:", connectionId, err)
      }
    }

    if (this.onScreenShareStopped) {
      this.onScreenShareStopped()
    }
  }

  removePeer(connectionId) {
    const pc = this.peers.get(connectionId)
    if (pc) {
      pc.close()
      this.peers.delete(connectionId)
    }
    if (this.onParticipantDisconnect) {
      this.onParticipantDisconnect(connectionId)
    }
  }

  destroy() {
    this.stopScreenShare()
    this.peers.forEach((pc) => pc.close())
    this.peers.clear()
    if (this.localStream) {
      this.localStream.getTracks().forEach((track) => track.stop())
      this.localStream = null
    }
    this._cleanups.forEach((fn) => fn())
    this._cleanups = []
  }
}
