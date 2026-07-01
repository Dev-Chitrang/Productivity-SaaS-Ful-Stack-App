import { useState, useEffect, useRef } from "react"
import { Search, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { SEARCH_DEBOUNCE } from "../constants"

export function WhiteboardSearchBar({ value, onChange, className }) {
    const [local, setLocal] = useState(value || "")
    const timer = useRef(null)

    useEffect(() => {
        if (timer.current) clearTimeout(timer.current)
        timer.current = setTimeout(() => {
            if (local !== value) onChange(local)
        }, SEARCH_DEBOUNCE)
        return () => clearTimeout(timer.current)
    }, [local, value, onChange])

    const handleClear = () => {
        setLocal("")
        if (timer.current) clearTimeout(timer.current)
        onChange("")
    }

    return (
        <div className={cn("relative flex items-center", className)}>
            <Search className="pointer-events-none absolute left-2.5 size-3.5 text-muted-foreground" />
            <input
                type="text"
                value={local}
                onChange={(e) => setLocal(e.target.value)}
                placeholder="Search whiteboards…"
                aria-label="Search whiteboards"
                className="h-8 w-full min-w-0 pl-8 pr-7 bg-background border border-input text-xs placeholder:text-muted-foreground outline-none focus-visible:border-ring focus-visible:ring-1 focus-visible:ring-ring/50"
            />
            {local && (
                <button
                    type="button"
                    onClick={handleClear}
                    aria-label="Clear search"
                    className="absolute right-2 text-muted-foreground hover:text-foreground"
                >
                    <X className="size-3.5" />
                </button>
            )}
        </div>
    )
}
