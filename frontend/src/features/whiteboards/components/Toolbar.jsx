import { useMemo } from "react"
import {
    MousePointer2,
    Pen,
    Square,
    Circle,
    ArrowUpRight,
    Minus,
    Type,
    Undo2,
    Redo2,
    ZoomIn,
    ZoomOut,
    Trash2,
    Download,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover"
import { WhiteboardTool } from "../api/whiteboardsTypes"
import { MIN_ZOOM, MAX_ZOOM } from "../constants"

const tools = [
    { key: WhiteboardTool.SELECT, icon: MousePointer2, label: "Select" },
    { key: WhiteboardTool.PEN, icon: Pen, label: "Pen" },
    { key: WhiteboardTool.RECTANGLE, icon: Square, label: "Rectangle" },
    { key: WhiteboardTool.CIRCLE, icon: Circle, label: "Circle" },
    { key: WhiteboardTool.ARROW, icon: ArrowUpRight, label: "Arrow" },
    { key: WhiteboardTool.LINE, icon: Minus, label: "Line" },
    { key: WhiteboardTool.TEXT, icon: Type, label: "Text" },
]

const STROKE_WIDTHS = [1, 2, 3, 5, 8]
const COLORS = [
    "#000000", "#ffffff", "#f44336", "#e91e63", "#9c27b0",
    "#673ab7", "#3f51b5", "#2196f3", "#03a9f4", "#00bcd4",
    "#009688", "#4caf50", "#8bc34a", "#cddc39", "#ffeb3b",
    "#ffc107", "#ff9800", "#ff5722", "#795548", "#607d8b",
]

export function Toolbar({
    activeTool,
    onToolChange,
    strokeColor,
    onStrokeColorChange,
    strokeWidth,
    onStrokeWidthChange,
    onUndo,
    onRedo,
    canUndo,
    canRedo,
    zoom,
    onZoomIn,
    onZoomOut,
    onResetZoom,
    onClearBoard,
    onExport,
    selectedId,
    onDeleteSelected,
}) {
    const strokeWidthLabel = useMemo(() => {
        const idx = STROKE_WIDTHS.indexOf(strokeWidth)
        return idx >= 0 ? STROKE_WIDTHS[idx] : strokeWidth
    }, [strokeWidth])

    return (
        <div className="flex items-center gap-1 px-2 py-1.5 border-b border-border bg-card overflow-x-auto shrink-0">
            {tools.map(({ key, icon: Icon, label }) => (
                <button
                    key={key}
                    type="button"
                    onClick={() => onToolChange(key)}
                    className={cn(
                        "flex items-center justify-center size-7 rounded-sm transition-colors",
                        activeTool === key
                            ? "bg-primary/10 text-primary"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted",
                    )}
                    aria-label={label}
                    title={label}
                >
                    <Icon className="size-3.5" />
                </button>
            ))}

            <div className="w-px h-5 bg-border mx-1" />

            <Popover>
                <PopoverTrigger asChild>
                    <button
                        type="button"
                        className="flex items-center justify-center size-7 rounded-sm text-muted-foreground hover:text-foreground hover:bg-muted"
                        aria-label="Stroke color"
                        title="Stroke color"
                    >
                        <div
                            className="size-3.5 rounded-sm border border-border"
                            style={{ backgroundColor: strokeColor }}
                        />
                    </button>
                </PopoverTrigger>
                <PopoverContent side="bottom" align="start" className="p-2 min-w-[160px]">
                    <div className="grid grid-cols-7 gap-1">
                        {COLORS.map((color) => (
                            <button
                                key={color}
                                type="button"
                                onClick={() => onStrokeColorChange(color)}
                                className={cn(
                                    "size-5 rounded-sm border transition-transform hover:scale-110",
                                    strokeColor === color ? "border-ring ring-1 ring-ring" : "border-border",
                                )}
                                style={{ backgroundColor: color }}
                                aria-label={`Color ${color}`}
                            />
                        ))}
                    </div>
                    <div className="mt-2">
                        <input
                            type="color"
                            value={strokeColor}
                            onChange={(e) => onStrokeColorChange(e.target.value)}
                            className="w-full h-6 rounded cursor-pointer"
                            aria-label="Custom color"
                        />
                    </div>
                </PopoverContent>
            </Popover>

            <Popover>
                <PopoverTrigger asChild>
                    <button
                        type="button"
                        className="flex items-center justify-center size-7 rounded-sm text-muted-foreground hover:text-foreground hover:bg-muted text-[10px] font-medium"
                        aria-label="Stroke width"
                        title={`Stroke width: ${strokeWidthLabel}`}
                    >
                        {strokeWidthLabel}
                    </button>
                </PopoverTrigger>
                <PopoverContent side="bottom" align="start" className="p-2">
                    {STROKE_WIDTHS.map((w) => (
                        <button
                            key={w}
                            type="button"
                            onClick={() => onStrokeWidthChange(w)}
                            className={cn(
                                "flex items-center gap-2 w-full px-2 py-1.5 text-xs rounded-sm transition-colors hover:bg-muted",
                                strokeWidth === w && "bg-primary/10 text-primary",
                            )}
                        >
                            <div className="w-8 flex items-center">
                                <div
                                    className="bg-current rounded-full"
                                    style={{ height: Math.max(2, w), width: Math.max(2, w) }}
                                />
                            </div>
                            <span className="text-muted-foreground">{w}px</span>
                        </button>
                    ))}
                </PopoverContent>
            </Popover>

            <div className="w-px h-5 bg-border mx-1" />

            <button
                type="button"
                onClick={onUndo}
                disabled={!canUndo}
                className={cn(
                    "flex items-center justify-center size-7 rounded-sm transition-colors",
                    canUndo
                        ? "text-muted-foreground hover:text-foreground hover:bg-muted"
                        : "text-muted-foreground/30 cursor-not-allowed",
                )}
                aria-label="Undo"
                title="Undo (Ctrl+Z)"
            >
                <Undo2 className="size-3.5" />
            </button>
            <button
                type="button"
                onClick={onRedo}
                disabled={!canRedo}
                className={cn(
                    "flex items-center justify-center size-7 rounded-sm transition-colors",
                    canRedo
                        ? "text-muted-foreground hover:text-foreground hover:bg-muted"
                        : "text-muted-foreground/30 cursor-not-allowed",
                )}
                aria-label="Redo"
                title="Redo (Ctrl+Y)"
            >
                <Redo2 className="size-3.5" />
            </button>

            <div className="w-px h-5 bg-border mx-1" />

            <div className="flex items-center gap-0.5">
                <button
                    type="button"
                    onClick={onZoomOut}
                    disabled={zoom <= MIN_ZOOM}
                    className={cn(
                        "flex items-center justify-center size-7 rounded-sm transition-colors",
                        zoom > MIN_ZOOM
                            ? "text-muted-foreground hover:text-foreground hover:bg-muted"
                            : "text-muted-foreground/30 cursor-not-allowed",
                    )}
                    aria-label="Zoom out"
                    title="Zoom out"
                >
                    <ZoomOut className="size-3.5" />
                </button>
                <button
                    type="button"
                    onClick={onResetZoom}
                    className="flex items-center justify-center min-w-[36px] h-7 px-1 rounded-sm text-[10px] font-medium text-muted-foreground hover:text-foreground hover:bg-muted"
                    aria-label="Reset zoom"
                    title="Reset zoom"
                >
                    {Math.round(zoom * 100)}%
                </button>
                <button
                    type="button"
                    onClick={onZoomIn}
                    disabled={zoom >= MAX_ZOOM}
                    className={cn(
                        "flex items-center justify-center size-7 rounded-sm transition-colors",
                        zoom < MAX_ZOOM
                            ? "text-muted-foreground hover:text-foreground hover:bg-muted"
                            : "text-muted-foreground/30 cursor-not-allowed",
                    )}
                    aria-label="Zoom in"
                    title="Zoom in"
                >
                    <ZoomIn className="size-3.5" />
                </button>
            </div>

            <div className="w-px h-5 bg-border mx-1" />

            {selectedId && (
                <button
                    type="button"
                    onClick={onDeleteSelected}
                    className="flex items-center justify-center size-7 rounded-sm text-destructive hover:bg-destructive/10"
                    aria-label="Delete selected"
                    title="Delete selected (Delete)"
                >
                    <Trash2 className="size-3.5" />
                </button>
            )}

            <div className="w-px h-5 bg-border mx-1" />

            <button
                type="button"
                onClick={onClearBoard}
                className="flex items-center justify-center size-7 rounded-sm text-muted-foreground hover:text-foreground hover:bg-muted"
                aria-label="Clear board"
                title="Clear board"
            >
                <Trash2 className="size-3.5" />
            </button>

            <button
                type="button"
                onClick={onExport}
                className="flex items-center justify-center size-7 rounded-sm text-muted-foreground hover:text-foreground hover:bg-muted"
                aria-label="Export PNG"
                title="Export PNG"
            >
                <Download className="size-3.5" />
            </button>
        </div>
    )
}
