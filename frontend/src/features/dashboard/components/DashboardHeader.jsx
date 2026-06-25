import UserNav from "./UserNav"

function DashboardHeader() {
  return (
    <header className="border-b border-border">
      <div className="mx-auto flex h-12 max-w-6xl items-center justify-between px-6">
        <span className="text-sm font-semibold tracking-tight">
          Unified Workspace
        </span>
        <UserNav />
      </div>
    </header>
  )
}

export default DashboardHeader
