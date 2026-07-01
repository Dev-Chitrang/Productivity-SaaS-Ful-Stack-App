import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

export function DeleteBoardDialog({ open, onClose, onConfirm, isPending, boardTitle }) {
    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="max-w-sm" showCloseButton={false}>
                <DialogHeader>
                    <DialogTitle>Delete whiteboard</DialogTitle>
                    <DialogDescription>
                        {boardTitle ? (
                            <>
                                Move <span className="font-medium text-foreground">"{boardTitle}"</span> to trash?
                                You can restore it later.
                            </>
                        ) : (
                            "Move this whiteboard to trash? You can restore it later."
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

export function RestoreBoardDialog({ open, onClose, onConfirm, isPending, boardTitle }) {
    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="max-w-sm" showCloseButton={false}>
                <DialogHeader>
                    <DialogTitle>Restore whiteboard</DialogTitle>
                    <DialogDescription>
                        {boardTitle ? (
                            <>
                                Restore <span className="font-medium text-foreground">"{boardTitle}"</span>?
                            </>
                        ) : (
                            "Restore this whiteboard?"
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

export function ArchiveBoardDialog({ open, onClose, onConfirm, isPending, boardTitle, currentlyArchived }) {
    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="max-w-sm" showCloseButton={false}>
                <DialogHeader>
                    <DialogTitle>{currentlyArchived ? "Unarchive whiteboard" : "Archive whiteboard"}</DialogTitle>
                    <DialogDescription>
                        {boardTitle ? (
                            <>
                                {currentlyArchived ? "Unarchive" : "Archive"}{" "}
                                <span className="font-medium text-foreground">"{boardTitle}"</span>?
                            </>
                        ) : (
                            `${currentlyArchived ? "Unarchive" : "Archive"} this whiteboard?`
                        )}
                    </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                    <Button variant="outline" size="sm" onClick={onClose} disabled={isPending}>
                        Cancel
                    </Button>
                    <Button variant="default" size="sm" onClick={onConfirm} disabled={isPending}>
                        {isPending
                            ? `${currentlyArchived ? "Unarchiving" : "Archiving"}…`
                            : `${currentlyArchived ? "Unarchive" : "Archive"}`}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
