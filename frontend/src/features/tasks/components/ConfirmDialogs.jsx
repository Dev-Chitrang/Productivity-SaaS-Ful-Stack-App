import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

export function DeleteTaskDialog({ open, onClose, onConfirm, isPending, taskTitle }) {
    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="max-w-sm" showCloseButton={false}>
                <DialogHeader>
                    <DialogTitle>Delete task</DialogTitle>
                    <DialogDescription>
                        {taskTitle ? (
                            <>
                                Move <span className="font-medium text-foreground">"{taskTitle}"</span> to trash?
                                You can restore it later.
                            </>
                        ) : (
                            "Move this task to trash? You can restore it later."
                        )}
                    </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                    <Button variant="outline" size="sm" onClick={onClose} disabled={isPending}>
                        Cancel
                    </Button>
                    <Button variant="destructive" size="sm" onClick={onConfirm} disabled={isPending}>
                        {isPending ? "Deleting…" : "Move to Trash"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

export function RestoreTaskDialog({ open, onClose, onConfirm, isPending, taskTitle }) {
    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="max-w-sm" showCloseButton={false}>
                <DialogHeader>
                    <DialogTitle>Restore task</DialogTitle>
                    <DialogDescription>
                        {taskTitle ? (
                            <>
                                Restore <span className="font-medium text-foreground">"{taskTitle}"</span>?
                            </>
                        ) : (
                            "Restore this task?"
                        )}
                    </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                    <Button variant="outline" size="sm" onClick={onClose} disabled={isPending}>
                        Cancel
                    </Button>
                    <Button variant="default" size="sm" onClick={onConfirm} disabled={isPending}>
                        {isPending ? "Restoring…" : "Restore"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

export function ArchiveTaskDialog({ open, onClose, onConfirm, isPending, taskTitle, currentlyArchived }) {
    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="max-w-sm" showCloseButton={false}>
                <DialogHeader>
                    <DialogTitle>{currentlyArchived ? "Unarchive task" : "Archive task"}</DialogTitle>
                    <DialogDescription>
                        {taskTitle ? (
                            <>
                                {currentlyArchived ? "Unarchive" : "Archive"}{" "}
                                <span className="font-medium text-foreground">"{taskTitle}"</span>?
                            </>
                        ) : (
                            `${currentlyArchived ? "Unarchive" : "Archive"} this task?`
                        )}
                    </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                    <Button variant="outline" size="sm" onClick={onClose} disabled={isPending}>
                        Cancel
                    </Button>
                    <Button variant="default" size="sm" onClick={onConfirm} disabled={isPending}>
                        {isPending ? `${currentlyArchived ? "Unarchiving" : "Archiving"}…` : `${currentlyArchived ? "Unarchive" : "Archive"}`}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
