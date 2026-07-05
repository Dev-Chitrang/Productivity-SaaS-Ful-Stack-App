/**
 * AttachmentPanel — reusable attachment section used by Tasks, Calendar Events
 * and Meeting Sessions.
 *
 * The parent component calls the appropriate hooks and passes the results in.
 * This keeps hook calls at the top level of the consuming component (Rules of Hooks).
 *
 * Props
 * ─────
 * attachments       Attachment[] | undefined  — list data from useQuery
 * isLoading         boolean
 * isError           boolean
 * isUploading       boolean                   — uploadMutation.isPending
 * isDeletingId      string | null             — id of attachment being deleted
 * onUpload          (files: File[]) => void
 * onDownload        (attachment, preview: boolean) => Promise<void>
 * onDeleteRequest   (attachment) => void      — shows confirm dialog
 * readOnly          boolean                   — hides upload + delete
 * className         string
 */

import { useRef, useState, useCallback } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
    DialogDescription,
} from "@/components/ui/dialog"
import {
    Paperclip,
    UploadSimple,
    DownloadSimple,
    Trash,
    Spinner,
    FileText,
    FileImage,
    FilePdf,
    FileAudio,
    FileVideo,
    FileZip,
    FileCode,
    FileDoc,
    FileXls,
    WarningCircle,
    Eye,
} from "@phosphor-icons/react"
import { cn } from "@/lib/utils"
import {
    formatFileSize,
    formatUploadDate,
    getFileCategory,
    FileCategory,
    canPreviewInBrowser,
    triggerBlobDownload,
    openBlobInNewTab,
} from "../utils/attachmentHelpers"
import { validateFile } from "../hooks/useAttachmentsApi"
import toast from "react-hot-toast"

// ─── File icon by category ────────────────────────────────────────────────────

function FileIcon({ extension, className = "size-4" }) {
    const cat = getFileCategory(extension)
    const cls = cn(className, "shrink-0 text-muted-foreground")
    switch (cat) {
        case FileCategory.IMAGE: return <FileImage className={cls} />
        case FileCategory.PDF: return <FilePdf className={cls} />
        case FileCategory.AUDIO: return <FileAudio className={cls} />
        case FileCategory.VIDEO: return <FileVideo className={cls} />
        case FileCategory.ARCHIVE: return <FileZip className={cls} />
        case FileCategory.CODE: return <FileCode className={cls} />
        case FileCategory.DOCUMENT: return <FileDoc className={cls} />
        case FileCategory.SHEET: return <FileXls className={cls} />
        case FileCategory.SLIDE: return <FileDoc className={cls} />
        default: return <FileText className={cls} />
    }
}

// ─── Dropzone ─────────────────────────────────────────────────────────────────

function AttachmentDropzone({ onFiles, isUploading }) {
    const [dragging, setDragging] = useState(false)
    const inputRef = useRef(null)

    const processFiles = useCallback(
        (fileList) => {
            const valid = []
            for (const f of Array.from(fileList)) {
                const err = validateFile(f)
                if (err) {
                    toast.error(`${f.name}: ${err}`)
                } else {
                    valid.push(f)
                }
            }
            if (valid.length) onFiles(valid)
        },
        [onFiles],
    )

    const handleDrop = useCallback(
        (e) => {
            e.preventDefault()
            setDragging(false)
            if (!isUploading) processFiles(e.dataTransfer.files)
        },
        [processFiles, isUploading],
    )

    const handleDragOver = (e) => { e.preventDefault(); if (!isUploading) setDragging(true) }
    const handleDragLeave = () => setDragging(false)
    const handleInput = (e) => {
        if (e.target.files?.length) processFiles(e.target.files)
        e.target.value = ""
    }

    return (
        <div
            role="button"
            tabIndex={0}
            aria-label="Upload attachment — click or drag and drop files here"
            aria-disabled={isUploading}
            onClick={() => !isUploading && inputRef.current?.click()}
            onKeyDown={(e) =>
                (e.key === "Enter" || e.key === " ") && !isUploading && inputRef.current?.click()
            }
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={cn(
                "flex flex-col items-center justify-center gap-2 rounded border border-dashed px-4 py-5 text-center transition-colors select-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                isUploading
                    ? "cursor-not-allowed opacity-60 border-border"
                    : dragging
                        ? "border-primary bg-primary/5 cursor-copy"
                        : "border-border hover:border-primary/50 hover:bg-muted/40 cursor-pointer",
            )}
        >
            <input
                ref={inputRef}
                type="file"
                multiple
                className="sr-only"
                aria-hidden="true"
                tabIndex={-1}
                onChange={handleInput}
                disabled={isUploading}
            />
            {isUploading ? (
                <>
                    <Spinner className="size-5 animate-spin text-primary" />
                    <p className="text-xs text-muted-foreground">Uploading…</p>
                </>
            ) : (
                <>
                    <UploadSimple
                        className={cn("size-5 transition-colors", dragging ? "text-primary" : "text-muted-foreground")}
                    />
                    <div>
                        <p className="text-xs font-medium text-foreground">
                            Drop files here or{" "}
                            <span className="text-primary underline underline-offset-2">browse</span>
                        </p>
                        <p className="mt-0.5 text-[10px] text-muted-foreground">
                            Max 50 MB · PDF, images, documents, audio, video, archives
                        </p>
                    </div>
                </>
            )}
        </div>
    )
}

