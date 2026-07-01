import { CheckSquare, Clock, AlertCircle, CalendarPlus } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"
import { AnalyticsCard } from "./AnalyticsCard"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const CHART_COLORS = ["var(--color-chart-1)", "var(--color-chart-2)", "var(--color-chart-3)"]

export function TasksAnalytics({ data, loading }) {
    if (loading) {
        return (
            <div className="space-y-4">
                <h2 className="text-sm font-semibold tracking-tight">Tasks Analytics</h2>
                <div className="text-xs text-muted-foreground">Loading...</div>
            </div>
        )
    }

    const priorityData = [
        { name: "Low", value: data?.priority_distribution?.LOW || 0 },
        { name: "Medium", value: data?.priority_distribution?.MEDIUM || 0 },
        { name: "High", value: data?.priority_distribution?.HIGH || 0 },
    ].filter((d) => d.value > 0)

    const statusData = [
        { name: "Todo", value: data?.status_distribution?.TODO || 0 },
        { name: "In Progress", value: data?.status_distribution?.["IN PROGRESS"] || 0 },
        { name: "Done", value: data?.status_distribution?.DONE || 0 },
    ].filter((d) => d.value > 0)

    return (
        <div className="space-y-4">
            <h2 className="text-sm font-semibold tracking-tight">Tasks Analytics</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <AnalyticsCard icon={CheckSquare} title="Total Tasks" value={data?.total} />
                <AnalyticsCard icon={Clock} title="Today's Tasks" value={data?.today} />
                <AnalyticsCard icon={AlertCircle} title="Overdue Tasks" value={data?.overdue} />
                <AnalyticsCard icon={CalendarPlus} title="Upcoming Tasks" value={data?.upcoming} />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card size="sm">
                    <CardHeader>
                        <CardTitle className="text-xs">Priority Distribution</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {priorityData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={priorityData}>
                                    <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                                    <YAxis tick={{ fontSize: 10 }} />
                                    <Tooltip contentStyle={{ fontSize: 11 }} />
                                    <Bar dataKey="value" fill="var(--color-chart-1)" radius={[2, 2, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="text-xs text-muted-foreground py-8 text-center">No data</div>
                        )}
                    </CardContent>
                </Card>
                <Card size="sm">
                    <CardHeader>
                        <CardTitle className="text-xs">Status Distribution</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {statusData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={statusData}>
                                    <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                                    <YAxis tick={{ fontSize: 10 }} />
                                    <Tooltip contentStyle={{ fontSize: 11 }} />
                                    <Bar dataKey="value" fill="var(--color-chart-2)" radius={[2, 2, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="text-xs text-muted-foreground py-8 text-center">No data</div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
