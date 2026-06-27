import { Link } from "react-router-dom"
import UserNav from "./UserNav"

function DashboardHeader() {
  return (
    <header className="border-b border-border">
      <div className="mx-auto flex h-12 max-w-6xl items-center justify-between px-6">
        <div className="flex items-center gap-6">
          <span className="text-sm font-semibold tracking-tight">
            Unified Workspace
          </span>
          <nav className="flex items-center gap-1">
            <Link
              to="/dashboard"
              className="px-2.5 py-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Dashboard
            </Link>
            <Link
              to="/calendar"
              className="px-2.5 py-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Calendar
            </Link>
          </nav>
        </div>
        <UserNav />
      </div>
    </header>
  )
}

export default DashboardHeader
