export class RecordingManager {
  constructor() {
    this.mediaRecorder = null
    this.chunks = []
    this.isRecording = false
    this.mimeType = ""
    this.startTime = null
    this.onStart = null
    this.onStop = null
    this.onError = null
  }

  startRecording(stream) {
    if (this.isRecording) return

    const types = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/ogg;codecs=opus",
      "audio/mp4",
    ]

    let selectedType = ""
    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        selectedType = type
        break
      }
    }

    if (!selectedType) {
      selectedType = "audio/webm"
    }

    this.mimeType = selectedType
    this.chunks = []
    this.startTime = Date.now()

    try {
      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: selectedType,
      })
    } catch {
      this.mediaRecorder = new MediaRecorder(stream)
      this.mimeType = "audio/webm"
    }

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.chunks.push(event.data)
      }
    }

    this.mediaRecorder.onstart = () => {
      this.isRecording = true
      this.onStart?.()
    }

    this.mediaRecorder.onstop = () => {
      this.isRecording = false
      const blob = this.getBlob()
      const duration = this.getDuration()
      this.onStop?.(blob, duration)
    }

    this.mediaRecorder.onerror = (event) => {
      this.isRecording = false
      this.onError?.(event.error)
    }

    this.mediaRecorder.start(1000)
  }

  stopRecording() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop()
    }
  }

  getBlob() {
    if (this.chunks.length === 0) return null
    return new Blob(this.chunks, { type: this.mimeType })
  }

  getDuration() {
    if (!this.startTime) return 0
    return (Date.now() - this.startTime) / 1000
  }

  download(filename = "meeting-recording") {
    const blob = this.getBlob()
    if (!blob) return

    const ext = this.mimeType.includes("mp4") ? "mp4" : "webm"
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${filename}.${ext}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
}
