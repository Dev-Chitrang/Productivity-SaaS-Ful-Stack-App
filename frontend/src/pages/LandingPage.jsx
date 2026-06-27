import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import {
  Video,
  FileText,
  CheckSquare,
  Calendar,
  Bell,
  ScrollText,
  ArrowRight,
  ArrowUpRight,
  Split,
} from "lucide-react"
import { Link } from "react-router-dom"
import { ThemeToggle } from "@/components/ThemeToggle"

const features = [
  {
    icon: Video,
    title: "Meetings",
    desc: "Schedule, join, and manage meetings with auto-generated summaries and action items.",
  },
  {
    icon: FileText,
    title: "Notes",
    desc: "Write and organize notes that stay in sync with your meetings and tasks.",
  },
  {
    icon: CheckSquare,
    title: "Tasks",
    desc: "Track tasks from creation to completion with priorities and due dates.",
  },
  {
    icon: Calendar,
    title: "Calendar",
    desc: "A unified calendar that merges meetings, deadlines, and reminders in one view.",
  },
  {
    icon: Bell,
    title: "Reminders",
    desc: "Never miss a beat with smart reminders that adapt to your workflow.",
  },
  {
    icon: ScrollText,
    title: "Transcripts",
    desc: "Searchable transcripts for every meeting, linked to notes and action items.",
  },
]

const relationships = [
  {
    from: "Meeting",
    to: "Notes",
    desc: "Meeting summaries automatically become notes.",
  },
  {
    from: "Meeting",
    to: "Tasks",
    desc: "Action items from meetings become tasks.",
  },
  {
    from: "Task",
    to: "Reminder",
    desc: "Overdue tasks trigger reminders.",
  },
]

function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <span className="text-sm font-semibold tracking-tight">
            Unified Workspace
          </span>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Button variant="outline" asChild>
              <Link to="/auth?mode=login">Log in</Link>
            </Button>
            <Button asChild>
              <Link to="/auth?mode=signup">Get Started</Link>
            </Button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 pt-24 pb-16 md:pt-32 md:pb-24">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <div className="flex flex-col gap-8">
            <div className="flex flex-col gap-4">
              <h1 className="text-3xl leading-tight font-semibold tracking-tight md:text-5xl md:leading-tight">
                Everything you need to organize your work, meetings and notes.
              </h1>
              <p className="max-w-md text-sm leading-relaxed text-muted-foreground md:text-base">
                Meetings, notes, tasks, reminders and calendar events in one
                workspace.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button size="lg" asChild>
<Link to="/auth?mode=signup">
                Get Started
                <ArrowRight className="size-3.5" />
              </Link>
            </Button>
            <Button variant="outline" size="lg">
                <svg viewBox="0 0 16 16" className="size-3.5" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" /></svg>
                GitHub
              </Button>
            </div>
          </div>

          <div className="relative hidden aspect-[4/3] overflow-hidden rounded-none border border-border bg-gradient-to-br from-indigo-500/5 to-indigo-500/10 lg:block">
            <div className="absolute inset-0 flex items-center justify-center p-8">
              <div className="grid w-full max-w-sm grid-cols-2 gap-3">
                {[
                  { label: "Meetings", color: "bg-indigo-500/20" },
                  { label: "Notes", color: "bg-indigo-500/15" },
                  { label: "Tasks", color: "bg-indigo-500/20" },
                  { label: "Calendar", color: "bg-indigo-500/15" },
                ].map((item) => (
                  <div
                    key={item.label}
                    className={`flex items-center justify-center rounded-none border border-border p-4 text-xs font-medium ${item.color}`}
                  >
                    {item.label}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-border py-16 md:py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-12 flex flex-col gap-3">
            <h2 className="text-xl font-semibold tracking-tight md:text-2xl">
              Everything in one place
            </h2>
            <p className="max-w-lg text-sm text-muted-foreground">
              Six core tools that work together — or on their own.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => {
              const Icon = feature.icon
              return (
                <Card key={feature.title} size="sm">
                  <CardHeader>
                    <Icon className="size-4 text-primary" />
                    <CardTitle>{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription>{feature.desc}</CardDescription>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      </section>

      <section className="border-t border-border py-16 md:py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-12 flex flex-col gap-3">
            <h2 className="text-xl font-semibold tracking-tight md:text-2xl">
              Why Unified Workspace
            </h2>
            <p className="max-w-lg text-sm text-muted-foreground">
              Connections are powerful, but not required.
            </p>
          </div>

          <div className="mb-10">
            <p className="text-sm font-medium text-muted-foreground">
              <span className="text-foreground">Relationships are optional.</span>{" "}
              Connect tools when it helps; use them standalone when it doesn&apos;t.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {relationships.map((rel) => (
              <Card key={`${rel.from}-${rel.to}`} size="sm">
                <CardHeader>
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <span>{rel.from}</span>
                    <ArrowRight className="size-3.5 text-primary" />
                    <span>{rel.to}</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <CardDescription>{rel.desc}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="mt-6">
            <Card size="sm" className="border-dashed">
              <CardHeader>
                <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <Split className="size-3.5" />
                  <span>Notes</span>
                  <span className="text-xs text-muted-foreground">
                    can exist independently
                  </span>
                </div>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      <section className="border-t border-border bg-primary/5 py-16 md:py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto flex max-w-2xl flex-col items-center gap-6 text-center">
            <h2 className="text-xl font-semibold tracking-tight md:text-3xl">
              Reduce context switching.
            </h2>
            <p className="max-w-md text-sm leading-relaxed text-muted-foreground">
              Stop jumping between apps. Bring your workflow into a single,
              focused workspace.
            </p>
            <Button size="lg" asChild>
              <Link to="/auth?mode=signup">
                Get Started
                <ArrowRight className="size-3.5" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6">
          <span className="text-xs text-muted-foreground">
            Unified Workspace
          </span>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
            >
              <svg viewBox="0 0 16 16" className="size-3.5" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" /></svg>
              GitHub
              <ArrowUpRight className="size-2.5" />
            </a>
            <a
              href="https://linkedin.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
            >
              <svg viewBox="0 0 16 16" className="size-3.5" fill="currentColor"><path d="M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708c0 .633-.526 1.146-1.175 1.146H1.175C.526 16 0 15.487 0 14.854V1.146zm4.943 12.248V6.169H2.542v7.225h2.401zm-1.2-8.212c.837 0 1.358-.554 1.358-1.248-.015-.709-.52-1.248-1.342-1.248-.822 0-1.359.54-1.359 1.248 0 .694.521 1.248 1.327 1.248h.016zm4.908 8.212V9.359c0-.216.016-.432.08-.586.173-.431.568-.878 1.232-.878.869 0 1.216.662 1.216 1.634v3.865h2.401V9.25c0-2.22-1.184-3.252-2.764-3.252-1.274 0-1.845.7-2.165 1.193v.025h-.016a5.54 5.54 0 01.016-.025V6.169h-2.4c.03.678 0 7.225 0 7.225h2.4z" /></svg>
              LinkedIn
              <ArrowUpRight className="size-2.5" />
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
