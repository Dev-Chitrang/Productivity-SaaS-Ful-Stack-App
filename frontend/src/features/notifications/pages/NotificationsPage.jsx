import { useState } from "react"
import { Search, CheckCheck, Bell, Video } from "lucide-react"
import { useNotifications, useMarkAsRead, useMarkAllAsRead } from "../hooks/useNotificationsApi"
import NotificationCard from "../components/NotificationCard"
import { cn } from "@/lib/utils"

const TYPE_FILTERS = [
  { label: "All", value: null },
  { label: "Meeting Reminders", value: "MEETING_REMINDER" },
]

function NotificationsPage() {
  const [search, setSearch] = useState("")
  const [typeFilter, setTypeFilter] = useState(null)
  const [page, setPage] = useState(1)

  const { data, isLoading } = useNotifications({
    search: search || undefined,
    type: typeFilter || undefined,
    page,
    page_size: 20,
  })

  const markAll = useMarkAllAsRead()
  const items = data?.items || []
  const total = data?.total || 0
  const totalPages = Math.ceil(total / 20)

  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 py-6 sm:py-8 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-foreground">Notifications</h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {total} notification{total !== 1 ? "s" : ""}
          </p>
        </div>
        <button
          type="button"
          onClick={() => markAll.mutate()}
          className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors"
        >
          <CheckCheck className="size-3.5" />
          Mark all read
        </button>
      </div>

      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search notifications..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
            className="w-full h-8 pl-8 pr-3 text-xs bg-muted/50 border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring text-foreground placeholder:text-muted-foreground"
          />
        </div>
        <div className="flex items-center gap-1">
          {TYPE_FILTERS.map((f) => (
            <button
              key={f.label}
              type="button"
              onClick={() => {
                setTypeFilter(f.value)
                setPage(1)
              }}
              className={cn(
                "px-2.5 py-1 text-[10px] font-medium rounded-md transition-colors",
                typeFilter === f.value
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="border border-border rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <span className="text-xs text-muted-foreground">Loading notifications...</span>
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-4">
            <Bell className="size-8 text-muted-foreground/30 mb-2" />
            <span className="text-xs text-muted-foreground">
              {search ? "No notifications match your search" : "No notifications yet"}
            </span>
          </div>
        ) : (
          <div>
            {items.map((n) => (
              <NotificationCard key={n.id} notification={n} />
            ))}
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="px-2.5 py-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-40 disabled:cursor-not-allowed rounded-md hover:bg-muted transition-colors"
          >
            Previous
          </button>
          <span className="text-xs text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="px-2.5 py-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-40 disabled:cursor-not-allowed rounded-md hover:bg-muted transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}

export default NotificationsPage
