import { useState, useCallback, useMemo, useEffect, useRef } from "react"
import { Plus, Filter } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useNotes, useNote, useCreateNote, useUpdateNote, useDeleteNote, useRestoreNote, useToggleArchive, useTogglePin, useToggleFavorite } from "../hooks/useNotesApi"
import { SearchBar } from "../components/SearchBar"
import { NoteList } from "../components/NoteList"
import { NoteEditor } from "../components/NoteEditor"
import { FilterPanel } from "../components/FilterPanel"
import { DeleteNoteDialog, RestoreNoteDialog, ArchiveNoteDialog } from "../components/ConfirmDialogs"
import { toCreatePayload, toUpdatePayload } from "../api/notesMapper"
import { getEmptyDoc } from "../utils/notesUtils"

export default function NotesPage() {
    const [search, setSearch] = useState("")
    const [filters, setFilters] = useState({})
    const [filterOpen, setFilterOpen] = useState(false)
    const [selectedNoteId, setSelectedNoteId] = useState(null)
    const [isCreating, setIsCreating] = useState(false)
    const [saveState, setSaveState] = useState("saved")

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

    const { data: notesData, isLoading: isListLoading } = useNotes(queryFilters)
    const notes = useMemo(() => {
        if (!notesData?.notes) return []
        const sorted = [...notesData.notes].sort((a, b) => {
            if (a.is_pinned && !b.is_pinned) return -1
            if (!a.is_pinned && b.is_pinned) return 1
            return new Date(b.updated_at) - new Date(a.updated_at)
        })
        return sorted
    }, [notesData])

    const { data: selectedNote, isLoading: isNoteLoading } = useNote(
        isCreating ? null : selectedNoteId,
    )

    const allCategories = useMemo(() => {
        const cats = new Set()
        notesData?.notes?.forEach((n) => { if (n.category) cats.add(n.category) })
        return Array.from(cats).sort()
    }, [notesData])

    const createMutation = useCreateNote((note) => {
        creatingRef.current = false
        setIsCreating(false)
        setSelectedNoteId(note.id)
        setSaveState("saved")
    })

    const updateMutation = useUpdateNote()
    const toggleArchive = useToggleArchive()
    const togglePin = useTogglePin()
    const toggleFavorite = useToggleFavorite()

    const deleteMutation = useDeleteNote((deletedId) => {
        setDeleteTarget(null)
        setSelectedNoteId((prev) => (prev === deletedId ? null : prev))
    })

    const restoreMutation = useRestoreNote((restoredId) => {
        setRestoreTarget(null)
        setFilters((prev) => {
            const next = { ...prev }
            delete next.deleted
            return next
        })
        setSelectedNoteId((prev) => (prev === restoredId ? null : prev))
    })

    const handleCreateNote = useCallback(() => {
        if (creatingRef.current) return
        setIsCreating(true)
        setSelectedNoteId(null)
        setMobileView("editor")
        setSaveState("saved")
    }, [])

    const handleSelectNote = useCallback((id) => {
        setSelectedNoteId(id)
        setIsCreating(false)
        setSaveState("saved")
        if (id) {
            setMobileView("editor")
        }
    }, [])

    const handleSave = useCallback((partialData) => {
        if (isCreating) {
            if (creatingRef.current) return
            creatingRef.current = true
            setSaveState("saving")
            const payload = toCreatePayload({
                title: partialData.title || "",
                content: partialData.content || JSON.stringify(getEmptyDoc()),
                category: partialData.category || null,
                tags: partialData.tags || [],
            })
            createMutation.mutate(payload)
        } else if (selectedNoteId) {
            setSaveState("saving")
            updateMutation.mutate(
                { id: selectedNoteId, payload: toUpdatePayload(partialData) },
                {
                    onSuccess: () => setSaveState("saved"),
                    onError: () => setSaveState("unsaved"),
                },
            )
        }
    }, [isCreating, selectedNoteId, createMutation, updateMutation])

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
                handleCreateNote()
            }
        }
        window.addEventListener("keydown", handleKeyDown)
        return () => window.removeEventListener("keydown", handleKeyDown)
    }, [handleCreateNote])

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

    const currentNoteForEditor = isCreating ? null : selectedNote

    const handleArchiveNote = useCallback((note) => {
        setArchiveTarget({ id: note.id, currentlyArchived: note.is_archived, title: note.title })
    }, [])

    const handleDeleteNote = useCallback((note) => {
        setDeleteTarget({ id: note.id, title: note.title })
    }, [])

    const handleRestoreNote = useCallback((note) => {
        setRestoreTarget({ id: note.id, title: note.title })
    }, [])

    const handleTogglePin = useCallback(
        (params) => togglePin.mutate(params),
        [togglePin],
    )

    const handleToggleFavorite = useCallback(
        (params) => toggleFavorite.mutate(params),
        [toggleFavorite],
    )

    const noteListContent = (
        <NoteList
            notes={notes}
            isLoading={isListLoading}
            selectedNoteId={selectedNoteId}
            onSelectNote={handleSelectNote}
            onTogglePin={handleTogglePin}
            onToggleFavorite={handleToggleFavorite}
            onArchive={handleArchiveNote}
            onDelete={handleDeleteNote}
            onRestore={handleRestoreNote}
            onCreateNote={handleCreateNote}
            emptyType={filters.deleted ? "no-deleted" : filters.archived ? "no-archived" : search ? "no-search" : "no-notes"}
        />
    )

    const editorCommonProps = {
        note: currentNoteForEditor,
        isLoading: isNoteLoading,
        isCreating,
        onSave: handleSave,
        onCreateNote: handleCreateNote,
        onTogglePin: handleTogglePin,
        onToggleFavorite: handleToggleFavorite,
        onArchive: handleArchiveNote,
        onDelete: handleDeleteNote,
        onRestore: handleRestoreNote,
        saveState,
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
                        <Button variant="default" size="icon-sm" onClick={handleCreateNote} aria-label="Create note">
                            <Plus className="size-4" />
                        </Button>
                    </div>

                    <div className="flex-1 overflow-y-auto">
                        {noteListContent}
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
                        allCategories={allCategories}
                        onClose={() => setFilterOpen(false)}
                    />
                )}

                <div className="flex-1 overflow-hidden">
                    <NoteEditor {...editorCommonProps} showBackButton={false} />
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
                            <Button variant="default" size="icon-sm" onClick={handleCreateNote} aria-label="Create note">
                                <Plus className="size-4" />
                            </Button>
                        </div>

                        {filterOpen && (
                            <div className="border-b border-border">
                                <FilterPanel
                                    filters={filters}
                                    onChange={setFilters}
                                    allCategories={allCategories}
                                    onClose={() => setFilterOpen(false)}
                                />
                            </div>
                        )}

                        <div className="flex-1 overflow-y-auto">
                            {noteListContent}
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col h-full">
                        <NoteEditor {...editorCommonProps} showBackButton={true} onBack={handleEditorBack} />
                    </div>
                )}
            </div>

            <DeleteNoteDialog
                open={!!deleteTarget}
                noteTitle={deleteTarget?.title}
                onClose={() => setDeleteTarget(null)}
                onConfirm={handleConfirmDelete}
                isPending={deleteMutation.isPending}
            />
            <RestoreNoteDialog
                open={!!restoreTarget}
                noteTitle={restoreTarget?.title}
                onClose={() => setRestoreTarget(null)}
                onConfirm={handleConfirmRestore}
                isPending={restoreMutation.isPending}
            />
            <ArchiveNoteDialog
                open={!!archiveTarget}
                noteTitle={archiveTarget?.title}
                currentlyArchived={archiveTarget?.currentlyArchived}
                onClose={() => setArchiveTarget(null)}
                onConfirm={handleConfirmArchive}
                isPending={toggleArchive.isPending}
            />
        </div>
    )
}
