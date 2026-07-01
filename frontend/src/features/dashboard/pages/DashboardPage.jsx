import { useNotesAnalytics, useTasksAnalytics, useCalendarAnalytics } from "../hooks/useDashboardApi"
import { TodayOverview } from "../components/TodayOverview"
import { CalendarAnalytics } from "../components/CalendarAnalytics"
import { NotesAnalytics } from "../components/NotesAnalytics"
import { TasksAnalytics } from "../components/TasksAnalytics"

function DashboardPage() {
    const { data: notesData, isLoading: notesLoading } = useNotesAnalytics()
    const { data: tasksData, isLoading: tasksLoading } = useTasksAnalytics()
    const { data: calendarData, isLoading: calendarLoading } = useCalendarAnalytics()

    const overviewLoading = notesLoading || tasksLoading || calendarLoading

    return (
        <div className="mx-auto max-w-6xl px-6 py-8 space-y-8">
            <div className="flex flex-col gap-1">
                <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
                <p className="text-sm text-muted-foreground">
                    Welcome to your workspace.
                </p>
            </div>

            <section>
                <h2 className="text-sm font-semibold tracking-tight mb-3">Today's Overview</h2>
                <TodayOverview
                    calendarData={calendarData}
                    tasksData={tasksData}
                    notesData={notesData}
                    loading={overviewLoading}
                />
            </section>

            <hr className="border-border" />

            <CalendarAnalytics data={calendarData} loading={calendarLoading} />

            <hr className="border-border" />

            <NotesAnalytics data={notesData} loading={notesLoading} />

            <hr className="border-border" />

            <TasksAnalytics data={tasksData} loading={tasksLoading} />
        </div>
    )
}

export default DashboardPage
