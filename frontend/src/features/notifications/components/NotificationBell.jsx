import { useState, useRef, useEffect } from "react"
import { Bell } from "lucide-react"
import { cn } from "@/lib/utils"
import { useUnreadCount } from "../hooks/useNotificationsApi"
import NotificationDropdown from "./NotificationDropdown"

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const { data: count = 0 } = useUnreadCount()

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside)
      return () => document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [open])

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="relative flex items-center justify-center size-8 text-muted-foreground hover:text-foreground transition-colors"
        aria-label="Notifications"
      >
        <Bell className="size-4" />
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center min-w-[16px] h-4 px-1 text-[10px] font-medium text-primary-foreground bg-primary rounded-full">
            {count > 99 ? "99+" : count}
          </span>
        )}
      </button>
      {open && (
        <NotificationDropdown onClose={() => setOpen(false)} />
      )}
    </div>
  )
}
