import { WelcomeSection } from "../components/WelcomeSection"
import { OverviewCards } from "../components/OverviewCards"
import { TodaysAgenda } from "../components/TodaysAgenda"
import { UpcomingMeetings } from "../components/UpcomingMeetings"
import { RecentTasks } from "../components/RecentTasks"
import { RecentNotes } from "../components/RecentNotes"
import { RecentWhiteboards } from "../components/RecentWhiteboards"
import { RecentAttachments } from "../components/RecentAttachments"
import { RecentAnalyses } from "../components/RecentAnalyses"
import { RecentActivity } from "../components/RecentActivity"

function DashboardPage() {
    return (
        <div className="mx-auto max-w-6xl px-4 sm:px-6 py-6 sm:py-8 space-y-6">
            {/* Top: greeting + quick actions */}
            <WelcomeSection />

            {/* Overview stat cards */}
            <OverviewCards />

            {/* Main content grid: agenda + meetings on left, activity feed on right */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div className="lg:col-span-2 space-y-4">
                    <TodaysAgenda />
                    <UpcomingMeetings />
                </div>
                <div className="space-y-4">
                    <RecentActivity />
                </div>
            </div>

            {/* Secondary content: tasks, notes, whiteboards, attachments */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <RecentTasks />
                <RecentNotes />
                <RecentWhiteboards />
                <RecentAttachments />
            </div>

            {/* AI analyses — full width */}
            <RecentAnalyses />
        </div>
    )
}

export default DashboardPage
