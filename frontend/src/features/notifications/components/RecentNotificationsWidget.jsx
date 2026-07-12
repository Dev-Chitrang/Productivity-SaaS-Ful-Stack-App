import { useNavigate } from "react-router-dom"
import { Bell, Video } from "lucide-react"
import { useRecentNotifications, useUnreadCount } from "../hooks/useNotificationsApi"
import { cn } from "@/lib/utils"
import dayjs from "dayjs"
import relativeTime from "dayjs/plugin/relativeTime"

dayjs.extend(relativeTime)

export default function RecentNotificationsWidget() {
  const navigate = useNavigate()
  const { data: notifications = [], isLoading } = useRecentNotifications()
  const { data: count = 0 } = useUnreadCount()

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-foreground">Recent Notifications</h3>
        {count > 0 && (
          <span className="px-1.5 py-0.5 text-[10px] font-medium bg-primary text-primary-foreground rounded-full">
            {count} unread
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-6">
          <span className="text-[10px] text-muted-foreground">Loading...</span>
        </div>
      ) : notifications.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-6">
          <Bell className="size-5 text-muted-foreground/30 mb-1" />
          <span className="text-[10px] text-muted-foreground">No notifications</span>
        </div>
      ) : (
        <div className="space-y-1">
          {notifications.slice(0, 5).map((n) => (
            <button
              key={n.id}
              type="button"
              onClick={() => {
                if (n.extra_data?.meeting_id) {
                  navigate(`/meetings/${n.extra_data.meeting_id}`)
                } else {
                  navigate("/notifications")
                }
              }}
              className={cn(
                "w-full flex items-start gap-2 px-2 py-1.5 rounded-md text-left hover:bg-muted/50 transition-colors",
                !n.is_read && "bg-primary/5"
              )}
            >
              <Video className={cn("size-3 mt-0.5 shrink-0", n.is_read ? "text-muted-foreground/50" : "text-primary")} />
              <div className="flex-1 min-w-0">
                <p className={cn("text-[10px] truncate", n.is_read ? "text-muted-foreground" : "text-foreground font-medium")}>
                  {n.title}
                </p>
                <p className="text-[9px] text-muted-foreground/70">
                  {dayjs(n.created_at).fromNow()}
                </p>
              </div>
              {!n.is_read && <span className="size-1 rounded-full bg-primary shrink-0 mt-1" />}
            </button>
          ))}
          <button
            type="button"
            onClick={() => navigate("/notifications")}
            className="w-full text-[10px] text-primary hover:underline pt-1 text-center"
          >
            View all
          </button>
        </div>
      )}
    </div>
  )
}
