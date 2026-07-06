import { useNavigate } from "react-router-dom"
import { useAuthContext } from "@/context/AuthContext"
import { CalendarPlus, FileText, ClipboardList, Presentation, PenSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useEffect, useState } from "react"

function useCurrentTime() {
    const [time, setTime] = useState(new Date())
    useEffect(() => {
        const id = setInterval(() => setTime(new Date()), 30_000)
        return () => clearInterval(id)
    }, [])
    return time
}

function getGreeting(hour) {
    if (hour < 12) return "Good morning"
    if (hour < 17) return "Good afternoon"
    return "Good evening"
}

function formatDate(date) {
    return date.toLocaleDateString(undefined, {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
    })
}

function formatTime(date) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}

const quickActions = [
    { label: "New Task", icon: ClipboardList, route: "/tasks", color: "text-blue-600 dark:text-blue-400" },
    { label: "New Meeting", icon: Presentation, route: "/meetings", color: "text-violet-600 dark:text-violet-400" },
    { label: "New Event", icon: CalendarPlus, route: "/calendar", color: "text-emerald-600 dark:text-emerald-400" },
    { label: "New Note", icon: FileText, route: "/notes", color: "text-amber-600 dark:text-amber-400" },
    { label: "New Board", icon: PenSquare, route: "/whiteboards", color: "text-rose-600 dark:text-rose-400" },
]

export function WelcomeSection() {
    const { user } = useAuthContext()
    const navigate = useNavigate()
    const now = useCurrentTime()
    const greeting = getGreeting(now.getHours())
    const name = user?.full_name?.split(" ")[0] || "there"

    return (
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-0.5">
                <h1 className="text-xl font-semibold tracking-tight">
                    {greeting}, {name}.
                </h1>
                <p className="text-sm text-muted-foreground">
                    {formatDate(now)} &middot; {formatTime(now)}
                </p>
            </div>
            <div className="flex flex-wrap gap-1.5">
                {quickActions.map((action) => (
                    <Button
                        key={action.label}
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(action.route)}
                        className="gap-1.5 text-xs h-7 px-2.5"
                    >
                        <action.icon className={`size-3.5 ${action.color}`} />
                        {action.label}
                    </Button>
                ))}
            </div>
        </div>
    )
}
