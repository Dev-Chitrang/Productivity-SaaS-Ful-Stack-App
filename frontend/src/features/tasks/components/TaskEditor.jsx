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
import { LinkedMeetingsPanel } from "./LinkedMeetingsPanel"
import {
    ArrowLeft, Pencil, Plus, Pin, Star, Archive, Trash2, RotateCcw,
    X, Calendar, Save, AlertCircle, History, Paperclip, Video, ListTodo,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { TaskStatus, TaskPriority, TaskStatusColors, TaskPriorityColors } from "../api/tasksTypes"
import { isOverdue as checkIsOverdue } from "../utils/tasksUtils"

const TABS = [
    { id: "activity", label: "Activity", icon: History },
    { id: "attachments", label: "Attachments", icon: Paperclip },
    { id: "meetings", label: "Related Meetings", icon: Video },
]

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
    const [isEditing, setIsEditing] = useState(false)
    const [title, setTitle] = useState("")
    const [status, setStatus] = useState("TODO")
    const [priority, setPriority] = useState("MEDIUM")
    const [dueDate, setDueDate] = useState("")
    const [newLabel, setNewLabel] = useState("")
    const [labels, setLabels] = useState([])
    const [editorInstance, setEditorInstance] = useState(null)
    const [descriptionContent, setDescriptionContent] = useState(null)
    const [activeTab, setActiveTab] = useState("activity")

    const initialSnapshot = useRef(null)
    const prevTaskId = useRef(task?.id)

    const isDeleted = task ? !!task.deleted_at : false
    const isOverdue = useMemo(() => {
        if (!task?.due_date) return false
        return checkIsOverdue(task.due_date)
    }, [task])

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
            setDescriptionContent(snapshot.description)
            setIsEditing(false)
            setActiveTab("activity")
            prevTaskId.current = task.id
        } else if (isCreating) {
            initialSnapshot.current = null
            setTitle("")
            setStatus("TODO")
            setPriority("MEDIUM")
            setDueDate("")
            setLabels([])
            setDescriptionContent(getEmptyDoc())
            setIsEditing(true)
            setActiveTab("activity")
            prevTaskId.current = null
        }
    }, [task?.id, task?.title, task?.status, task?.priority, task?.due_date, task?.labels, task?.description, isCreating])

    const isDirty = useMemo(() => {
        if (!initialSnapshot.current) return false
        const init = initialSnapshot.current
        if (title !== init.title) return true
        if (status !== init.status) return true
        if (priority !== init.priority) return true
        if (dueDate !== init.dueDate) return true
        if (JSON.stringify(labels) !== JSON.stringify(init.labels)) return true
        if (JSON.stringify(descriptionContent) !== JSON.stringify(init.description)) return true
        return false
    }, [title, status, priority, dueDate, labels, descriptionContent])

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

    const handleTitleChange = (e) => setTitle(e.target.value)
    const handleStatusChange = (newStatus) => setStatus(newStatus)
    const handlePriorityChange = (newPriority) => setPriority(newPriority)
    const handleDueDateChange = (e) => setDueDate(e.target.value)
    const handleAddLabel = () => {
        const trimmed = newLabel.trim().toLowerCase()
        if (!trimmed || labels.includes(trimmed)) return
        setLabels([...labels, trimmed])
        setNewLabel("")
    }
    const handleRemoveLabel = (label) => setLabels(labels.filter((l) => l !== label))

    const handleSaveClick = () => {
        if (!canSave || isSaving) return
        onSave?.({
            title: title || null,
            description: descriptionContent || getEmptyDoc(),
            status,
            priority,
            due_date: dueDate || null,
            labels,
        })
    }

    const handleCancel = () => {
        if (isCreating) {
            onBack?.()
            return
        }
        const init = initialSnapshot.current
        if (init) {
            setTitle(init.title)
            setStatus(init.status)
            setPriority(init.priority)
            setDueDate(init.dueDate)
            setLabels([...init.labels])
            setDescriptionContent(JSON.parse(JSON.stringify(init.description)))
        }
        setIsEditing(false)
    }

    const handleStartEditing = () => setIsEditing(true)

    const handleTogglePin = () => {
        if (task) onTogglePin?.({ id: task.id, currentlyPinned: task.is_pinned })
    }
    const handleToggleFavorite = () => {
        if (task) onToggleFavorite?.({ id: task.id, currentlyFavorited: task.is_favorite })
    }
    const handleArchive = () => { if (task) onArchive?.(task) }
    const handleDelete = () => { if (task) onDelete?.(task) }
    const handleRestore = () => { if (task) onRestore?.(task) }

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

    // ──── Sub-renders ────

    const renderMetadataDisplay = () => (
        <div className="space-y-4">
            <div>
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1.5">Status</p>
                <span className={cn(
                    "inline-flex items-center px-2 py-0.5 text-[11px] font-medium rounded-sm",
                    TaskStatusColors[status],
                )}>
                    {status === "IN PROGRESS" ? "In Progress" : status.charAt(0) + status.slice(1).toLowerCase()}
                </span>
            </div>
            <div>
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1.5">Priority</p>
                <span className={cn(
                    "inline-flex items-center px-2 py-0.5 text-[11px] font-medium rounded-sm",
                    TaskPriorityColors[priority],
                )}>
                    {priority.charAt(0) + priority.slice(1).toLowerCase()}
                </span>
            </div>
            <div>
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1.5">Due Date</p>
                <div className="flex items-center gap-1.5">
                    {dueDate ? (
                        <>
                            <Calendar className="size-3 text-muted-foreground shrink-0" />
                            <span className="text-xs text-foreground">{dueDate}</span>
                            {checkIsOverdue(dueDate) && (
                                <span className="text-[10px] text-red-500 font-medium">Overdue</span>
                            )}
                        </>
                    ) : (
                        <span className="text-xs text-muted-foreground/60 italic">None set</span>
                    )}
                </div>
            </div>
            <div>
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1.5">Tags</p>
                {labels.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                        {labels.map((label) => (
                            <span key={label} className="inline-flex items-center px-1.5 py-0.5 bg-muted text-[10px] text-muted-foreground rounded-sm">
                                {label}
                            </span>
                        ))}
                    </div>
                ) : (
                    <span className="text-xs text-muted-foreground/60 italic">No tags</span>
                )}
            </div>
        </div>
    )

    const renderEditableMetadata = () => (
        <div className="space-y-3">
            <div>
                <p className="text-[10px] font-medium text-muted-foreground mb-1">Status</p>
                <div className="flex items-center gap-1 flex-wrap">
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
                        >
                            {s === "IN PROGRESS" ? "In Progress" : s.charAt(0) + s.slice(1).toLowerCase()}
                        </button>
                    ))}
                </div>
            </div>
            <div>
                <p className="text-[10px] font-medium text-muted-foreground mb-1">Priority</p>
                <div className="flex items-center gap-1 flex-wrap">
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
                        >
                            {p.charAt(0) + p.slice(1).toLowerCase()}
                        </button>
                    ))}
                </div>
            </div>
            <div>
                <p className="text-[10px] font-medium text-muted-foreground mb-1">Due Date</p>
                <div className="flex items-center gap-2">
                    <Calendar className="size-3.5 text-muted-foreground shrink-0" />
                    <input
                        type="date"
                        value={dueDate}
                        onChange={handleDueDateChange}
                        className="h-7 px-2 bg-muted border border-border text-[11px] text-foreground outline-none focus-visible:border-ring"
                    />
                    {dueDate && checkIsOverdue(dueDate) && (
                        <span className="text-[10px] text-red-500 font-medium">Overdue</span>
                    )}
                </div>
            </div>
            <div>
                <p className="text-[10px] font-medium text-muted-foreground mb-1">Tags</p>
                <div className="flex items-center gap-1.5 flex-wrap">
                    {labels.map((label) => (
                        <span key={label} className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-muted text-[10px] text-muted-foreground rounded-sm">
                            {label}
                            <button type="button" onClick={() => handleRemoveLabel(label)} className="hover:text-foreground">
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
                            placeholder="Add tag…"
                            className="h-6 px-2 bg-muted border border-border text-[11px] text-foreground placeholder:text-muted-foreground outline-none focus-visible:border-ring w-20"
                        />
                        {newLabel && (
                            <Button variant="ghost" size="icon-xs" onClick={handleAddLabel}>
                                <Plus className="size-3" />
                            </Button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )

    const renderTabContent = () => {
        switch (activeTab) {
            case "activity":
                return <TaskActivityTimeline taskId={task?.id} />
            case "attachments":
                return task?.id ? (
                    <div className="py-3">
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
                ) : null
            case "meetings":
                return task?.id ? <LinkedMeetingsPanel taskId={task.id} /> : null
            default:
                return null
        }
    }

    const showTabs = !isEditing && !isCreating && task?.id
    const showEditButton = !isEditing && !isCreating && !isDeleted
    const showActionButtons = !isDeleted && !isEditing && !isCreating

    return (
        <div className="flex flex-col">
            {/*** Header ***/}
            <div className="flex items-center justify-between px-4 py-2 border-b border-border gap-2 sticky top-0 bg-background z-10">
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
                    {showEditButton && (
                        <Button variant="ghost" size="icon-xs" onClick={handleStartEditing} title="Edit task">
                            <Pencil className="size-3.5" />
                        </Button>
                    )}
                    {showActionButtons && (
                        <>
                            <Button variant="ghost" size="icon-xs" onClick={handleTogglePin} className={task.is_pinned ? "text-amber-600" : ""} title={task.is_pinned ? "Unpin" : "Pin"}>
                                <Pin className="size-3.5" />
                            </Button>
                            <Button variant="ghost" size="icon-xs" onClick={handleToggleFavorite} className={task.is_favorite ? "text-amber-500" : ""} title={task.is_favorite ? "Remove from favorites" : "Add to favorites"}>
                                <Star className="size-3.5" />
                            </Button>
                            <Button variant="ghost" size="icon-xs" onClick={handleArchive} title={task.is_archived ? "Unarchive" : "Archive"}>
                                <Archive className="size-3.5" />
                            </Button>
                            <Button variant="ghost" size="icon-xs" onClick={handleDelete} className="text-destructive hover:text-destructive" title="Delete">
                                <Trash2 className="size-3.5" />
                            </Button>
                        </>
                    )}
                    {isDeleted && (
                        <Button variant="ghost" size="icon-xs" onClick={handleRestore} className="text-green-600 hover:text-green-700" title="Restore">
                            <RotateCcw className="size-3.5" />
                        </Button>
                    )}
                    {(isEditing || isCreating) && (
                        <>
                            <Button variant="ghost" size="sm" onClick={handleCancel} disabled={isSaving}>
                                <X className="size-3.5 mr-1" />
                                Cancel
                            </Button>
                            <Button size="sm" onClick={handleSaveClick} disabled={!canSave || isSaving}>
                                <Save className="size-3.5 mr-1" />
                                {isSaving ? "Saving\u2026" : isCreating ? "Create" : "Save"}
                            </Button>
                        </>
                    )}
                </div>
            </div>

            {/*** Edit / Create Mode ***/}
            {(isEditing || isCreating) ? (
                <div>
                    {!isCreating && (
                        <div className="px-4 pt-3 pb-2 border-b border-border">
                            <input
                                type="text"
                                value={title}
                                onChange={handleTitleChange}
                                placeholder="Task title\u2026"
                                className="w-full bg-transparent text-sm font-medium text-foreground placeholder:text-muted-foreground outline-none border-none p-0"
                            />
                        </div>
                    )}
                    {isCreating && (
                        <div className="px-4 pt-3 pb-2 border-b border-border">
                            <input
                                type="text"
                                value={title}
                                onChange={handleTitleChange}
                                placeholder="Task title\u2026"
                                className="w-full bg-transparent text-sm font-medium text-foreground placeholder:text-muted-foreground outline-none border-none p-0"
                                autoFocus
                            />
                        </div>
                    )}
                    <div className="px-4 py-3 space-y-4">
                        {renderEditableMetadata()}
                    </div>
                    <EditorToolbar editor={editorInstance} />
                    <div className="px-4 py-3">
                        <RichTextEditor
                            content={descriptionContent}
                            onUpdate={handleEditorUpdate}
                            editorRef={setEditorInstance}
                            editable={!isDeleted}
                            placeholder="Add description\u2026"
                            editorClassName="[&_.ProseMirror]:!min-h-0"
                        />
                    </div>
                </div>
            ) : (
                /*** Normal Mode ***/ 
                <div>
                    {/* Title */}
                    <div className="px-4 pt-3 pb-2 border-b border-border">
                        <h2 className="text-sm font-medium text-foreground">{task?.title || title}</h2>
                    </div>

                    {/* Description + Sidebar */}
                    <div className="lg:grid lg:grid-cols-[1fr_220px]">
                        <div className="min-w-0 px-4 py-3">
                            <RichTextEditor
                                content={contentJson}
                                onUpdate={handleEditorUpdate}
                                editorRef={setEditorInstance}
                                editable={false}
                                placeholder="Add description\u2026"
                                editorClassName="[&_.ProseMirror]:!min-h-0 [&_.ProseMirror]:cursor-default"
                            />
                        </div>
                        <div className="border-t lg:border-t-0 lg:border-l border-border px-4 py-3">
                            {renderMetadataDisplay()}
                        </div>
                    </div>

                    {/* Tabs */}
                    {showTabs && (
                        <div className="border-t border-border">
                            <div className="flex border-b border-border overflow-x-auto">
                                {TABS.map((tab) => (
                                    <button
                                        key={tab.id}
                                        type="button"
                                        onClick={() => setActiveTab(tab.id)}
                                        className={cn(
                                            "flex items-center gap-1.5 px-3 py-2 text-[11px] font-medium whitespace-nowrap border-b-2 transition-colors -mb-px",
                                            activeTab === tab.id
                                                ? "border-primary text-foreground"
                                                : "border-transparent text-muted-foreground hover:text-foreground",
                                        )}
                                    >
                                        <tab.icon className="size-3" />
                                        {tab.label}
                                    </button>
                                ))}
                            </div>
                            <div>
                                {renderTabContent()}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
