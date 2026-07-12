import { useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { useMarkAsRead } from "../hooks/useNotificationsApi"
import { Video } from "lucide-react"
import dayjs from "dayjs"
import relativeTime from "dayjs/plugin/relativeTime"

const TYPE_ICONS = {
  MEETING_REMINDER: Video,
}

export default function NotificationCard({ notification, compact = false, onClose }) {
  const navigate = useNavigate()
  const markRead = useMarkAsRead()

  const Icon = TYPE_ICONS[notification.type] || Video

  const handleClick = () => {
    if (!notification.is_read) {
      markRead.mutate([notification.id])
    }
      onClose?.()
      if (notification.extra_data?.meeting_id) {
        navigate(`/meetings/${notification.extra_data.meeting_id}`)
    }
  }

  dayjs.extend(relativeTime)
  const timeAgo = dayjs(notification.created_at).fromNow()

  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        "w-full text-left px-3 py-2.5 border-b border-border last:border-0 hover:bg-muted/50 transition-colors",
        !notification.is_read && "bg-primary/5",
      )}
    >
      <div className="flex items-start gap-2">
        <div className={cn(
          "flex items-center justify-center size-7 rounded-md shrink-0 mt-0.5",
          notification.is_read ? "bg-muted" : "bg-primary/10"
        )}>
          <Icon className={cn("size-3.5", notification.is_read ? "text-muted-foreground" : "text-primary")} />
        </div>
        <div className="flex-1 min-w-0">
          <p className={cn(
            "text-xs leading-tight truncate",
            notification.is_read ? "text-muted-foreground" : "text-foreground font-medium"
          )}>
            {notification.title}
          </p>
          {!compact && (
            <p className="text-[10px] text-muted-foreground mt-0.5 line-clamp-2">
              {notification.body}
            </p>
          )}
          <p className="text-[10px] text-muted-foreground/70 mt-0.5">{timeAgo}</p>
        </div>
        {!notification.is_read && (
          <span className="size-1.5 rounded-full bg-primary shrink-0 mt-1.5" />
        )}
      </div>
    </button>
  )
}
