import { Button } from "@/components/ui/button"
import { DownloadSimple } from "@phosphor-icons/react"
import { useRef, useEffect } from "react"

export function TranscriptPanel({
  isActive,
  entries,
  interimText,
  onStart,
  onStop,
  onDownload,
  speechSupported = true,
}) {
  const bottomRef = useRef(null)

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [entries, interimText])

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium">Transcript</span>
        <div className="flex items-center gap-1">
          {entries.length > 0 && (
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={onDownload}
              aria-label="Download transcript"
            >
              <DownloadSimple className="size-3.5" />
            </Button>
          )}
          {!speechSupported ? (
            <Button variant="outline" size="xs" disabled aria-label="Transcript not supported">
              Start
            </Button>
          ) : isActive ? (
            <Button
              variant="destructive"
              size="xs"
              onClick={onStop}
              aria-label="Stop transcript"
            >
              Stop
            </Button>
          ) : (
            <Button
              variant="outline"
              size="xs"
              onClick={onStart}
              aria-label="Start transcript"
            >
              Start
            </Button>
          )}
        </div>
      </div>

      {!speechSupported && (
        <p className="text-xs text-muted-foreground text-center py-2">
          Speech Recognition is not supported in this browser.
        </p>
      )}

      <div className="max-h-48 overflow-y-auto rounded border border-border bg-muted/30 p-2 text-xs leading-relaxed">
        {entries.length === 0 && !interimText ? (
          <p className="text-muted-foreground text-center py-4">
            {isActive
              ? "Listening..."
              : "Transcript not started."}
          </p>
        ) : (
          <div className="space-y-1">
            {entries.map((entry, i) => (
              <div key={i} className="flex gap-2">
                <span className="text-muted-foreground shrink-0">
                  [{new Date(entry.timestamp).toLocaleTimeString()}]
                </span>
                <span>
                  <span className="font-medium">{entry.speaker}:</span>{" "}
                  {entry.text}
                </span>
              </div>
            ))}
            {interimText && (
              <p className="text-muted-foreground italic">{interimText}</p>
            )}
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
