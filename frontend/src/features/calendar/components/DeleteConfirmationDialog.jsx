import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

/**
 * @param {Object} props
 * @param {boolean} props.open
 * @param {() => void} props.onClose
 * @param {() => void} props.onConfirm
 * @param {boolean} [props.isPending]
 * @param {string} [props.eventTitle]
 */
export function DeleteConfirmationDialog({ open, onClose, onConfirm, isPending = false, eventTitle }) {
    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="max-w-sm" showCloseButton={false}>
                <DialogHeader>
                    <DialogTitle>Delete event</DialogTitle>
                    <DialogDescription>
                        {eventTitle ? (
                            <>
                                Are you sure you want to delete{" "}
                                <span className="font-medium text-foreground">"{eventTitle}"</span>?
                                This action cannot be undone.
                            </>
                        ) : (
                            "Are you sure you want to delete this event? This action cannot be undone."
                        )}
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
                    >
                        {isPending ? "Deleting…" : "Delete"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
