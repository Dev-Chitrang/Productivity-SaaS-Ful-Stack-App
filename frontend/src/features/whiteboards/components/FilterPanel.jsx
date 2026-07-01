import { Star, Archive, Trash2, LayoutTemplate } from "lucide-react"
import { cn } from "@/lib/utils"

const FILTERS = [
    { key: "all", label: "All", icon: LayoutTemplate },
    { key: "favorite", label: "Favorites", icon: Star },
    { key: "archived", label: "Archived", icon: Archive },
    { key: "deleted", label: "Deleted", icon: Trash2 },
]

export function WhiteboardFilterPanel({ activeFilter, onChange }) {
    return (
        <div className="flex gap-1 px-3 py-2 border-b border-border">
            {FILTERS.map(({ key, label, icon: Icon }) => (
                <button
                    key={key}
                    type="button"
                    onClick={() => onChange(key)}
                    className={cn(
                        "flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-sm transition-colors",
                        activeFilter === key
                            ? "bg-primary/10 text-primary"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted",
                    )}
                >
                    <Icon className={cn("size-3.5", key === "favorite" && activeFilter === key && "fill-current")} />
                    {label}
                </button>
            ))}
        </div>
    )
}