// ─── Delete confirmation dialog ───────────────────────────────────────────────

function DeleteConfirmDialog({ open, filename, onClose, onConfirm, isPending }) {
    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Delete attachment?</DialogTitle>
                    <DialogDescription>
                        <span className="font-medium text-foreground">{filename}</span>{" "}
                        will be permanently deleted. This cannot be undone.
                    </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                    <Button variant="outline" size="sm" onClick={onClose} disabled={isPending}>
                        Cancel
                    </Button>
                    <Button
                        variant="destructive"
                        size="sm"
                        onClick={onConfirm}
                        disabled={isPending}
                        aria-label="Confirm delete attachment"
                    >
                        {isPending
                            ? <Spinner className="size-3.5 animate-spin" />
                            : <Trash className="size-3.5" />
                        }
                        Delete
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

// ─── Single attachment row ────────────────────────────────────────────────────

function AttachmentCard({ attachment, onDownload, onDeleteRequest, readOnly, isDeleting }) {
    const previewable = canPreviewInBrowser(attachment.extension, attachment.content_type)

    return (
        <div className="flex items-center gap-3 px-3 py-2.5 text-xs">
            <FileIcon extension={attachment.extension} />

            <div className="min-w-0 flex-1">
                <p
                    className="truncate font-medium text-foreground"
                    title={attachment.original_filename}
                >
                    {attachment.original_filename}
                </p>
                <div className="mt-0.5 flex flex-wrap items-center gap-2 text-muted-foreground">
                    <span className="uppercase text-[10px]">{attachment.extension}</span>
                    <span>{formatFileSize(attachment.size)}</span>
                    <span>{formatUploadDate(attachment.created_at)}</span>
                </div>
            </div>

            <div className="flex shrink-0 items-center gap-0.5">
                {previewable && (
                    <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => onDownload(attachment, true)}
                        aria-label={`Preview ${attachment.original_filename}`}
                        title="Preview in browser"
                    >
                        <Eye className="size-3.5" />
                    </Button>
                )}
                <Button
                    variant="ghost"
                    size="icon-xs"
                    onClick={() => onDownload(attachment, false)}
                    aria-label={`Download ${attachment.original_filename}`}
                    title="Download"
                >
                    <DownloadSimple className="size-3.5" />
                </Button>
                {!readOnly && (
                    <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => onDeleteRequest(attachment)}
                        disabled={isDeleting}
                        aria-label={`Delete ${attachment.original_filename}`}
                        title="Delete"
                        className="text-destructive/70 hover:text-destructive"
                    >
                        {isDeleting
                            ? <Spinner className="size-3.5 animate-spin" />
                            : <Trash className="size-3.5" />
                        }
                    </Button>
                )}
            </div>
        </div>
    )
}

// ─── Skeleton list ────────────────────────────────────────────────────────────

function AttachmentListSkeleton() {
    return (
        <div className="divide-y divide-border rounded border border-border">
            {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2.5">
                    <Skeleton className="size-4 shrink-0 rounded" />
                    <div className="flex-1 space-y-1.5">
                        <Skeleton className="h-3 w-3/5" />
                        <Skeleton className="h-2.5 w-2/5" />
                    </div>
                    <Skeleton className="size-6 shrink-0 rounded" />
                </div>
            ))}
        </div>
    )
}

// ─── Main panel ──────────────────────────────────────────────────────────────

