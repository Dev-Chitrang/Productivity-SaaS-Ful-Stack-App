import { cn } from "@/lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function AnalyticsCard({ icon: Icon, title, value, subtitle, trend }) {
    return (
        <Card size="sm">
            <CardHeader>
                <CardTitle className="flex items-center gap-1.5 text-xs">
                    {Icon && <Icon className="size-3.5 text-muted-foreground" />}
                    {title}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="text-lg font-semibold tracking-tight">{value ?? "-"}</div>
                {subtitle && (
                    <div className="text-xs text-muted-foreground mt-0.5">{subtitle}</div>
                )}
                {trend !== undefined && trend !== null && (
                    <div className={cn(
                        "text-xs mt-0.5",
                        trend > 0 ? "text-emerald-600" : trend < 0 ? "text-destructive" : "text-muted-foreground"
                    )}>
                        {trend > 0 ? "+" : ""}{trend} from last period
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
