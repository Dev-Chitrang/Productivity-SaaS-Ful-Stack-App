import { NavLink } from "react-router-dom"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Calendar,
  FileText,
  CheckSquare,
  Video,
  Users,
  Bell,
  Settings,
  X,
} from "lucide-react"

const navItems = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/calendar", icon: Calendar, label: "Calendar" },
  { to: "/notes", icon: FileText, label: "Notes" },
  { to: "/tasks", icon: CheckSquare, label: "Tasks" },
  { to: "/meetings", icon: Video, label: "Meetings", disabled: true },
  { to: "/participants", icon: Users, label: "Participants", disabled: true },
  { to: "/notifications", icon: Bell, label: "Notifications", disabled: true },
  { to: "/settings", icon: Settings, label: "Settings" },
]

const navClass = ({ isActive }) =>
  cn(
    "flex items-center gap-3 px-3 py-2 text-xs font-medium rounded-md transition-colors",
    isActive
      ? "bg-primary/10 text-primary"
      : "text-muted-foreground hover:text-foreground hover:bg-muted",
  )

function SidebarNav() {
  return (
    <nav className="flex flex-col gap-0.5 px-3 py-4">
      {navItems.map((item) =>
        item.disabled ? (
          <span
            key={item.to}
            className="flex items-center gap-3 px-3 py-2 text-xs font-medium text-muted-foreground/40 rounded-md cursor-not-allowed"
          >
            <item.icon className="size-4 shrink-0" />
            {item.label}
          </span>
        ) : (
          <NavLink key={item.to} to={item.to} end className={navClass}>
            <item.icon className="size-4 shrink-0" />
            {item.label}
          </NavLink>
        ),
      )}
    </nav>
  )
}

export function Sidebar() {
  return (
    <aside className="hidden lg:flex lg:flex-col w-60 shrink-0 border-r border-border bg-card overflow-y-auto">
      <div className="flex h-14 items-center px-4 border-b border-border">
        <span className="text-sm font-semibold tracking-tight text-foreground">
          Unified Workspace
        </span>
      </div>
      <SidebarNav />
    </aside>
  )
}

export function MobileSidebar({ open, onClose }) {
  return (
    <div
      data-state={open ? "open" : "closed"}
      className={cn(
        "fixed inset-0 z-50 lg:hidden",
        open ? "pointer-events-auto" : "pointer-events-none",
      )}
    >
      {open && (
        <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      )}
      <div
        className={cn(
          "relative flex w-60 flex-col bg-card border-r border-border h-full transition-transform duration-200",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-14 items-center justify-between px-4 border-b border-border">
          <span className="text-sm font-semibold tracking-tight text-foreground">
            Unified Workspace
          </span>
          <button
            type="button"
            onClick={onClose}
            className="flex items-center justify-center size-7 text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close sidebar"
          >
            <X className="size-4" />
          </button>
        </div>
        <SidebarNav />
      </div>
    </div>
  )
}
