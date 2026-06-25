import DashboardHeader from "../components/DashboardHeader"

function DashboardPage() {
  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader />
      <main className="mx-auto max-w-6xl px-6 py-12">
        <div className="flex flex-col gap-2">
          <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Welcome to your workspace.
          </p>
        </div>
      </main>
    </div>
  )
}

export default DashboardPage
