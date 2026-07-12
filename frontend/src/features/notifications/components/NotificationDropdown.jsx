import { useNavigate } from "react-router-dom"
import { CheckCheck, Bell } from "lucide-react"
import { useRecentNotifications, useMarkAllAsRead } from "../hooks/useNotificationsApi"
import NotificationCard from "./NotificationCard"

export default function NotificationDropdown({ onClose }) {
  const navigate = useNavigate()
  const { data: notifications = [], isLoading } = useRecentNotifications()
  const markAll = useMarkAllAsRead()

  const handleViewAll = () => {
    onClose()
    navigate("/notifications")
  }

  return (
    <div className="absolute right-0 top-full mt-2 w-80 max-h-96 rounded-lg border border-border bg-popover shadow-lg z-50 flex flex-col">
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <span className="text-xs font-semibold text-foreground">Notifications</span>
        <button
          type="button"
          onClick={() => markAll.mutate()}
          className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
          title="Mark all as read"
        >
          <CheckCheck className="size-3" />
          Mark all read
        </button>
      </div>
      <div className="overflow-y-auto flex-1">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <span className="text-xs text-muted-foreground">Loading...</span>
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 px-4">
            <Bell className="size-6 text-muted-foreground/40 mb-2" />
            <span className="text-xs text-muted-foreground">No notifications yet</span>
          </div>
        ) : (
          notifications.map((n) => (
            <NotificationCard key={n.id} notification={n} compact onClose={onClose} />
          ))
        )}
      </div>
      {notifications.length > 0 && (
        <div className="border-t border-border px-3 py-2">
          <button
            type="button"
            onClick={handleViewAll}
            className="text-[10px] font-medium text-primary hover:underline w-full text-center"
          >
            View all notifications
          </button>
        </div>
      )}
    </div>
  )
}
