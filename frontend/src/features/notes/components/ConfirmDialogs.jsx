import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

export function DeleteNoteDialog({ open, onClose, onConfirm, isPending, noteTitle }) {
    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="max-w-sm" showCloseButton={false}>
                <DialogHeader>
                    <DialogTitle>Delete note</DialogTitle>
                    <DialogDescription>
                        {noteTitle ? (
                            <>
                                Move <span className="font-medium text-foreground">"{noteTitle}"</span> to trash?
                                You can restore it later.
                            </>
                        ) : (
                            "Move this note to trash? You can restore it later."
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

export function RestoreNoteDialog({ open, onClose, onConfirm, isPending, noteTitle }) {
    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="max-w-sm" showCloseButton={false}>
                <DialogHeader>
                    <DialogTitle>Restore note</DialogTitle>
                    <DialogDescription>
                        {noteTitle ? (
                            <>
                                Restore <span className="font-medium text-foreground">"{noteTitle}"</span>?
                            </>
                        ) : (
                            "Restore this note?"
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

export function ArchiveNoteDialog({ open, onClose, onConfirm, isPending, noteTitle, currentlyArchived }) {
    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="max-w-sm" showCloseButton={false}>
                <DialogHeader>
                    <DialogTitle>{currentlyArchived ? "Unarchive note" : "Archive note"}</DialogTitle>
                    <DialogDescription>
                        {noteTitle ? (
                            <>
                                {currentlyArchived ? "Unarchive" : "Archive"}{" "}
                                <span className="font-medium text-foreground">"{noteTitle}"</span>?
                            </>
                        ) : (
                            `${currentlyArchived ? "Unarchive" : "Archive"} this note?`
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
