import { useState, useEffect, useRef, useCallback } from "react"
import { useEditor, EditorContent } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import Underline from "@tiptap/extension-underline"
import TaskList from "@tiptap/extension-task-list"
import TaskItem from "@tiptap/extension-task-item"
import { Table } from "@tiptap/extension-table"
import TableRow from "@tiptap/extension-table-row"
import TableCell from "@tiptap/extension-table-cell"
import TableHeader from "@tiptap/extension-table-header"
import Placeholder from "@tiptap/extension-placeholder"
import { Button } from "@/components/ui/button"
import { NoteToolbar } from "./NoteToolbar"
import { EditorSkeleton } from "./LoadingSkeleton"
import { ArrowLeft, Plus, FileText, Circle, Pin, Star, Archive, Trash2, RotateCcw } from "lucide-react"
import { AUTO_SAVE_DELAY } from "../constants"
import { getEmptyDoc } from "../utils/notesUtils"

export function NoteEditor({
    note,
    isLoading,
    isCreating,
    onSave,
    onBack,
    onCreateNote,
    onTogglePin,
    onToggleFavorite,
    onArchive,
    onDelete,
    onRestore,
    saveState,
    showBackButton,
}) {
    const [title, setTitle] = useState("")
    const [category, setCategory] = useState("")
    const [newTag, setNewTag] = useState("")
    const saveTimer = useRef(null)
    const titleRef = useRef(title)
    const categoryRef = useRef(category)
    const onSaveRef = useRef(onSave)
    const isUpdatingContent = useRef(false)

    useEffect(() => { titleRef.current = title }, [title])
    useEffect(() => { categoryRef.current = category }, [category])
    useEffect(() => { onSaveRef.current = onSave }, [onSave])

    const editor = useEditor({
        extensions: [
            StarterKit.configure({
                heading: { levels: [1, 2, 3] },
                underline: false,
            }),
            Underline,
            TaskList,
            TaskItem.configure({ nested: true }),
            Table.configure({ resizable: true }),
            TableRow,
            TableCell,
            TableHeader,
            Placeholder.configure({
                placeholder: "Start writing…",
            }),
        ],
        content: getEmptyDoc(),
        onUpdate: () => {
            if (isUpdatingContent.current) return
            autosaveRef.current()
        },
        editorProps: {
            attributes: {
                class: "prose prose-sm max-w-none focus:outline-none min-h-[300px] text-xs",
            },
        },
    })

    const autosaveRef = useRef(() => {})
    const triggerAutosave = useCallback(() => {
        if (saveTimer.current) clearTimeout(saveTimer.current)
        saveTimer.current = setTimeout(() => {
            if (!editor) return
            const json = editor.getJSON()
            onSaveRef.current?.({
                title: titleRef.current || null,
                content: JSON.stringify(json),
                category: categoryRef.current || null,
            })
        }, AUTO_SAVE_DELAY)
    }, [editor])

    autosaveRef.current = triggerAutosave

    const isDeleted = note ? !!note.deleted_at : false

    useEffect(() => {
        if (!editor) return
        isUpdatingContent.current = true
        if (isCreating) {
            editor.commands.setContent(getEmptyDoc())
        } else if (note) {
            try {
                const json = typeof note.content === "string" ? JSON.parse(note.content) : note.content
                editor.commands.setContent(json || getEmptyDoc())
            } catch {
                editor.commands.setContent(getEmptyDoc())
            }
        }
        isUpdatingContent.current = false
    }, [note?.id, isCreating, editor])

    const prevNoteId = useRef(note?.id)
    useEffect(() => {
        if (note && note.id !== prevNoteId.current) {
            setTitle(note.title || "")
            setCategory(note.category || "")
            prevNoteId.current = note.id
        } else if (isCreating && prevNoteId.current !== null) {
            setTitle("")
            setCategory("")
            prevNoteId.current = null
        }
    }, [note?.id, note?.title, note?.category, isCreating])

    useEffect(() => {
        return () => {
            if (saveTimer.current) clearTimeout(saveTimer.current)
        }
    }, [])

    const handleTitleChange = (e) => {
        setTitle(e.target.value)
        triggerAutosave()
    }

    const handleCategoryChange = (e) => {
        setCategory(e.target.value)
        triggerAutosave()
    }

    const handleAddTag = () => {
        if (!newTag.trim()) return
        onSave?.({ tags: [newTag.trim().toLowerCase()] })
        setNewTag("")
    }

    const handleTogglePin = () => {
        if (note) onTogglePin?.({ id: note.id, currentlyPinned: note.is_pinned })
    }

    const handleToggleFavorite = () => {
        if (note) onToggleFavorite?.({ id: note.id, currentlyFavorited: note.is_favorite })
    }

    const handleArchive = () => {
        if (note) onArchive?.(note)
    }

    const handleDelete = () => {
        if (note) onDelete?.(note)
    }

    const handleRestore = () => {
        if (note) onRestore?.(note)
    }

    if (!isCreating && !note && !isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-center px-6">
                <div className="flex size-12 items-center justify-center bg-muted mb-4">
                    <FileText className="size-5 text-muted-foreground" />
                </div>
                <p className="text-sm font-medium text-foreground mb-1">Select a note</p>
                <p className="text-xs text-muted-foreground max-w-xs mb-5">
                    Choose a note from the list or create a new one.
                </p>
                <Button size="sm" onClick={onCreateNote}>
                    <Plus className="size-3.5 mr-1" />
                    Create Note
                </Button>
            </div>
        )
    }

    if (isLoading) return <EditorSkeleton />

    const stateLabel = saveState === "saving" ? "Saving…" : saveState === "saved" ? "Saved" : saveState === "unsaved" ? "Unsaved changes" : ""

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between px-4 py-2 border-b border-border gap-2">
                <div className="flex items-center gap-2 min-w-0">
                    {showBackButton && (
                        <Button variant="ghost" size="icon-xs" onClick={onBack} aria-label="Back to list">
                            <ArrowLeft className="size-4" />
                        </Button>
                    )}
                    <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                        {stateLabel && (
                            <span className="flex items-center gap-1">
                                <span className={`size-1.5 rounded-full ${saveState === "saving" ? "bg-amber-500 animate-pulse" : saveState === "saved" ? "bg-green-500" : "bg-muted-foreground"}`} />
                                {stateLabel}
                            </span>
                        )}
                    </div>
                </div>
                {note && !isCreating && (
                    <div className="flex items-center gap-0.5">
                        {isDeleted ? (
                            <Button
                                variant="ghost"
                                size="icon-xs"
                                onClick={handleRestore}
                                className="text-green-600 hover:text-green-700"
                                title="Restore"
                            >
                                <RotateCcw className="size-3.5" />
                            </Button>
                        ) : (
                            <>
                                <Button
                                    variant="ghost"
                                    size="icon-xs"
                                    onClick={handleTogglePin}
                                    className={note.is_pinned ? "text-amber-600" : ""}
                                    title={note.is_pinned ? "Unpin" : "Pin"}
                                >
                                    <Pin className="size-3.5" />
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="icon-xs"
                                    onClick={handleToggleFavorite}
                                    className={note.is_favorite ? "text-amber-500" : ""}
                                    title={note.is_favorite ? "Remove from favorites" : "Add to favorites"}
                                >
                                    <Star className="size-3.5" />
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="icon-xs"
                                    onClick={handleArchive}
                                    title={note.is_archived ? "Unarchive" : "Archive"}
                                >
                                    <Archive className="size-3.5" />
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="icon-xs"
                                    onClick={handleDelete}
                                    className="text-destructive hover:text-destructive"
                                    title="Delete"
                                >
                                    <Trash2 className="size-3.5" />
                                </Button>
                            </>
                        )}
                    </div>
                )}
            </div>

            <div className="px-4 pt-3 pb-1 border-b border-border">
                <input
                    type="text"
                    value={title}
                    onChange={handleTitleChange}
                    placeholder="Note title…"
                    className="w-full bg-transparent text-sm font-medium text-foreground placeholder:text-muted-foreground outline-none border-none p-0"
                    aria-label="Note title"
                />
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <div className="relative flex items-center">
                        <Circle className="size-2.5 absolute left-2 text-muted-foreground" />
                        <input
                            type="text"
                            value={category}
                            onChange={handleCategoryChange}
                            placeholder="Category…"
                            className="h-6 pl-6 pr-2 bg-muted border border-border text-[11px] text-foreground placeholder:text-muted-foreground outline-none focus-visible:border-ring w-28"
                            aria-label="Category"
                        />
                    </div>
                    {note?.tags?.map((tag) => (
                        <span key={tag} className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-muted text-[10px] text-muted-foreground rounded-sm">
                            {tag}
                        </span>
                    ))}
                    <div className="flex items-center gap-1">
                        <input
                            type="text"
                            value={newTag}
                            onChange={(e) => setNewTag(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleAddTag()}
                            placeholder="Add tag…"
                            className="h-6 px-2 bg-muted border border-border text-[11px] text-foreground placeholder:text-muted-foreground outline-none focus-visible:border-ring w-20"
                            aria-label="Add tag"
                        />
                        {newTag && (
                            <Button variant="ghost" size="icon-xs" onClick={handleAddTag}>
                                <Plus className="size-3" />
                            </Button>
                        )}
                    </div>
                </div>
            </div>

            <NoteToolbar editor={editor} />

            <div className="flex-1 overflow-y-auto px-4 py-3">
                <EditorContent editor={editor} className="h-full" />
            </div>
        </div>
    )
}
