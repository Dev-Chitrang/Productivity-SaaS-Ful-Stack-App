import { useState, useCallback, useMemo, useEffect, useRef } from "react"
import { Plus, Filter } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useTasks, useTask, useCreateTask, useUpdateTask, useDeleteTask, useRestoreTask, useToggleArchive, useTogglePin, useToggleFavorite } from "../hooks/useTasksApi"
import { SearchBar } from "../components/SearchBar"
import { TaskList } from "../components/TaskList"
import { TaskEditor } from "../components/TaskEditor"
import { FilterPanel } from "../components/FilterPanel"
import { DeleteTaskDialog, RestoreTaskDialog, ArchiveTaskDialog } from "../components/ConfirmDialogs"
import { toCreatePayload, toUpdatePayload } from "../api/tasksMapper"
import { getEmptyDoc } from "@/shared/editor"

export default function TasksPage() {
    const [search, setSearch] = useState("")
    const [filters, setFilters] = useState({})
    const [filterOpen, setFilterOpen] = useState(false)
    const [selectedTaskId, setSelectedTaskId] = useState(null)
    const [isCreating, setIsCreating] = useState(false)

    const [deleteTarget, setDeleteTarget] = useState(null)
    const [restoreTarget, setRestoreTarget] = useState(null)
    const [archiveTarget, setArchiveTarget] = useState(null)

    const [mobileView, setMobileView] = useState("list")
    const resizeRef = useRef(null)
    const [leftWidth, setLeftWidth] = useState(320)
    const creatingRef = useRef(false)

    const queryFilters = useMemo(() => ({
        search: search || undefined,
        ...Object.fromEntries(
            Object.entries(filters).filter(([, v]) => v !== undefined && v !== null && v !== ""),
        ),
    }), [search, filters])

    const { data: tasksData, isLoading: isListLoading } = useTasks(queryFilters)
    const tasks = useMemo(() => {
        if (!tasksData?.tasks) return []
        const sorted = [...tasksData.tasks].sort((a, b) => {
            if (a.is_pinned && !b.is_pinned) return -1
            if (!a.is_pinned && b.is_pinned) return 1
            return new Date(b.updated_at) - new Date(a.updated_at)
        })
        return sorted
    }, [tasksData])

    const { data: selectedTask, isLoading: isTaskLoading } = useTask(
        isCreating ? null : selectedTaskId,
    )

    const createMutation = useCreateTask((task) => {
        creatingRef.current = false
        setIsCreating(false)
        setSelectedTaskId(task.id)
    })

    const updateMutation = useUpdateTask()
    const toggleArchive = useToggleArchive()
    const togglePin = useTogglePin()
    const toggleFavorite = useToggleFavorite()

    const deleteMutation = useDeleteTask((deletedId) => {
        setDeleteTarget(null)
        setSelectedTaskId((prev) => (prev === deletedId ? null : prev))
    })

    const restoreMutation = useRestoreTask((restoredId) => {
        setRestoreTarget(null)
        setFilters((prev) => {
            const next = { ...prev }
            delete next.deleted
            return next
        })
        setSelectedTaskId((prev) => (prev === restoredId ? null : prev))
    })

    const handleCreateTask = useCallback(() => {
        if (creatingRef.current) return
        setIsCreating(true)
        setSelectedTaskId(null)
        setMobileView("editor")
    }, [])

    const handleSelectTask = useCallback((id) => {
        setSelectedTaskId(id)
        setIsCreating(false)
        if (id) {
            setMobileView("editor")
        }
    }, [])

    const handleSave = useCallback((partialData) => {
        if (isCreating) {
            if (creatingRef.current) return
            creatingRef.current = true
            const payload = toCreatePayload({
                title: partialData.title || "Untitled",
                description: partialData.description || getEmptyDoc(),
                status: partialData.status || "TODO",
                priority: partialData.priority || "MEDIUM",
                due_date: partialData.due_date || null,
                labels: partialData.labels || [],
                checklist: partialData.checklist || [],
            })
            createMutation.mutate(payload)
        } else if (selectedTaskId) {
            updateMutation.mutate(
                { id: selectedTaskId, payload: toUpdatePayload(partialData) },
            )
        }
    }, [isCreating, selectedTaskId, createMutation, updateMutation])

    const handleConfirmDelete = useCallback(() => {
        if (deleteTarget) deleteMutation.mutate(deleteTarget.id)
    }, [deleteTarget, deleteMutation])

    const handleConfirmRestore = useCallback(() => {
        if (restoreTarget) restoreMutation.mutate(restoreTarget.id)
    }, [restoreTarget, restoreMutation])

    const handleConfirmArchive = useCallback(() => {
        if (archiveTarget) {
            toggleArchive.mutate({ id: archiveTarget.id, currentlyArchived: archiveTarget.currentlyArchived })
            setArchiveTarget(null)
        }
    }, [archiveTarget, toggleArchive])

    const handleEditorBack = useCallback(() => {
        if (isCreating) {
            creatingRef.current = false
            setIsCreating(false)
        }
        setMobileView("list")
    }, [isCreating])

    useEffect(() => {
        const handleKeyDown = (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "n") {
                e.preventDefault()
                handleCreateTask()
            }
        }
        window.addEventListener("keydown", handleKeyDown)
        return () => window.removeEventListener("keydown", handleKeyDown)
    }, [handleCreateTask])

    const handleMouseDown = useCallback((e) => {
        e.preventDefault()
        const startX = e.clientX
        const startWidth = leftWidth
        const handleMouseMove = (moveEvent) => {
            const delta = moveEvent.clientX - startX
            const newWidth = Math.max(240, Math.min(500, startWidth + delta))
            setLeftWidth(newWidth)
        }
        const handleMouseUp = () => {
            document.removeEventListener("mousemove", handleMouseMove)
            document.removeEventListener("mouseup", handleMouseUp)
        }
        document.addEventListener("mousemove", handleMouseMove)
        document.addEventListener("mouseup", handleMouseUp)
    }, [leftWidth])

    const currentTaskForEditor = isCreating ? null : selectedTask

    const handleArchiveTask = useCallback((note) => {
        setArchiveTarget({ id: note.id, currentlyArchived: note.is_archived, title: note.title })
    }, [])

    const handleDeleteTask = useCallback((note) => {
        setDeleteTarget({ id: note.id, title: note.title })
    }, [])

    const handleRestoreTask = useCallback((note) => {
        setRestoreTarget({ id: note.id, title: note.title })
    }, [])

    const handleTogglePinAction = useCallback(
        (params) => togglePin.mutate(params),
        [togglePin],
    )

    const handleToggleFavoriteAction = useCallback(
        (params) => toggleFavorite.mutate(params),
        [toggleFavorite],
    )

    const taskListContent = (
        <TaskList
            tasks={tasks}
            isLoading={isListLoading}
            selectedTaskId={selectedTaskId}
            onSelectTask={handleSelectTask}
            onTogglePin={handleTogglePinAction}
            onToggleFavorite={handleToggleFavoriteAction}
            onArchive={handleArchiveTask}
            onDelete={handleDeleteTask}
            onRestore={handleRestoreTask}
            onCreateTask={handleCreateTask}
            emptyType={filters.deleted ? "no-deleted" : filters.archived ? "no-archived" : search ? "no-search" : "no-tasks"}
        />
    )

    const isSaving = createMutation.isPending || updateMutation.isPending

    const editorCommonProps = {
        task: currentTaskForEditor,
        isLoading: isTaskLoading,
        isCreating,
        onSave: handleSave,
        onBack: handleEditorBack,
        onCreateTask: handleCreateTask,
        onTogglePin: handleTogglePinAction,
        onToggleFavorite: handleToggleFavoriteAction,
        onArchive: handleArchiveTask,
        onDelete: handleDeleteTask,
        onRestore: handleRestoreTask,
        showBackButton: false,
        isSaving,
    }

    return (
        <div className="flex flex-col h-full">
            <div className="hidden lg:flex flex-1 overflow-hidden">
                <div
                    className="flex flex-col border-r border-border overflow-hidden shrink-0"
                    style={{ width: leftWidth }}
                >
                    <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
                        <SearchBar value={search} onChange={setSearch} className="flex-1" />
                        <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => setFilterOpen(!filterOpen)}
                            aria-label="Toggle filters"
                            data-active={filterOpen || Object.values(filters).some(Boolean)}
                            className="data-[active=true]:bg-primary/10 data-[active=true]:text-primary"
                        >
                            <Filter className="size-4" />
                        </Button>
                        <Button variant="default" size="icon-sm" onClick={handleCreateTask} aria-label="Create task">
                            <Plus className="size-4" />
                        </Button>
                    </div>

                    <div className="flex-1 overflow-y-auto">
                        {taskListContent}
                    </div>
                </div>

                <div
                    ref={resizeRef}
                    className="w-1 cursor-col-resize hover:bg-primary/20 active:bg-primary/30 shrink-0 transition-colors relative"
                    onMouseDown={handleMouseDown}
                >
                    <div className="absolute inset-y-0 -left-1 -right-1" />
                </div>

                {filterOpen && (
                    <FilterPanel
                        filters={filters}
                        onChange={setFilters}
                        onClose={() => setFilterOpen(false)}
                    />
                )}

                <div className="flex-1 overflow-hidden">
                    <TaskEditor {...editorCommonProps} showBackButton={false} />
                </div>
            </div>

            <div className="lg:hidden flex-1 overflow-hidden">
                {mobileView === "list" ? (
                    <div className="flex flex-col h-full">
                        <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
                            <SearchBar value={search} onChange={setSearch} className="flex-1" />
                            <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => setFilterOpen(!filterOpen)}
                                aria-label="Toggle filters"
                            >
                                <Filter className="size-4" />
                            </Button>
                            <Button variant="default" size="icon-sm" onClick={handleCreateTask} aria-label="Create task">
                                <Plus className="size-4" />
                            </Button>
                        </div>

                        {filterOpen && (
                            <div className="border-b border-border">
                                <FilterPanel
                                    filters={filters}
                                    onChange={setFilters}
                                    onClose={() => setFilterOpen(false)}
                                />
                            </div>
                        )}

                        <div className="flex-1 overflow-y-auto">
                            {taskListContent}
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col h-full">
                        <TaskEditor {...editorCommonProps} showBackButton={true} onBack={handleEditorBack} />
                    </div>
                )}
            </div>

            <DeleteTaskDialog
                open={!!deleteTarget}
                taskTitle={deleteTarget?.title}
                onClose={() => setDeleteTarget(null)}
                onConfirm={handleConfirmDelete}
                isPending={deleteMutation.isPending}
            />
            <RestoreTaskDialog
                open={!!restoreTarget}
                taskTitle={restoreTarget?.title}
                onClose={() => setRestoreTarget(null)}
                onConfirm={handleConfirmRestore}
                isPending={restoreMutation.isPending}
            />
            <ArchiveTaskDialog
                open={!!archiveTarget}
                taskTitle={archiveTarget?.title}
                currentlyArchived={archiveTarget?.currentlyArchived}
                onClose={() => setArchiveTarget(null)}
                onConfirm={handleConfirmArchive}
                isPending={toggleArchive.isPending}
            />
        </div>
    )
}
