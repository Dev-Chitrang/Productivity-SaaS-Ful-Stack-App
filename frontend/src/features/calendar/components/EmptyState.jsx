import { CalendarDays } from "lucide-react"
import { Button } from "@/components/ui/button"

/**
 * @param {Object} props
 * @param {string} [props.title]
 * @param {string} [props.description]
 * @param {() => void} [props.onCreateEvent]
 */
export function EmptyState({
    title = "No events",
    description = "There are no events to display for this period.",
    onCreateEvent,
}) {
    return (
        <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
            <div className="flex size-12 items-center justify-center bg-muted mb-4">
                <CalendarDays className="size-5 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-foreground mb-1">{title}</p>
            <p className="text-xs text-muted-foreground max-w-xs mb-5">{description}</p>
            {onCreateEvent && (
                <Button size="sm" onClick={onCreateEvent}>
                    Create event
                </Button>
            )}
        </div>
    )
}
