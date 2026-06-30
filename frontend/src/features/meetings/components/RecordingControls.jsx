import { Button } from "@/components/ui/button"
import { Spinner, DownloadSimple, Record, StopCircle } from "@phosphor-icons/react"
import { useState } from "react"

export function RecordingControls({
  isRecording,
  hasRecording,
  onStartRecording,
  onStopRecording,
  onDownload,
}) {
  const [starting, setStarting] = useState(false)

  const handleStart = async () => {
    setStarting(true)
    await onStartRecording()
    setStarting(false)
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        {isRecording ? (
          <Button
            variant="destructive"
            size="sm"
            onClick={onStopRecording}
            aria-label="Stop recording"
            className="animate-pulse"
          >
            <StopCircle className="size-3.5" />
            Stop Recording
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={handleStart}
            disabled={starting}
            aria-label="Start recording"
          >
            {starting ? (
              <Spinner className="size-3.5 animate-spin" />
            ) : (
              <Record className="size-3.5" />
            )}
            Start Recording
          </Button>
        )}

        {hasRecording && !isRecording && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onDownload}
            aria-label="Download recording"
          >
            <DownloadSimple className="size-3.5" />
            Download
          </Button>
        )}
      </div>

      {isRecording && (
        <div className="flex items-center gap-1.5 text-[10px] text-red-500">
          <span className="size-1.5 rounded-full bg-red-500 animate-pulse" />
          Recording...
        </div>
      )}
    </div>
  )
}
