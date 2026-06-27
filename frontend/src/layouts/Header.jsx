import { Menu } from "lucide-react"
import { ThemeToggle } from "@/components/ThemeToggle"
import UserNav from "@/features/dashboard/components/UserNav"

export function Header({ onMenuClick }) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-background px-4">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="flex items-center justify-center size-8 -ml-1 text-muted-foreground hover:text-foreground transition-colors lg:hidden"
          aria-label="Open sidebar"
        >
          <Menu className="size-4" />
        </button>
        <span className="text-sm font-semibold tracking-tight text-foreground lg:hidden">
          Unified Workspace
        </span>
      </div>
      <div className="flex items-center gap-1">
        <ThemeToggle />
        <UserNav />
      </div>
    </header>
  )
}
