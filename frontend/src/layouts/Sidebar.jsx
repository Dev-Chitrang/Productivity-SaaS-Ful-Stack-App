import { NavLink } from "react-router-dom"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Calendar,
  FileText,
  CheckSquare,
  Video,
  PenSquare,
  Settings,
  X,
  ChevronLeft,
} from "lucide-react"
import { useSidebar } from "@/context/SidebarContext"
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip"

const navItems = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/calendar", icon: Calendar, label: "Calendar" },
  { to: "/notes", icon: FileText, label: "Notes" },
  { to: "/tasks", icon: CheckSquare, label: "Tasks" },
  { to: "/meetings", icon: Video, label: "Meetings" },
  { to: "/whiteboards", icon: PenSquare, label: "Whiteboards" },
  { to: "/settings", icon: Settings, label: "Settings" },
]

const navClass = ({ isActive }) =>
  cn(
    "flex items-center gap-3 px-3 py-2 text-xs font-medium rounded-md transition-colors",
    isActive
      ? "bg-primary/10 text-primary"
      : "text-muted-foreground hover:text-foreground hover:bg-muted",
  )

function SidebarNavItem({ to, icon: Icon, label, collapsed }) {
  const link = (
    <NavLink to={to} end className={navClass}>
      <Icon className="size-4 shrink-0" />
      {!collapsed && label}
    </NavLink>
  )

  if (!collapsed) return link

  return (
    <Tooltip>
      <TooltipTrigger asChild>{link}</TooltipTrigger>
      <TooltipContent side="right" sideOffset={8}>
        {label}
      </TooltipContent>
    </Tooltip>
  )
}

function SidebarNav({ collapsed }) {
  return (
    <nav className="flex flex-col gap-0.5 px-3 py-4">
      {navItems.map((item) =>
        item.disabled ? (
          <span
            key={item.to}
            className="flex items-center gap-3 px-3 py-2 text-xs font-medium text-muted-foreground/40 rounded-md cursor-not-allowed"
          >
            <item.icon className="size-4 shrink-0" />
            {!collapsed && item.label}
          </span>
        ) : (
          <SidebarNavItem
            key={item.to}
            to={item.to}
            icon={item.icon}
            label={item.label}
            collapsed={collapsed}
          />
        ),
      )}
      {collapsed && <div className="mt-4" />}
    </nav>
  )
}

export function Sidebar() {
  const { collapsed, toggleSidebar } = useSidebar()

  return (
    <aside
      className={cn(
        "hidden lg:flex lg:flex-col shrink-0 border-r border-border bg-card overflow-y-auto transition-[width] duration-200 ease-in-out",
        collapsed ? "w-16" : "w-60",
      )}
    >
      <div className="flex h-14 items-center gap-2 px-3 border-b border-border shrink-0">
        <div className="flex-1 flex items-center gap-2">
          {collapsed ? (
            <span className="text-sm font-semibold tracking-tight text-foreground shrink-0 px-1">
              UW
            </span>
          ) : (
            <span className="text-sm font-semibold tracking-tight text-foreground px-1">
              Unified Workspace
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={toggleSidebar}
          className="flex items-center justify-center size-6 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors shrink-0"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeft
            className={cn(
              "size-4 transition-transform duration-200",
              collapsed && "rotate-180",
            )}
          />
        </button>
      </div>
      <SidebarNav collapsed={collapsed} />
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
        <SidebarNav collapsed={false} />
      </div>
    </div>
  )
}
