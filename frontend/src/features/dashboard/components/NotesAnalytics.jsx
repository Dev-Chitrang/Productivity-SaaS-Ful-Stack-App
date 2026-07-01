import { FileText, Heart, Archive } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"
import { AnalyticsCard } from "./AnalyticsCard"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const CHART_COLORS = ["var(--color-chart-1)", "var(--color-chart-2)", "var(--color-chart-3)"]

function formatMonth(iso) {
    if (!iso) return ""
    const d = new Date(iso)
    return d.toLocaleDateString([], { month: "short", year: "2-digit" })
}

export function NotesAnalytics({ data, loading }) {
    if (loading) {
        return (
            <div className="space-y-4">
                <h2 className="text-sm font-semibold tracking-tight">Notes Analytics</h2>
                <div className="text-xs text-muted-foreground">Loading...</div>
            </div>
        )
    }

    const monthlyData = (data?.monthly_created || []).map((d) => ({
        month: formatMonth(d.month),
        count: d.count,
    }))

    const pieData = [
        { name: "Favorite", value: data?.favorite || 0 },
        { name: "Normal", value: Math.max(0, (data?.total || 0) - (data?.favorite || 0)) },
    ].filter((d) => d.value > 0)

    return (
        <div className="space-y-4">
            <h2 className="text-sm font-semibold tracking-tight">Notes Analytics</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <AnalyticsCard icon={FileText} title="Total Notes" value={data?.total} />
                <AnalyticsCard icon={Heart} title="Favorite Notes" value={data?.favorite} />
                <AnalyticsCard icon={Archive} title="Archived Notes" value={data?.archived} />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card size="sm">
                    <CardHeader>
                        <CardTitle className="text-xs">Notes Created Over Time</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {monthlyData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={monthlyData}>
                                    <XAxis dataKey="month" tick={{ fontSize: 10 }} />
                                    <YAxis tick={{ fontSize: 10 }} />
                                    <Tooltip contentStyle={{ fontSize: 11 }} />
                                    <Bar dataKey="count" fill="var(--color-chart-2)" radius={[2, 2, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="text-xs text-muted-foreground py-8 text-center">No data</div>
                        )}
                    </CardContent>
                </Card>
                <Card size="sm">
                    <CardHeader>
                        <CardTitle className="text-xs">Favorite vs Normal Notes</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {pieData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={200}>
                                <PieChart>
                                    <Pie
                                        data={pieData}
                                        dataKey="value"
                                        nameKey="name"
                                        cx="50%"
                                        cy="50%"
                                        outerRadius={70}
                                        innerRadius={45}
                                    >
                                        {pieData.map((_, i) => (
                                            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ fontSize: 11 }} />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="text-xs text-muted-foreground py-8 text-center">No data</div>
                        )}
                        <div className="flex justify-center gap-4 text-xs text-muted-foreground mt-1">
                            {pieData.map((d, i) => (
                                <div key={d.name} className="flex items-center gap-1">
                                    <span className="size-2 rounded-full" style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }} />
                                    {d.name}: {d.value}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
