import { cn } from "@/lib/utils"

/** @type {Array<{ value: string, label: string }>} */
export const VIEWS = [
    { value: "month", label: "Month" },
    { value: "week", label: "Week" },
    { value: "day", label: "Day" },
    { value: "agenda", label: "Agenda" },
]

/**
 * @param {Object} props
 * @param {"month"|"week"|"day"|"agenda"} props.view
 * @param {(v: string) => void} props.onViewChange
 */
export function ViewSwitcher({ view, onViewChange }) {
    return (
        <div
            role="tablist"
            aria-label="Calendar view"
            className="flex border border-border bg-background"
        >
            {VIEWS.map((v) => (
                <button
                    key={v.value}
                    role="tab"
                    aria-selected={view === v.value}
                    type="button"
                    onClick={() => onViewChange(v.value)}
                    className={cn(
                        "px-3 h-8 text-xs font-medium transition-colors select-none",
                        "border-r border-border last:border-r-0",
                        "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                        view === v.value
                            ? "bg-primary text-primary-foreground"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    )}
                >
                    {v.label}
                </button>
            ))}
        </div>
    )
}