export function AttachmentPanel({
    attachments = [],
    isLoading = false,
    isError = false,
    isUploading = false,
    isDeletingId = null,
    onUpload,
    onDownload,
    onDeleteRequest,
    readOnly = false,
    className,
}) {
    return (
        <div className={cn("space-y-3", className)}>
            {!readOnly && (
                <AttachmentDropzone onFiles={onUpload} isUploading={isUploading} />
            )}

            {isLoading ? (
                <AttachmentListSkeleton />
            ) : isError ? (
                <div className="flex items-center gap-2 rounded border border-border px-3 py-4 text-xs text-muted-foreground">
                    <WarningCircle className="size-4 shrink-0 text-destructive/70" />
                    Failed to load attachments.
                </div>
            ) : attachments.length === 0 ? (
                <div className="flex flex-col items-center justify-center gap-2 py-6 text-center">
                    <div className="flex size-9 items-center justify-center rounded-full bg-muted">
                        <Paperclip className="size-4 text-muted-foreground" weight="light" />
                    </div>
                    <p className="text-xs font-medium text-foreground">No attachments uploaded.</p>
                    {!readOnly && (
                        <p className="text-[10px] text-muted-foreground">
                            Drag and drop files above or click to browse.
                        </p>
                    )}
                </div>
            ) : (
                <div className="divide-y divide-border rounded border border-border">
                    {attachments.map((a) => (
                        <AttachmentCard
                            key={a.id}
                            attachment={a}
                            onDownload={onDownload}
                            onDeleteRequest={onDeleteRequest}
                            readOnly={readOnly}
                            isDeleting={isDeletingId === a.id}
                        />
                    ))}
                </div>
            )}

            {!isLoading && !isError && attachments.length > 0 && (
                <p className="text-right text-[10px] tabular-nums text-muted-foreground">
                    {attachments.length} attachment{attachments.length !== 1 ? "s" : ""}
                </p>
            )}
        </div>
    )
}

// ─── Container: manages download state + delete dialog ───────────────────────
// Wraps AttachmentPanel with the imperative logic so consuming components
// stay declarative. Each module creates one of these by passing its own hooks.

export function AttachmentPanelContainer({
    // Query hook results (called at top level of parent)
    attachments,
    isLoading,
    isError,
    uploadMutation,
    deleteMutation,
    // Download function: (attachmentId: string) => Promise<Blob>
    downloadFn,
    readOnly = false,
    className,
}) {
    const [deleteTarget, setDeleteTarget] = useState(null)
    const [downloadingId, setDownloadingId] = useState(null)

    const handleUpload = useCallback(
        async (files) => {
            for (const file of files) {
                await uploadMutation.mutateAsync(file).catch(() => {
                    // onError toast already fired inside the mutation
                })
            }
        },
        [uploadMutation],
    )

    const handleDownload = useCallback(
        async (attachment, preview = false) => {
            if (downloadingId === attachment.id) return
            setDownloadingId(attachment.id)
            try {
                const blob = await downloadFn(attachment.id)
                if (preview && canPreviewInBrowser(attachment.extension, attachment.content_type)) {
                    openBlobInNewTab(blob, attachment.content_type)
                } else {
                    triggerBlobDownload(blob, attachment.original_filename)
                }
            } catch {
                toast.error("Failed to download attachment.")
            } finally {
                setDownloadingId(null)
            }
        },
        [downloadFn, downloadingId],
    )

    const handleConfirmDelete = useCallback(async () => {
        if (!deleteTarget) return
        await deleteMutation.mutateAsync(deleteTarget.id).catch(() => { })
        setDeleteTarget(null)
    }, [deleteTarget, deleteMutation])

    return (
        <>
            <AttachmentPanel
                attachments={attachments}
                isLoading={isLoading}
                isError={isError}
                isUploading={uploadMutation.isPending}
                isDeletingId={deleteMutation.isPending ? deleteTarget?.id : null}
                onUpload={handleUpload}
                onDownload={handleDownload}
                onDeleteRequest={setDeleteTarget}
                readOnly={readOnly}
                className={className}
            />
            <DeleteConfirmDialog
                open={!!deleteTarget}
                filename={deleteTarget?.original_filename}
                onClose={() => setDeleteTarget(null)}
                onConfirm={handleConfirmDelete}
                isPending={deleteMutation.isPending}
            />
        </>
    )
}
