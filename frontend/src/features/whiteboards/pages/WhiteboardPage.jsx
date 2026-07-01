import { useState, useCallback, useMemo, useEffect, useRef } from "react"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
    useWhiteboards,
    useWhiteboard,
    useCreateWhiteboard,
    useRenameWhiteboard,
    useAutosaveWhiteboard,
    useDeleteWhiteboard,
    useRestoreWhiteboard,
    useToggleFavorite,
    useToggleArchive,
} from "../hooks/useWhiteboardsApi"
import { WhiteboardSearchBar } from "../components/SearchBar"
import { WhiteboardFilterPanel } from "../components/FilterPanel"
import { WhiteboardList } from "../components/WhiteboardList"
import { WhiteboardCanvas } from "../components/Canvas"
import { Toolbar } from "../components/Toolbar"
import { DeleteBoardDialog, RestoreBoardDialog, ArchiveBoardDialog } from "../components/ConfirmDialogs"
import { EmptyState } from "../components/EmptyState"
import { WhiteboardFilter, WhiteboardTool, DEFAULT_BOARD_DATA } from "../api/whiteboardsTypes"
import { MIN_ZOOM, MAX_ZOOM, ZOOM_STEP, DEFAULT_ZOOM } from "../constants"

export default function WhiteboardPage() {
    const [search, setSearch] = useState("")
    const [activeFilter, setActiveFilter] = useState(WhiteboardFilter.ALL)
    const [selectedBoardId, setSelectedBoardId] = useState(null)
    const [isCreating, setIsCreating] = useState(false)
    const isCreatingRef = useRef(false)

    const [tool, setTool] = useState(WhiteboardTool.SELECT)
    const [strokeColor, setStrokeColor] = useState("#000000")
    const [strokeWidth, setStrokeWidth] = useState(2)
    const [zoom, setZoom] = useState(DEFAULT_ZOOM)

    const [elements, setElements] = useState([])
    const [history, setHistory] = useState([])
    const [historyIndex, setHistoryIndex] = useState(-1)
    const [isCanvasReady, setIsCanvasReady] = useState(false)
    const [selectedId, setSelectedId] = useState(null)
    const autosaveTimer = useRef(null)
    const desktopStageRef = useRef(null)
    const mobileStageRef = useRef(null)
    const historyInitializedRef = useRef({})
    const historyIndexRef = useRef(historyIndex)
    historyIndexRef.current = historyIndex

    const [deleteTarget, setDeleteTarget] = useState(null)
    const [restoreTarget, setRestoreTarget] = useState(null)
    const [archiveTarget, setArchiveTarget] = useState(null)

    const [mobileView, setMobileView] = useState("list")
    const [leftWidth, setLeftWidth] = useState(280)

    const onSelectElement = useCallback((id) => {
        setSelectedId(id)
    }, [])

    const queryFilters = useMemo(() => {
        const filters = { search: search || undefined }
        if (activeFilter === WhiteboardFilter.ARCHIVED) {
            filters.is_archived = true
            filters.is_deleted = false
        } else if (activeFilter === WhiteboardFilter.DELETED) {
            filters.is_deleted = true
            filters.is_archived = false
        } else if (activeFilter === WhiteboardFilter.FAVORITE) {
            filters.is_favorite = true
            filters.is_archived = false
            filters.is_deleted = false
        } else {
            filters.is_archived = false
            filters.is_deleted = false
        }
        return filters
    }, [search, activeFilter])

    const { data: boardsData, isLoading: isListLoading } = useWhiteboards(queryFilters)
    const boards = useMemo(() => {
        if (!boardsData) return []
        const sorted = [...boardsData].sort((a, b) => {
            if (a.is_favorite && !b.is_favorite) return -1
            if (!a.is_favorite && b.is_favorite) return 1
            return new Date(b.updated_at) - new Date(a.updated_at)
        })
        return sorted
    }, [boardsData])

    const { data: selectedBoard } = useWhiteboard(
        isCreating ? null : selectedBoardId,
    )

    const createMutation = useCreateWhiteboard((board) => {
        isCreatingRef.current = false
        setIsCreating(false)
        setSelectedBoardId(board.id)
        setElements((board.board_data?.elements) || [])
        setHistory([(board.board_data?.elements) || []])
        setHistoryIndex(0)
        setIsCanvasReady(true)
    })
    const renameMutation = useRenameWhiteboard()
    const autosaveMutation = useAutosaveWhiteboard()
    const toggleFavoriteMutation = useToggleFavorite()
    const toggleArchiveMutation = useToggleArchive()
    const deleteMutation = useDeleteWhiteboard((deletedId) => {
        setDeleteTarget(null)
        setSelectedBoardId((prev) => (prev === deletedId ? null : prev))
        setElements([])
        setIsCanvasReady(false)
    })
    const restoreMutation = useRestoreWhiteboard((restoredId) => {
        setRestoreTarget(null)
        setActiveFilter(WhiteboardFilter.ALL)
        setSelectedBoardId((prev) => (prev === restoredId ? null : prev))
    })

    useEffect(() => {
        if (selectedBoard && !isCreating) {
            const boardId = selectedBoard.id
            if (historyInitializedRef.current[boardId]) return
            historyInitializedRef.current[boardId] = true
            const boardData = selectedBoard.board_data || DEFAULT_BOARD_DATA
            const loadedElements = boardData.elements || []
            setElements(loadedElements)
            setHistory([loadedElements])
            setHistoryIndex(0)
            setIsCanvasReady(true)
        } else if (!selectedBoard && !isCreating) {
            setIsCanvasReady(false)
        }
    }, [selectedBoard])

    useEffect(() => {
        if (autosaveTimer.current) clearTimeout(autosaveTimer.current)
        if (!selectedBoardId || isCreating || !isCanvasReady) return

        const boardData = { version: 1, elements }

        autosaveTimer.current = setTimeout(() => {
            autosaveMutation.mutate({
                id: selectedBoardId,
                payload: { board_data: boardData },
            })
        }, 1000)

        return () => {
            if (autosaveTimer.current) clearTimeout(autosaveTimer.current)
        }
    }, [elements, selectedBoardId, isCreating, isCanvasReady, autosaveMutation])

    const pushHistory = useCallback((newElements) => {
        setHistory((prev) => {
            const trimmed = prev.slice(0, historyIndexRef.current + 1)
            return [...trimmed, newElements]
        })
        setHistoryIndex((prev) => prev + 1)
    }, [])

    const handleElementsChange = useCallback((newElements) => {
        setElements(newElements)
        pushHistory(newElements)
    }, [pushHistory])

    const canUndo = historyIndex > 0
    const canRedo = historyIndex < history.length - 1

    const handleUndo = useCallback(() => {
        if (!canUndo) return
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        setElements(history[newIndex])
    }, [canUndo, historyIndex, history])

    const handleRedo = useCallback(() => {
        if (!canRedo) return
        const newIndex = historyIndex + 1
        setHistoryIndex(newIndex)
        setElements(history[newIndex])
    }, [canRedo, historyIndex, history])

    const handleCreateBoard = useCallback(() => {
        if (isCreatingRef.current) return
        isCreatingRef.current = true
        const payload = { title: "Untitled", board_data: { version: 1, elements: [] } }
        createMutation.mutate(payload)
        setIsCreating(true)
        setSelectedBoardId(null)
        setMobileView("canvas")
    }, [createMutation])

    const handleSelectBoard = useCallback((id) => {
        if (isCreatingRef.current) return
        setSelectedBoardId(id)
        setIsCreating(false)
        if (id) setMobileView("canvas")
    }, [])

    const handleSaveBoardTitle = useCallback((boardId, title) => {
        if (!title?.trim()) return
        renameMutation.mutate({ id: boardId, payload: { title: title.trim() } })
    }, [renameMutation])

    const handleConfirmDelete = useCallback(() => {
        if (deleteTarget) deleteMutation.mutate(deleteTarget.id)
    }, [deleteTarget, deleteMutation])

    const handleConfirmRestore = useCallback(() => {
        if (restoreTarget) restoreMutation.mutate(restoreTarget.id)
    }, [restoreTarget, restoreMutation])

    const handleConfirmArchive = useCallback(() => {
        if (archiveTarget) {
            toggleArchiveMutation.mutate({
                id: archiveTarget.id,
                currentlyArchived: archiveTarget.currentlyArchived,
            })
            setArchiveTarget(null)
        }
    }, [archiveTarget, toggleArchiveMutation])

    const handleDeleteElement = useCallback(() => {
        if (!selectedId) return
        const updated = elements.filter((el) => el.id !== selectedId)
        handleElementsChange(updated)
        setSelectedId(null)
    }, [selectedId, elements, handleElementsChange])

    const handleClearBoard = useCallback(() => {
        handleElementsChange([])
    }, [handleElementsChange])

    const handleExport = useCallback(() => {
        const stages = [desktopStageRef, mobileStageRef]
        let visibleStage = null
        for (const ref of stages) {
            const stage = ref.current
            if (!stage) continue
            const container = stage.container()
            if (container && container.offsetWidth > 0 && container.offsetHeight > 0) {
                visibleStage = stage
                break
            }
        }
        if (!visibleStage) return
        const uri = visibleStage.toDataURL({ pixelRatio: 2 })
        const link = document.createElement("a")
        link.download = `${selectedBoard?.title || "whiteboard"}.png`
        link.href = uri
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
    }, [selectedBoard])

    const handleZoomChange = useCallback((newZoom) => {
        setZoom(newZoom)
    }, [])

    useEffect(() => {
        const handleKeyDown = (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) {
                e.preventDefault()
                handleUndo()
            }
            if ((e.ctrlKey || e.metaKey) && (e.key === "y" || (e.key === "z" && e.shiftKey))) {
                e.preventDefault()
                handleRedo()
            }
            if (e.key === "Delete" || e.key === "Backspace") {
                if (document.activeElement?.tagName === "INPUT" || document.activeElement?.tagName === "TEXTAREA") return
                if (selectedBoardId && selectedId) {
                    const updated = elements.filter((el) => el.id !== selectedId)
                    handleElementsChange(updated)
                    onSelectElement(null)
                }
            }
            if ((e.ctrlKey || e.metaKey) && e.key === "n") {
                e.preventDefault()
                handleCreateBoard()
            }
        }
        window.addEventListener("keydown", handleKeyDown)
        return () => window.removeEventListener("keydown", handleKeyDown)
    }, [handleUndo, handleRedo, handleCreateBoard, elements, selectedBoardId, selectedId, onSelectElement, handleElementsChange])

    const handleMouseDown = useCallback((e) => {
        e.preventDefault()
        const startX = e.clientX
        const startWidth = leftWidth
        const handleMouseMove = (moveEvent) => {
            const delta = moveEvent.clientX - startX
            const newWidth = Math.max(200, Math.min(400, startWidth + delta))
            setLeftWidth(newWidth)
        }
        const handleMouseUp = () => {
            document.removeEventListener("mousemove", handleMouseMove)
            document.removeEventListener("mouseup", handleMouseUp)
        }
        document.addEventListener("mousemove", handleMouseMove)
        document.addEventListener("mouseup", handleMouseUp)
    }, [leftWidth])

    const handleDeleteBoard = useCallback((board) => {
        setDeleteTarget({ id: board.id, title: board.title })
    }, [])

    const handleRestoreBoardAction = useCallback((board) => {
        setRestoreTarget({ id: board.id, title: board.title })
    }, [])

    const handleArchiveBoard = useCallback((board) => {
        setArchiveTarget({
            id: board.id,
            currentlyArchived: board.is_archived,
            title: board.title,
        })
    }, [])

    const handleToggleFavorite = useCallback(
        (params) => toggleFavoriteMutation.mutate(params),
        [toggleFavoriteMutation],
    )

    const boardListContent = (
        <WhiteboardList
            boards={boards}
            isLoading={isListLoading}
            selectedBoardId={selectedBoardId}
            onSelectBoard={handleSelectBoard}
            onToggleFavorite={handleToggleFavorite}
            onArchive={handleArchiveBoard}
            onDelete={handleDeleteBoard}
            onRestore={handleRestoreBoardAction}
            onCreateBoard={handleCreateBoard}
            emptyType={
                activeFilter === WhiteboardFilter.DELETED
                    ? "no-deleted"
                    : activeFilter === WhiteboardFilter.ARCHIVED
                        ? "no-archived"
                        : search
                            ? "no-search"
                            : "no-boards"
            }
        />
    )

    const displayTitle = isCreating
        ? "New Whiteboard"
        : selectedBoard?.title || "Untitled"

    const emptyType = !selectedBoardId && !isCreating ? "no-board-selected" : null

    return (
        <div className="flex flex-col h-full">
            <div className="hidden lg:flex flex-1">
                <div
                    className="flex flex-col border-r border-border overflow-hidden shrink-0"
                    style={{ width: leftWidth }}
                >
                    <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
                        <WhiteboardSearchBar value={search} onChange={setSearch} className="flex-1" />
                        <Button variant="default" size="icon-sm" onClick={handleCreateBoard} aria-label="Create whiteboard">
                            <Plus className="size-4" />
                        </Button>
                    </div>
                    <WhiteboardFilterPanel activeFilter={activeFilter} onChange={setActiveFilter} />
                    <div className="flex-1 overflow-y-auto">
                        {boardListContent}
                    </div>
                </div>

                <div
                    className="w-1 cursor-col-resize hover:bg-primary/20 active:bg-primary/30 shrink-0 transition-colors relative"
                    onMouseDown={handleMouseDown}
                >
                    <div className="absolute inset-y-0 -left-1 -right-1" />
                </div>

                <div className="flex-1 flex flex-col">
                    {isCanvasReady ? (
                        <>
                            <div className="flex items-center gap-2 px-3 py-1.5 border-b border-border shrink-0">
                                <input
                                    type="text"
                                    defaultValue={displayTitle}
                                    onBlur={(e) => {
                                        if (selectedBoardId && !isCreating) {
                                            handleSaveBoardTitle(selectedBoardId, e.target.value)
                                        }
                                    }}
                                    onKeyDown={(e) => {
                                        if (e.key === "Enter") e.currentTarget.blur()
                                    }}
                                    className="text-xs font-medium text-foreground bg-transparent border-none outline-none px-1 py-0.5 rounded-sm focus:ring-1 focus:ring-ring/50 flex-1 min-w-0"
                                    aria-label="Board title"
                                />
                            </div>
                            <Toolbar
                                activeTool={tool}
                                onToolChange={setTool}
                                strokeColor={strokeColor}
                                onStrokeColorChange={setStrokeColor}
                                strokeWidth={strokeWidth}
                                onStrokeWidthChange={setStrokeWidth}
                                onUndo={handleUndo}
                                onRedo={handleRedo}
                                canUndo={canUndo}
                                canRedo={canRedo}
                                zoom={zoom}
                                onZoomIn={() => setZoom((z) => Math.min(MAX_ZOOM, +(z + ZOOM_STEP).toFixed(2)))}
                                onZoomOut={() => setZoom((z) => Math.max(MIN_ZOOM, +(z - ZOOM_STEP).toFixed(2)))}
                                onResetZoom={() => setZoom(DEFAULT_ZOOM)}
                                onClearBoard={handleClearBoard}
                                onExport={handleExport}
                                selectedId={selectedId}
                                onDeleteSelected={handleDeleteElement}
                            />
                            <WhiteboardCanvas
                                elements={elements}
                                selectedId={selectedId}
                                tool={tool}
                                strokeColor={strokeColor}
                                strokeWidth={strokeWidth}
                                zoom={zoom}
                                onElementsChange={handleElementsChange}
                                onSelectElement={onSelectElement}
                                onStageRef={(ref) => { desktopStageRef.current = ref }}
                                onZoomChange={handleZoomChange}
                            />
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center">
                            <EmptyState type={emptyType} onCreateBoard={handleCreateBoard} />
                        </div>
                    )}
                </div>
            </div>

            <div className="lg:hidden flex-1 overflow-hidden">
                {mobileView === "list" ? (
                    <div className="flex flex-col h-full">
                        <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
                            <WhiteboardSearchBar value={search} onChange={setSearch} className="flex-1" />
                            <Button variant="default" size="icon-sm" onClick={handleCreateBoard} aria-label="Create whiteboard">
                                <Plus className="size-4" />
                            </Button>
                        </div>
                        <WhiteboardFilterPanel activeFilter={activeFilter} onChange={setActiveFilter} />
                        <div className="flex-1 overflow-y-auto">
                            {boardListContent}
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col h-full">
                        {isCanvasReady ? (
                            <>
                                <div className="flex items-center gap-2 px-3 py-1.5 border-b border-border shrink-0">
                                    <button
                                        type="button"
                                        onClick={() => setMobileView("list")}
                                        className="text-xs text-muted-foreground hover:text-foreground"
                                    >
                                        &larr; Back
                                    </button>
                                    <input
                                        type="text"
                                        defaultValue={displayTitle}
                                        onBlur={(e) => {
                                            if (selectedBoardId && !isCreating) {
                                                handleSaveBoardTitle(selectedBoardId, e.target.value)
                                            }
                                        }}
                                        onKeyDown={(e) => {
                                            if (e.key === "Enter") e.currentTarget.blur()
                                        }}
                                        className="text-xs font-medium text-foreground bg-transparent border-none outline-none px-1 py-0.5 rounded-sm focus:ring-1 focus:ring-ring/50 flex-1 min-w-0"
                                        aria-label="Board title"
                                    />
                                </div>
                                <Toolbar
                                    activeTool={tool}
                                    onToolChange={setTool}
                                    strokeColor={strokeColor}
                                    onStrokeColorChange={setStrokeColor}
                                    strokeWidth={strokeWidth}
                                    onStrokeWidthChange={setStrokeWidth}
                                    onUndo={handleUndo}
                                    onRedo={handleRedo}
                                    canUndo={canUndo}
                                    canRedo={canRedo}
                                    zoom={zoom}
                                    onZoomIn={() => setZoom((z) => Math.min(MAX_ZOOM, +(z + ZOOM_STEP).toFixed(2)))}
                                    onZoomOut={() => setZoom((z) => Math.max(MIN_ZOOM, +(z - ZOOM_STEP).toFixed(2)))}
                                    onResetZoom={() => setZoom(DEFAULT_ZOOM)}
                                    onClearBoard={handleClearBoard}
                                    onExport={handleExport}
                                    selectedId={selectedId}
                                    onDeleteSelected={handleDeleteElement}
                                />
                                <WhiteboardCanvas
                                    elements={elements}
                                    selectedId={selectedId}
                                    tool={tool}
                                    strokeColor={strokeColor}
                                    strokeWidth={strokeWidth}
                                    zoom={zoom}
                                    onElementsChange={handleElementsChange}
                                    onSelectElement={onSelectElement}
                                    onStageRef={(ref) => { mobileStageRef.current = ref }}
                                    onZoomChange={handleZoomChange}
                                />
                            </>
                        ) : (
                            <div className="flex-1 flex items-center justify-center">
                                <EmptyState type={emptyType} onCreateBoard={handleCreateBoard} />
                            </div>
                        )}
                    </div>
                )}
            </div>

            <DeleteBoardDialog
                open={!!deleteTarget}
                boardTitle={deleteTarget?.title}
                onClose={() => setDeleteTarget(null)}
                onConfirm={handleConfirmDelete}
                isPending={deleteMutation.isPending}
            />
            <RestoreBoardDialog
                open={!!restoreTarget}
                boardTitle={restoreTarget?.title}
                onClose={() => setRestoreTarget(null)}
                onConfirm={handleConfirmRestore}
                isPending={restoreMutation.isPending}
            />
            <ArchiveBoardDialog
                open={!!archiveTarget}
                boardTitle={archiveTarget?.title}
                currentlyArchived={archiveTarget?.currentlyArchived}
                onClose={() => setArchiveTarget(null)}
                onConfirm={handleConfirmArchive}
                isPending={toggleArchiveMutation.isPending}
            />
        </div>
    )
}
