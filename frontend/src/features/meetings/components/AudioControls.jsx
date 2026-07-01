import { Button } from "@/components/ui/button"
import { Microphone, MicrophoneSlash, PhoneSlash } from "@phosphor-icons/react"

export function AudioControls({ isMuted, onToggleMute, onLeave }) {
  return (
    <div className="flex items-center justify-center gap-3">
      <Button
        variant={isMuted ? "destructive" : "outline"}
        size="lg"
        onClick={onToggleMute}
        aria-label={isMuted ? "Unmute microphone" : "Mute microphone"}
        className="min-w-[100px]"
      >
        {isMuted ? (
          <>
            <MicrophoneSlash className="size-4" />
            Unmute
          </>
        ) : (
          <>
            <Microphone className="size-4" />
            Mute
          </>
        )}
      </Button>

      <Button
        variant="destructive"
        size="lg"
        onClick={onLeave}
        aria-label="Leave meeting"
        className="min-w-[100px]"
      >
        <PhoneSlash className="size-4" />
        Leave
      </Button>
    </div>
  )
}
