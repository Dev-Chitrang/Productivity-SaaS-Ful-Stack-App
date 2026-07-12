/**
 * TimezoneField
 *
 * Reusable timezone UI used in forms and settings.
 *
 * Default state: shows "Timezone  Asia/Kolkata  Change"
 * After clicking Change: shows a searchable <select> + "Done" button.
 *
 * Props:
 *   value      {string}           - current IANA timezone value
 *   onChange   {(tz: string)=>void}
 *   label      {string}           - optional, defaults to "Timezone"
 *   className  {string}           - optional wrapper class
 */

import { useState, useMemo } from "react"
import { Globe } from "lucide-react"
import { Button } from "@/components/ui/button"
import { COMMON_TIMEZONES } from "@/lib/timezone"

export function TimezoneField({ value, onChange, label = "Timezone", className = "" }) {
    const [editing, setEditing] = useState(false)
    const [search, setSearch] = useState("")

    const filtered = useMemo(() => {
        const q = search.trim().toLowerCase()
        if (!q) return COMMON_TIMEZONES
        return COMMON_TIMEZONES.filter((tz) => tz.toLowerCase().includes(q))
    }, [search])

    function handleSelect(tz) {
        onChange(tz)
        setEditing(false)
        setSearch("")
    }

    if (!editing) {
        return (
            <div className={`flex items-center gap-2 text-sm ${className}`}>
                <Globe className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
                <span className="text-xs text-muted-foreground font-medium">{label}</span>
                <span className="text-xs font-mono text-foreground">{value || "UTC"}</span>
                <button
                    type="button"
                    onClick={() => setEditing(true)}
                    className="text-xs text-primary underline underline-offset-2 hover:text-primary/80 transition-colors ml-1"
                    aria-label={`Change ${label}`}
                >
                    Change
                </button>
            </div>
        )
    }

    return (
        <div className={`space-y-1.5 ${className}`}>
            <div className="flex items-center gap-2">
                <Globe className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
                <span className="text-xs font-medium text-muted-foreground">{label}</span>
            </div>

            {/* Search input */}
            <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search timezone..."
                autoFocus
                className="h-7 w-full border border-input bg-background px-2 text-xs outline-none focus-visible:border-ring placeholder:text-muted-foreground"
                aria-label="Search timezones"
            />

            {/* Scrollable list */}
            <div
                role="listbox"
                aria-label="Select timezone"
                className="max-h-44 overflow-y-auto border border-input bg-background"
            >
                {filtered.length === 0 ? (
                    <p className="px-2 py-3 text-center text-xs text-muted-foreground">No results</p>
                ) : (
                    filtered.map((tz) => (
                        <button
                            key={tz}
                            type="button"
                            role="option"
                            aria-selected={tz === value}
                            onClick={() => handleSelect(tz)}
                            className={`w-full px-3 py-1.5 text-left text-xs transition-colors hover:bg-accent hover:text-accent-foreground ${tz === value ? "bg-primary/10 text-primary font-medium" : "text-foreground"
                                }`}
                        >
                            {tz}
                        </button>
                    ))
                )}
            </div>

            <div className="flex gap-2">
                <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs"
                    onClick={() => { setEditing(false); setSearch("") }}
                >
                    Cancel
                </Button>
            </div>
        </div>
    )
}
