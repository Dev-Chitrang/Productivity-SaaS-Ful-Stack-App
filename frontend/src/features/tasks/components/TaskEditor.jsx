import { useState, useEffect, useRef, useCallback, useMemo } from "react"
import { RichTextEditor, EditorToolbar, getEmptyDoc } from "@/shared/editor"
import { Button } from "@/components/ui/button"
import { TaskEditorSkeleton } from "./LoadingSkeleton"
import { TaskActivityTimeline } from "./TaskActivityTimeline"
import { AttachmentPanelContainer } from "@/features/attachments/components/AttachmentPanel"
import {
    useTaskAttachments,
    useUploadTaskAttachment,
    useDeleteTaskAttachment,
} from "@/features/attachments/hooks/useAttachmentsApi"
import { attachmentsApi } from "@/features/attachments/api/attachmentsApi"
import {
    ArrowLeft, Plus, ListTodo, Pin, Star, Archive, Trash2, RotateCcw,
    Circle, X, Calendar, Save, AlertCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { TaskStatus, TaskPriority, TaskStatusColors, TaskPriorityColors } from "../api/tasksTypes"
import { generateChecklistId, isOverdue as checkIsOverdue } from "../utils/tasksUtils"

export function TaskEditor({
    task,
    isLoading,
    isCreating,
    onSave,
    onBack,
    onCreateTask,
    onTogglePin,
    onToggleFavorite,
    onArchive,
    onDelete,
    onRestore,
    showBackButton,
    isSaving,
}) {
    const [title, setTitle] = useState("")
    const [status, setStatus] = useState("TODO")
    const [priority, setPriority] = useState("MEDIUM")
    const [dueDate, setDueDate] = useState("")
    const [newLabel, setNewLabel] = useState("")
    const [labels, setLabels] = useState([])
    const [checklist, setChecklist] = useState([])
    const [newChecklistItem, setNewChecklistItem] = useState("")
    const [editorInstance, setEditorInstance] = useState(null)
    const [descriptionContent, setDescriptionContent] = useState(null)

    const initialSnapshot = useRef(null)
    const prevTaskId = useRef(task?.id)

    const isDeleted = task ? !!task.deleted_at : false
    const isOverdue = useMemo(() => {
        if (!task?.due_date) return false
        return checkIsOverdue(task.due_date)
    }, [task])

    // ── Attachment hooks — must be called at top level, not inside JSX ──────
    const taskAttachments = useTaskAttachments(task?.id ?? null)
    const uploadTaskAttachment = useUploadTaskAttachment(task?.id ?? null)
    const deleteTaskAttachment = useDeleteTaskAttachment(task?.id ?? null)

    const contentJson = useMemo(() => {
        if (isCreating) return getEmptyDoc()
        if (task?.description) return task.description
        return getEmptyDoc()
    }, [task?.description, isCreating])

    const handleEditorUpdate = useCallback((json) => {
        setDescriptionContent(json)
    }, [])

    useEffect(() => {
        if (task && task.id !== prevTaskId.current) {
            const snapshot = {
                title: task.title || "",
                status: task.status || "TODO",
                priority: task.priority || "MEDIUM",
                dueDate: task.due_date ? task.due_date.slice(0, 10) : "",
                labels: [...(task.labels || [])],
                checklist: JSON.parse(JSON.stringify(task.checklist || [])),
                description: task.description
                    ? JSON.parse(JSON.stringify(task.description))
                    : JSON.parse(JSON.stringify(getEmptyDoc())),
            }
            initialSnapshot.current = snapshot
            setTitle(snapshot.title)
            setStatus(snapshot.status)
            setPriority(snapshot.priority)
            setDueDate(snapshot.dueDate)
            setLabels(snapshot.labels)
            setChecklist(snapshot.checklist)
            setDescriptionContent(snapshot.description)
            prevTaskId.current = task.id
        } else if (isCreating && prevTaskId.current !== null) {
            initialSnapshot.current = null
            setTitle("")
            setStatus("TODO")
            setPriority("MEDIUM")
            setDueDate("")
            setLabels([])
            setChecklist([])
            setDescriptionContent(getEmptyDoc())
            prevTaskId.current = null
        }
    }, [task?.id, task?.title, task?.status, task?.priority, task?.due_date, task?.labels, task?.checklist, task?.description, isCreating])

    const isDirty = useMemo(() => {
        if (!initialSnapshot.current) return false
        const init = initialSnapshot.current
        if (title !== init.title) return true
        if (status !== init.status) return true
        if (priority !== init.priority) return true
        if (dueDate !== init.dueDate) return true
        if (JSON.stringify(labels) !== JSON.stringify(init.labels)) return true
        if (JSON.stringify(checklist) !== JSON.stringify(init.checklist)) return true
        if (JSON.stringify(descriptionContent) !== JSON.stringify(init.description)) return true
        return false
    }, [title, status, priority, dueDate, labels, checklist, descriptionContent])

    const canSave = isCreating || isDirty

    useEffect(() => {
        if (!isDirty && !isCreating) return
        const handler = (e) => {
            e.preventDefault()
            e.returnValue = ""
        }
        window.addEventListener("beforeunload", handler)
        return () => window.removeEventListener("beforeunload", handler)
    }, [isDirty, isCreating])

    const handleTitleChange = (e) => {
        setTitle(e.target.value)
    }

    const handleStatusChange = (newStatus) => {
        setStatus(newStatus)
    }

    const handlePriorityChange = (newPriority) => {
        setPriority(newPriority)
    }

    const handleDueDateChange = (e) => {
        setDueDate(e.target.value)
    }

    const handleAddLabel = () => {
        const trimmed = newLabel.trim().toLowerCase()
        if (!trimmed || labels.includes(trimmed)) return
        setLabels([...labels, trimmed])
        setNewLabel("")
    }

    const handleRemoveLabel = (label) => {
        setLabels(labels.filter((l) => l !== label))
    }

    const handleAddChecklistItem = () => {
        const trimmed = newChecklistItem.trim()
        if (!trimmed) return
        const newItem = { id: generateChecklistId(), text: trimmed, completed: false }
        setChecklist([...checklist, newItem])
        setNewChecklistItem("")
    }

    const handleToggleChecklistItem = (id) => {
        setChecklist(checklist.map((item) =>
            item.id === id ? { ...item, completed: !item.completed } : item,
        ))
    }

    const handleEditChecklistItem = (id, text) => {
        setChecklist(checklist.map((item) =>
            item.id === id ? { ...item, text } : item,
        ))
    }

    const handleDeleteChecklistItem = (id) => {
        setChecklist(checklist.filter((item) => item.id !== id))
    }

    const handleSaveClick = () => {
        if (!canSave || isSaving) return
        onSave?.({
            title: title || null,
            description: descriptionContent || getEmptyDoc(),
            status,
            priority,
            due_date: dueDate || null,
            labels,
            checklist,
        })
    }

    const handleTogglePin = () => {
        if (task) onTogglePin?.({ id: task.id, currentlyPinned: task.is_pinned })
    }

    const handleToggleFavorite = () => {
        if (task) onToggleFavorite?.({ id: task.id, currentlyFavorited: task.is_favorite })
    }

    const handleArchive = () => {
        if (task) onArchive?.(task)
    }

    const handleDelete = () => {
        if (task) onDelete?.(task)
    }

    const handleRestore = () => {
        if (task) onRestore?.(task)
    }

    if (!isCreating && !task && !isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-center px-6">
                <div className="flex size-12 items-center justify-center bg-muted mb-4">
                    <ListTodo className="size-5 text-muted-foreground" />
                </div>
                <p className="text-sm font-medium text-foreground mb-1">Select a task</p>
                <p className="text-xs text-muted-foreground max-w-xs mb-5">
                    Choose a task from the list or create a new one.
                </p>
                <Button size="sm" onClick={onCreateTask}>
                    <Plus className="size-3.5 mr-1" />
                    Create Task
                </Button>
            </div>
        )
    }

    if (isLoading) return <TaskEditorSkeleton />

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between px-4 py-2 border-b border-border gap-2">
                <div className="flex items-center gap-2 min-w-0">
                    {showBackButton && (
                        <Button variant="ghost" size="icon-xs" onClick={onBack} aria-label="Back to list">
                            <ArrowLeft className="size-4" />
                        </Button>
                    )}
                    {isOverdue && (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-medium rounded-sm bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300">
                            <AlertCircle className="size-2.5" />
                            Overdue
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {task && !isCreating && !isDeleted && (
                        <>
                            <Button
                                variant="ghost"
                                size="icon-xs"
                                onClick={handleTogglePin}
                                className={task.is_pinned ? "text-amber-600" : ""}
                                title={task.is_pinned ? "Unpin" : "Pin"}
                            >
                                <Pin className="size-3.5" />
                            </Button>
                            <Button
                                variant="ghost"
                                size="icon-xs"
                                onClick={handleToggleFavorite}
                                className={task.is_favorite ? "text-amber-500" : ""}
                                title={task.is_favorite ? "Remove from favorites" : "Add to favorites"}
                            >
                                <Star className="size-3.5" />
                            </Button>
                            <Button
                                variant="ghost"
                                size="icon-xs"
                                onClick={handleArchive}
                                title={task.is_archived ? "Unarchive" : "Archive"}
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
                    {task && !isCreating && isDeleted && (
                        <Button
                            variant="ghost"
                            size="icon-xs"
                            onClick={handleRestore}
                            className="text-green-600 hover:text-green-700"
                            title="Restore"
                        >
                            <RotateCcw className="size-3.5" />
                        </Button>
                    )}
                    {!isDeleted && (
                        <Button
                            size="sm"
                            onClick={handleSaveClick}
                            disabled={!canSave || isSaving}
                        >
                            <Save className="size-3.5 mr-1" />
                            {isSaving ? "Saving…" : isCreating ? "Create" : "Save"}
                        </Button>
                    )}
                </div>
            </div>

            <div className="px-4 pt-3 pb-2 border-b border-border space-y-3">
                <input
                    type="text"
                    value={title}
                    onChange={handleTitleChange}
                    placeholder="Task title…"
                    className="w-full bg-transparent text-sm font-medium text-foreground placeholder:text-muted-foreground outline-none border-none p-0"
                    aria-label="Task title"
                />

                <div className="flex items-center gap-2 flex-wrap">
                    <div className="flex items-center gap-1">
                        {Object.values(TaskStatus).map((s) => (
                            <button
                                key={s}
                                type="button"
                                onClick={() => handleStatusChange(s)}
                                className={cn(
                                    "px-2 py-1 text-[11px] font-medium rounded-sm border transition-colors",
                                    status === s
                                        ? TaskStatusColors[s] + " border-current"
                                        : "border-border text-muted-foreground hover:text-foreground hover:bg-muted",
                                )}
                                aria-label={`Status: ${s}`}
                            >
                                {s === "IN PROGRESS" ? "In Progress" : s.charAt(0) + s.slice(1).toLowerCase()}
                            </button>
                        ))}
                    </div>

                    <div className="flex items-center gap-1">
                        {Object.values(TaskPriority).map((p) => (
                            <button
                                key={p}
                                type="button"
                                onClick={() => handlePriorityChange(p)}
                                className={cn(
                                    "px-2 py-1 text-[11px] font-medium rounded-sm border transition-colors",
                                    priority === p
                                        ? TaskPriorityColors[p] + " border-current"
                                        : "border-border text-muted-foreground hover:text-foreground hover:bg-muted",
                                )}
                                aria-label={`Priority: ${p}`}
                            >
                                {p.charAt(0) + p.slice(1).toLowerCase()}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <Calendar className="size-3.5 text-muted-foreground shrink-0" />
                    <input
                        type="date"
                        value={dueDate}
                        onChange={handleDueDateChange}
                        className="h-7 px-2 bg-muted border border-border text-[11px] text-foreground outline-none focus-visible:border-ring"
                        aria-label="Due date"
                    />
                    {dueDate && checkIsOverdue(dueDate) && (
                        <span className="text-[10px] text-red-500 font-medium">Overdue</span>
                    )}
                </div>

                <div className="flex items-center gap-1.5 flex-wrap">
                    {labels.map((label) => (
                        <span
                            key={label}
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-muted text-[10px] text-muted-foreground rounded-sm"
                        >
                            {label}
                            <button
                                type="button"
                                onClick={() => handleRemoveLabel(label)}
                                className="hover:text-foreground"
                                aria-label={`Remove label ${label}`}
                            >
                                <X className="size-2.5" />
                            </button>
                        </span>
                    ))}
                    <div className="flex items-center gap-1">
                        <input
                            type="text"
                            value={newLabel}
                            onChange={(e) => setNewLabel(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleAddLabel()}
                            placeholder="Add label…"
                            className="h-6 px-2 bg-muted border border-border text-[11px] text-foreground placeholder:text-muted-foreground outline-none focus-visible:border-ring w-20"
                            aria-label="Add label"
                        />
                        {newLabel && (
                            <Button variant="ghost" size="icon-xs" onClick={handleAddLabel}>
                                <Plus className="size-3" />
                            </Button>
                        )}
                    </div>
                </div>
            </div>

            <EditorToolbar editor={editorInstance} />

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
                <RichTextEditor
                    content={contentJson}
                    onUpdate={handleEditorUpdate}
                    editorRef={setEditorInstance}
                    editable={!isDeleted}
                    placeholder="Add description…"
                    editorClassName="h-full"
                />
            </div>

            <div className="border-t border-border px-4 py-3">
                <p className="text-[11px] font-medium text-muted-foreground mb-2">Checklist</p>
                <div className="space-y-1">
                    {checklist.map((item) => (
                        <div key={item.id} className="flex items-center gap-2 group">
                            <button
                                type="button"
                                onClick={() => handleToggleChecklistItem(item.id)}
                                className={cn(
                                    "size-4 shrink-0 rounded-sm border flex items-center justify-center transition-colors",
                                    item.completed
                                        ? "bg-primary border-primary text-primary-foreground"
                                        : "border-border hover:border-muted-foreground",
                                )}
                                aria-label={item.completed ? "Mark as incomplete" : "Mark as complete"}
                            >
                                {item.completed && <Circle className="size-2.5 fill-current" />}
                            </button>
                            <input
                                type="text"
                                value={item.text}
                                onChange={(e) => handleEditChecklistItem(item.id, e.target.value)}
                                className={cn(
                                    "flex-1 bg-transparent text-[11px] text-foreground outline-none border-none p-0",
                                    item.completed && "line-through text-muted-foreground",
                                )}
                                aria-label="Checklist item"
                            />
                            <button
                                type="button"
                                onClick={() => handleDeleteChecklistItem(item.id)}
                                className="opacity-0 group-hover:opacity-100 p-0.5 text-muted-foreground hover:text-destructive transition-opacity"
                                aria-label="Delete checklist item"
                            >
                                <X className="size-3" />
                            </button>
                        </div>
                    ))}
                    <div className="flex items-center gap-2">
                        <div className="size-4 shrink-0" />
                        <input
                            type="text"
                            value={newChecklistItem}
                            onChange={(e) => setNewChecklistItem(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleAddChecklistItem()}
                            placeholder="Add checklist item…"
                            className="flex-1 bg-transparent text-[11px] text-muted-foreground placeholder:text-muted-foreground outline-none border-none p-0"
                            aria-label="Add checklist item"
                        />
                        {newChecklistItem && (
                            <Button variant="ghost" size="icon-xs" onClick={handleAddChecklistItem}>
                                <Plus className="size-3" />
                            </Button>
                        )}
                    </div>
                </div>
            </div>

            <TaskActivityTimeline taskId={task?.id} />

            {/* Attachments — only shown for persisted tasks */}
            {task?.id && !isCreating && (
                <div className="border-t border-border px-4 py-3">
                    <p className="text-[11px] font-medium text-muted-foreground mb-3 flex items-center gap-1.5">
                        Attachments
                    </p>
                    <AttachmentPanelContainer
                        attachments={taskAttachments.data}
                        isLoading={taskAttachments.isLoading}
                        isError={taskAttachments.isError}
                        uploadMutation={uploadTaskAttachment}
                        deleteMutation={deleteTaskAttachment}
                        downloadFn={async (attachmentId) => {
                            const { data } = await attachmentsApi.downloadForTask(task.id, attachmentId)
                            return data
                        }}
                        readOnly={isDeleted}
                    />
                </div>
            )}
        </div>
    )
}
