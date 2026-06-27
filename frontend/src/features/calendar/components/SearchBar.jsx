import { Search, X } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * @param {Object} props
 * @param {string} props.value
 * @param {(v: string) => void} props.onChange
 * @param {string} [props.className]
 */
export function SearchBar({ value, onChange, className }) {
    return (
        <div className={cn("relative flex items-center", className)}>
            <Search className="pointer-events-none absolute left-2.5 size-3.5 text-muted-foreground" />
            <input
                type="text"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder="Search events…"
                aria-label="Search events"
                className={cn(
                    "h-8 w-full min-w-[160px] pl-8 pr-7",
                    "bg-background border border-input text-xs",
                    "placeholder:text-muted-foreground",
                    "outline-none focus-visible:border-ring focus-visible:ring-1 focus-visible:ring-ring/50",
                )}
            />
            {value && (
                <button
                    type="button"
                    onClick={() => onChange("")}
                    aria-label="Clear search"
                    className="absolute right-2 text-muted-foreground hover:text-foreground"
                >
                    <X className="size-3.5" />
                </button>
            )}
        </div>
    )
}
