import { useCallback } from "react"
import {
    Bold, Italic, Underline, Strikethrough,
    Heading1, Heading2, Heading3,
    List, ListOrdered, ListChecks,
    Quote, Code2, Table, Minus,
    Undo2, Redo2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"

export function NoteToolbar({ editor }) {
    const addTable = useCallback(() => {
        if (!editor) return
        editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
    }, [editor])

    if (!editor) return null

    const groups = [
        [
            { icon: Undo2, action: () => editor.chain().focus().undo().run(), label: "Undo", disabled: !editor.can().undo() },
            { icon: Redo2, action: () => editor.chain().focus().redo().run(), label: "Redo", disabled: !editor.can().redo() },
        ],
        [
            { icon: Heading1, action: () => editor.chain().focus().toggleHeading({ level: 1 }).run(), label: "Heading 1", active: editor.isActive("heading", { level: 1 }) },
            { icon: Heading2, action: () => editor.chain().focus().toggleHeading({ level: 2 }).run(), label: "Heading 2", active: editor.isActive("heading", { level: 2 }) },
            { icon: Heading3, action: () => editor.chain().focus().toggleHeading({ level: 3 }).run(), label: "Heading 3", active: editor.isActive("heading", { level: 3 }) },
        ],
        [
            { icon: Bold, action: () => editor.chain().focus().toggleBold().run(), label: "Bold", active: editor.isActive("bold") },
            { icon: Italic, action: () => editor.chain().focus().toggleItalic().run(), label: "Italic", active: editor.isActive("italic") },
            { icon: Underline, action: () => editor.chain().focus().toggleUnderline().run(), label: "Underline", active: editor.isActive("underline") },
            { icon: Strikethrough, action: () => editor.chain().focus().toggleStrike().run(), label: "Strike", active: editor.isActive("strike") },
        ],
        [
            { icon: List, action: () => editor.chain().focus().toggleBulletList().run(), label: "Bullet List", active: editor.isActive("bulletList") },
            { icon: ListOrdered, action: () => editor.chain().focus().toggleOrderedList().run(), label: "Ordered List", active: editor.isActive("orderedList") },
            { icon: ListChecks, action: () => editor.chain().focus().toggleTaskList().run(), label: "Checklist", active: editor.isActive("taskList") },
        ],
        [
            { icon: Quote, action: () => editor.chain().focus().toggleBlockquote().run(), label: "Blockquote", active: editor.isActive("blockquote") },
            { icon: Code2, action: () => editor.chain().focus().toggleCodeBlock().run(), label: "Code Block", active: editor.isActive("codeBlock") },
            { icon: Table, action: addTable, label: "Table" },
            { icon: Minus, action: () => editor.chain().focus().setHorizontalRule().run(), label: "Horizontal Rule" },
        ],
    ]

    return (
        <div className="flex flex-wrap items-center gap-0.5 px-3 py-1.5 border-b border-border bg-muted/30 overflow-x-auto">
            {groups.map((group, gi) => (
                <div key={gi} className="flex items-center gap-0.5">
                    {gi > 0 && <Separator orientation="vertical" className="h-5 mx-1" />}
                    {group.map((btn, bi) => (
                        <Button
                            key={bi}
                            variant={btn.active ? "secondary" : "ghost"}
                            size="icon-xs"
                            onClick={btn.action}
                            disabled={btn.disabled}
                            title={btn.label}
                            aria-label={btn.label}
                        >
                            <btn.icon className="size-3.5" />
                        </Button>
                    ))}
                </div>
            ))}
        </div>
    )
}
