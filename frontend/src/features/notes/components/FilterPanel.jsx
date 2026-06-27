import { useState, useMemo } from "react"
import { Star, Pin, Archive, Trash2, ChevronDown, ChevronRight, X, Circle } from "lucide-react"
import { cn } from "@/lib/utils"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export function FilterPanel({ filters, onChange, allCategories = [], onClose }) {
    const [newCategory, setNewCategory] = useState("")
    const [showAddCategory, setShowAddCategory] = useState(false)

    const quickFilters = [
        {
            key: "favorite",
            label: "Favorites",
            icon: Star,
            active: !!filters.favorite,
        },
        {
            key: "pinned",
            label: "Pinned",
            icon: Pin,
            active: !!filters.pinned,
        },
        {
            key: "archived",
            label: "Archived",
            icon: Archive,
            active: !!filters.archived,
        },
        {
            key: "deleted",
            label: "Trash",
            icon: Trash2,
            active: !!filters.deleted,
        },
    ]

    const handleQuickFilter = (key) => {
        const next = { ...filters }
        if (next[key]) {
            delete next[key]
        } else {
            next[key] = true
        }
        onChange(next)
    }

    const handleCategoryFilter = (cat) => {
        const next = { ...filters }
        if (next.category === cat) {
            delete next.category
        } else {
            next.category = cat
        }
        onChange(next)
    }

    const handleAddCategory = () => {
        const trimmed = newCategory.trim()
        if (!trimmed) return
        handleCategoryFilter(trimmed)
        setNewCategory("")
        setShowAddCategory(false)
    }

    const hasActiveFilters = useMemo(
        () => Object.values(filters).some(Boolean),
        [filters],
    )

    return (
        <div className="w-56 border-l border-border bg-card h-full overflow-y-auto">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
                <span className="text-xs font-medium text-foreground">Filters</span>
                <div className="flex items-center gap-1">
                    {hasActiveFilters && (
                        <Button
                            variant="ghost"
                            size="xs"
                            onClick={() => onChange({})}
                        >
                            Clear
                        </Button>
                    )}
                    <Button variant="ghost" size="icon-xs" onClick={onClose} aria-label="Close filters">
                        <X className="size-3" />
                    </Button>
                </div>
            </div>

            <div className="px-3 py-3 space-y-1">
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
                    Quick Filters
                </p>
                {quickFilters.map(({ key, label, icon: Icon, active }) => (
                    <button
                        key={key}
                        type="button"
                        onClick={() => handleQuickFilter(key)}
                        className={cn(
                            "flex items-center gap-2 w-full px-2 py-1.5 text-xs rounded-sm transition-colors",
                            active
                                ? "bg-primary/10 text-primary"
                                : "text-muted-foreground hover:text-foreground hover:bg-muted",
                        )}
                    >
                        <Icon className={cn("size-3.5", active && "fill-current")} />
                        {label}
                    </button>
                ))}
            </div>

            <Separator />

            <div className="px-3 py-3">
                <div className="flex items-center justify-between mb-1.5">
                    <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                        Categories
                    </p>
                    <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => setShowAddCategory(!showAddCategory)}
                        aria-label="Add category"
                    >
                        {showAddCategory ? <ChevronDown className="size-3" /> : <ChevronRight className="size-3" />}
                    </Button>
                </div>

                {showAddCategory && (
                    <div className="flex gap-1 mb-2">
                        <Input
                            value={newCategory}
                            onChange={(e) => setNewCategory(e.target.value)}
                            placeholder="New category…"
                            className="h-7 text-[11px]"
                            onKeyDown={(e) => e.key === "Enter" && handleAddCategory()}
                        />
                        <Button variant="default" size="xs" onClick={handleAddCategory}>
                            Add
                        </Button>
                    </div>
                )}

                <div className="space-y-0.5 max-h-40 overflow-y-auto">
                    {allCategories.map((cat) => (
                        <button
                            key={cat}
                            type="button"
                            onClick={() => handleCategoryFilter(cat)}
                            className={cn(
                                "flex items-center gap-2 w-full px-2 py-1 text-[11px] rounded-sm transition-colors",
                                filters.category === cat
                                    ? "bg-primary/10 text-primary"
                                    : "text-muted-foreground hover:text-foreground hover:bg-muted",
                            )}
                        >
                            <Circle className="size-2.5 fill-current" />
                            {cat}
                        </button>
                    ))}
                    {allCategories.length === 0 && !showAddCategory && (
                        <p className="text-[11px] text-muted-foreground px-2 py-1 italic">
                            No categories yet
                        </p>
                    )}
                </div>
            </div>
        </div>
    )
}
