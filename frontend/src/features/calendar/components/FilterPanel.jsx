import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { COLOR_SWATCHES } from "../utils/colorUtils"

/**
 * Event type values match the backend EventType enum.
 * Color values match the backend EventColor enum.
 */
const FILTER_EVENT_TYPES = [
    { label: "Personal", value: "PERSONAL" },
    { label: "Meeting", value: "MEETING" },
    { label: "Reminder", value: "REMINDER" },
]

const FILTER_COLORS = [
    { label: "Red", value: "RED" },
    { label: "Blue", value: "BLUE" },
    { label: "Green", value: "GREEN" },
    { label: "Yellow", value: "YELLOW" },
    { label: "Purple", value: "PURPLE" },
    { label: "Orange", value: "ORANGE" },
    { label: "Gray", value: "GRAY" },
]

// Map backend color enum values to hex swatches for the picker
const COLOR_HEX = {
    RED: "#ef4444",
    BLUE: "#3b82f6",
    GREEN: "#10b981",
    YELLOW: "#f59e0b",
    PURPLE: "#a855f7",
    ORANGE: "#f97316",
    GRAY: "#6b7280",
}

/**
 * @typedef {Object} CalendarFilters
 * @property {string} [event_type]   - Matches backend EventType enum (e.g. "MEETING")
 * @property {string} [color]        - Matches backend EventColor enum (e.g. "BLUE")
 */

/**
 * @param {Object} props
 * @param {CalendarFilters} props.filters
 * @param {(f: CalendarFilters) => void} props.onChange
 * @param {() => void} props.onClose
 */
export function FilterPanel({ filters, onChange, onClose }) {
    const set = (key, val) =>
        onChange({ ...filters, [key]: val === filters[key] ? undefined : val })

    const hasFilters = !!filters.event_type || !!filters.color

    return (
        <div className="border border-border bg-card p-4 space-y-4 w-60 shadow-sm">
            {/* Header */}
            <div className="flex items-center justify-between">
                <span className="text-xs font-semibold tracking-tight">Filters</span>
                <div className="flex items-center gap-1">
                    {hasFilters && (
                        <button
                            type="button"
                            onClick={() => onChange({})}
                            className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                        >
                            Clear all
                        </button>
                    )}
                    <Button size="icon-xs" variant="ghost" onClick={onClose} aria-label="Close filters">
                        <X className="size-3.5" />
                    </Button>
                </div>
            </div>

            {/* Event type */}
            <div className="space-y-1.5">
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                    Type
                </p>
                <div className="flex flex-wrap gap-1">
                    {FILTER_EVENT_TYPES.map(({ label, value }) => (
                        <button
                            key={value}
                            type="button"
                            onClick={() => set("event_type", value)}
                            className={cn(
                                "px-2 py-0.5 text-[10px] border transition-colors",
                                filters.event_type === value
                                    ? "bg-primary text-primary-foreground border-primary"
                                    : "border-border text-muted-foreground hover:border-foreground hover:text-foreground",
                            )}
                        >
                            {label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Color */}
            <div className="space-y-1.5">
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                    Color
                </p>
                <div className="flex flex-wrap gap-1.5">
                    {FILTER_COLORS.map(({ label, value }) => (
                        <button
                            key={value}
                            type="button"
                            onClick={() => set("color", value)}
                            aria-label={`Filter by ${label}`}
                            className={cn(
                                "size-5 rounded-full transition-transform",
                                filters.color === value
                                    ? "ring-2 ring-offset-1 ring-foreground scale-110"
                                    : "hover:scale-110",
                            )}
                            style={{ backgroundColor: COLOR_HEX[value] }}
                        />
                    ))}
                </div>
            </div>
        </div>
    )
}
