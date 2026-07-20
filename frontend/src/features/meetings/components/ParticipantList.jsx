import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { ParticipantType, ParticipantStatus } from "../api/meetingTypes"
import { Crown, MicrophoneSlash, Microphone, Prohibit, Check, X, SpinnerGap } from "@phosphor-icons/react"

export function ParticipantList({
  participants,
  hostId,
  currentUserId,
  connectionStates,
  isHost,
  onAdmit,
  onReject,
  onRemove,
  onMute,
  onUnmute,
  actionPending,
}) {
  const waiting = (participants || []).filter((p) => p.status === ParticipantStatus.WAITING)
  const admitted = (participants || []).filter((p) => p.status === ParticipantStatus.ADMITTED)

  return (
    <div className="space-y-3">
      <div>
        <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mb-2">
          Waiting Room ({waiting.length})
        </p>
        {waiting.length > 0 ? (
          <ul className="space-y-2" role="list">
            {waiting.map((p) => (
              <ParticipantRow
                key={p.id}
                participant={p}
                hostId={hostId}
                isHost={isHost}
                connectionStates={connectionStates}
                onAdmit={onAdmit}
                onReject={onReject}
                onRemove={onRemove}
                onMute={onMute}
                onUnmute={onUnmute}
                actionPending={actionPending}
              />
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground text-center py-4">No participants waiting.</p>
        )}
      </div>

      <div>
        <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mb-2">
          In Meeting ({admitted.length})
        </p>
        {admitted.length > 0 ? (
          <ul className="space-y-2" role="list" aria-label="Meeting participants">
            {admitted.map((p) => (
              <ParticipantRow
                key={p.id}
                participant={p}
                hostId={hostId}
                isHost={isHost}
                connectionStates={connectionStates}
                onAdmit={onAdmit}
                onReject={onReject}
                onRemove={onRemove}
                onMute={onMute}
                onUnmute={onUnmute}
                actionPending={actionPending}
              />
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground text-center py-4">No participants in meeting.</p>
        )}
      </div>
    </div>
  )
}

function ParticipantRow({
  participant: p,
  hostId,
  isHost,
  connectionStates,
  onAdmit,
  onReject,
  onRemove,
  onMute,
  onUnmute,
  actionPending,
}) {
  const isPHost = p.user_id === hostId
  const isGuest = p.participant_type === ParticipantType.GUEST
  const isWaiting = p.status === ParticipantStatus.WAITING
  const isLoading = actionPending === p.id

  const displayName = p.guest_name || p.user_name || p.user_id?.slice(0, 8) || "Unknown"
  const initials = displayName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)

  const connState = connectionStates?.[p.id]
  const isConnected =
    !connState || connState === "connected" || connState === "checking"

  return (
    <li
      key={p.id}
      className="flex items-center gap-3 px-3 py-2 rounded bg-muted/50"
      role="listitem"
    >
      <Avatar size="sm">
        <AvatarFallback>{initials}</AvatarFallback>
      </Avatar>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-medium truncate">
            {displayName}
          </span>
          {isPHost && (
            <span
              className="inline-flex items-center gap-0.5 text-[10px] text-yellow-600 dark:text-yellow-400"
              aria-label="Host"
            >
              <Crown weight="fill" className="size-3" />
              Host
            </span>
          )}
          {isGuest && !isPHost && (
            <span className="inline-flex items-center rounded px-1 py-0.5 text-[10px] bg-muted text-muted-foreground">
              Guest
            </span>
          )}
          {isWaiting && (
            <span className="inline-flex items-center rounded px-1 py-0.5 text-[10px] bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300">
              Waiting
            </span>
          )}
          {p.is_reconnecting && (
            <span className="inline-flex items-center rounded px-1 py-0.5 text-[10px] bg-orange-50 text-orange-700 dark:bg-orange-950 dark:text-orange-300">
              Reconnecting...
            </span>
          )}
          {p.is_muted && !isWaiting && (
            <MicrophoneSlash className="size-3 text-destructive" weight="fill" />
          )}
        </div>
      </div>

      <div className="flex items-center gap-1 shrink-0">
        {!isPHost && isHost && isWaiting && (
          <>
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={() => onAdmit?.(p.id)}
              disabled={!!isLoading}
              className="text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-950"
              aria-label="Admit participant"
            >
              {isLoading ? <SpinnerGap className="size-3.5 animate-spin" /> : <Check className="size-3.5" />}
            </Button>
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={() => onReject?.(p.id)}
              disabled={!!isLoading}
              className="text-destructive hover:text-destructive hover:bg-destructive/10"
              aria-label="Reject participant"
            >
              {isLoading ? <SpinnerGap className="size-3.5 animate-spin" /> : <X className="size-3.5" />}
            </Button>
          </>
        )}

        {!isPHost && isHost && !isWaiting && (
          <>
            {p.is_muted ? (
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={() => onUnmute?.(p.id)}
                disabled={!!isLoading}
                aria-label="Unmute participant"
              >
                {isLoading ? <SpinnerGap className="size-3.5 animate-spin" /> : <Microphone className="size-3.5" />}
              </Button>
            ) : (
              <Button
                variant="ghost"
                size="icon-xs"
                onClick={() => onMute?.(p.id)}
                disabled={!!isLoading}
                aria-label="Mute participant"
              >
                {isLoading ? <SpinnerGap className="size-3.5 animate-spin" /> : <MicrophoneSlash className="size-3.5" />}
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon-xs"
              onClick={() => onRemove?.(p.id)}
              disabled={!!isLoading}
              className="text-destructive hover:text-destructive hover:bg-destructive/10"
              aria-label="Remove participant"
            >
              {isLoading ? <SpinnerGap className="size-3.5 animate-spin" /> : <Prohibit className="size-3.5" />}
            </Button>
          </>
        )}
      </div>

      {!isWaiting && (
        <div className="flex items-center gap-1.5">
          <span
            className={`size-2 rounded-full ${isConnected ? "bg-green-500" : "bg-gray-400"}`}
            aria-label={isConnected ? "Connected" : "Disconnected"}
          />
          <span className="text-[10px] text-muted-foreground hidden sm:inline">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
      )}
    </li>
  )
}
