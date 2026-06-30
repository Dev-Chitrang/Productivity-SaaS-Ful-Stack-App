export class TranscriptManager {
  constructor() {
    this.recognition = null
    this.isActive = false
    this.transcriptEntries = []
    this.onTranscriptUpdate = null
    this.onError = null
    this.interimText = ""
    this.startTime = null
  }

  start() {
    if (this.isActive) return

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      this.onError?.(new Error("Speech recognition is not supported in this browser."))
      return false
    }

    try {
      this.recognition = new SpeechRecognition()
      this.recognition.continuous = true
      this.recognition.interimResults = true
      this.recognition.lang = "en-US"
      this.startTime = Date.now()

      this.recognition.onresult = (event) => {
        let finalTranscript = ""
        let interimTranscript = ""

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i]
          if (result.isFinal) {
            finalTranscript += result[0].transcript
          } else {
            interimTranscript += result[0].transcript
          }
        }

        if (finalTranscript) {
          const entry = {
            text: finalTranscript.trim(),
            timestamp: new Date().toISOString(),
            speaker: "You",
          }
          this.transcriptEntries.push(entry)
        }

        this.interimText = interimTranscript
        this.onTranscriptUpdate?.({
          entries: this.transcriptEntries,
          interim: interimTranscript,
        })
      }

      this.recognition.onerror = (event) => {
        if (event.error === "not-allowed") {
          this.onError?.(new Error("Microphone access denied for speech recognition."))
        } else if (event.error !== "no-speech") {
          this.onError?.(new Error(`Speech recognition error: ${event.error}`))
        }
      }

      this.recognition.onend = () => {
        if (this.isActive) {
          try {
            this.recognition.start()
          } catch {
            this.isActive = false
          }
        }
      }

      this.recognition.start()
      this.isActive = true
      return true
    } catch (err) {
      this.onError?.(err)
      return false
    }
  }

  stop() {
    this.isActive = false
    if (this.recognition) {
      try {
        this.recognition.stop()
      } catch {}
      this.recognition = null
    }
  }

  getTranscriptText() {
    return this.transcriptEntries
      .map((entry) => `[${new Date(entry.timestamp).toLocaleTimeString()}] ${entry.speaker}: ${entry.text}`)
      .join("\n")
  }

  getBlob() {
    const text = this.getTranscriptText()
    if (!text) return null
    return new Blob([text], { type: "text/plain" })
  }

  getDuration() {
    if (!this.startTime) return 0
    return (Date.now() - this.startTime) / 1000
  }

  download(filename = "meeting-transcript") {
    const blob = this.getBlob()
    if (!blob) return

    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${filename}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  reset() {
    this.stop()
    this.transcriptEntries = []
    this.interimText = ""
    this.startTime = null
  }
}
