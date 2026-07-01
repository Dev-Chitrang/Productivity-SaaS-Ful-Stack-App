import { useState } from "react"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Minus, Plus } from "lucide-react"

export function TableDialog({ open, onOpenChange, onInsert }) {
    const [rows, setRows] = useState(3)
    const [cols, setCols] = useState(3)

    const canDecrementRows = rows > 1
    const canIncrementRows = rows < 20
    const canDecrementCols = cols > 1
    const canIncrementCols = cols < 10

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-xs">
                <DialogHeader>
                    <DialogTitle>Insert Table</DialogTitle>
                    <DialogDescription>
                        Choose the number of rows and columns.
                    </DialogDescription>
                </DialogHeader>
                <div className="flex flex-col gap-4 py-2">
                    <div className="flex items-center justify-between gap-4">
                        <span className="text-xs font-medium text-foreground w-16">Rows</span>
                        <div className="flex items-center gap-2">
                            <Button
                                variant="outline"
                                size="icon-xs"
                                disabled={!canDecrementRows}
                                onClick={() => setRows((r) => Math.max(1, r - 1))}
                                aria-label="Decrease rows"
                            >
                                <Minus className="size-3" />
                            </Button>
                            <span className="w-8 text-center text-xs font-medium tabular-nums">{rows}</span>
                            <Button
                                variant="outline"
                                size="icon-xs"
                                disabled={!canIncrementRows}
                                onClick={() => setRows((r) => Math.min(20, r + 1))}
                                aria-label="Increase rows"
                            >
                                <Plus className="size-3" />
                            </Button>
                        </div>
                    </div>
                    <div className="flex items-center justify-between gap-4">
                        <span className="text-xs font-medium text-foreground w-16">Columns</span>
                        <div className="flex items-center gap-2">
                            <Button
                                variant="outline"
                                size="icon-xs"
                                disabled={!canDecrementCols}
                                onClick={() => setCols((c) => Math.max(1, c - 1))}
                                aria-label="Decrease columns"
                            >
                                <Minus className="size-3" />
                            </Button>
                            <span className="w-8 text-center text-xs font-medium tabular-nums">{cols}</span>
                            <Button
                                variant="outline"
                                size="icon-xs"
                                disabled={!canIncrementCols}
                                onClick={() => setCols((c) => Math.min(10, c + 1))}
                                aria-label="Increase columns"
                            >
                                <Plus className="size-3" />
                            </Button>
                        </div>
                    </div>
                    <div
                        className="grid gap-px p-2 bg-border rounded-sm mx-auto"
                        style={{
                            gridTemplateColumns: `repeat(${cols}, 1fr)`,
                            width: `${cols * 24 + 4}px`,
                            height: `${rows * 16 + 4}px`,
                        }}
                    >
                        {Array.from({ length: rows * cols }).map((_, i) => (
                            <div key={i} className="bg-card rounded-[1px]" />
                        ))}
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        Cancel
                    </Button>
                    <Button
                        onClick={() => {
                            onInsert(rows, cols)
                            onOpenChange(false)
                        }}
                    >
                        Insert
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
