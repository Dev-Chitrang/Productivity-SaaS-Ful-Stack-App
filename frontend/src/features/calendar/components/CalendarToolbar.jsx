import { ChevronLeft, ChevronRight, Plus, SlidersHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ViewSwitcher } from "./ViewSwitcher"
import { SearchBar } from "./SearchBar"
import { cn } from "@/lib/utils"
import { fmtMonthYear, fmtWeekRange, fmtShortDate, dayjs } from "../utils/dateUtils"

/**
 * @param {Object} props
 * @param {"month"|"week"|"day"|"agenda"} props.view
 * @param {(v: string) => void} props.onViewChange
 * @param {string} props.anchorDate        - ISO date
 * @param {() => void} props.onPrev
 * @param {() => void} props.onNext
 * @param {() => void} props.onToday
 * @param {string} props.search
 * @param {(s: string) => void} props.onSearchChange
 * @param {boolean} props.filterOpen
 * @param {() => void} props.onToggleFilter
 * @param {boolean} props.hasActiveFilters
 * @param {() => void} props.onCreateEvent
 */
export function CalendarToolbar({
    view,
    onViewChange,
    anchorDate,
    onPrev,
    onNext,
    onToday,
    search,
    onSearchChange,
    filterOpen,
    onToggleFilter,
    hasActiveFilters,
    onCreateEvent,
}) {
    const periodLabel = {
        month: fmtMonthYear(anchorDate),
        week: fmtWeekRange(anchorDate),
        day: fmtShortDate(anchorDate),
        agenda: fmtMonthYear(anchorDate),
    }[view]

    return (
        <div className="border-b border-border bg-background">
            {/* top row */}
            <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5">
                {/* left: nav */}
                <div className="flex items-center gap-1">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={onToday}
                        aria-label="Go to today"
                    >
                        Today
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={onPrev}
                        aria-label="Previous period"
                    >
                        <ChevronLeft className="size-4" />
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={onNext}
                        aria-label="Next period"
                    >
                        <ChevronRight className="size-4" />
                    </Button>
                    <span className="ml-1 text-sm font-semibold tracking-tight select-none min-w-[160px]">
                        {periodLabel}
                    </span>
                </div>

                {/* right: search + filter + create */}
                <div className="flex items-center gap-2">
                    <SearchBar
                        value={search}
                        onChange={onSearchChange}
                        className="hidden sm:flex"
                    />
                    <Button
                        variant="outline"
                        size="icon-sm"
                        onClick={onToggleFilter}
                        aria-label="Toggle filters"
                        aria-pressed={filterOpen}
                        className={cn(hasActiveFilters && "border-primary text-primary")}
                    >
                        <SlidersHorizontal className="size-3.5" />
                    </Button>
                    <Button size="sm" onClick={onCreateEvent} aria-label="Create new event">
                        <Plus className="size-3.5" />
                        <span className="hidden sm:inline">Create</span>
                    </Button>
                    <ViewSwitcher view={view} onViewChange={onViewChange} />
                </div>
            </div>

            {/* mobile search row */}
            <div className="sm:hidden px-4 pb-2.5">
                <SearchBar value={search} onChange={onSearchChange} className="w-full" />
            </div>
        </div>
    )
}
