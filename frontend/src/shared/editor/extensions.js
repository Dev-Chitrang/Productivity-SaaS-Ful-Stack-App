import StarterKit from "@tiptap/starter-kit"
import Underline from "@tiptap/extension-underline"
import TaskList from "@tiptap/extension-task-list"
import TaskItem from "@tiptap/extension-task-item"
import { Table } from "@tiptap/extension-table"
import TableRow from "@tiptap/extension-table-row"
import TableCell from "@tiptap/extension-table-cell"
import TableHeader from "@tiptap/extension-table-header"
import Placeholder from "@tiptap/extension-placeholder"

const extensions = [
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
]

export function getExtensions(placeholder) {
    return [
        ...extensions,
        Placeholder.configure({
            placeholder: placeholder || "Start writing…",
        }),
    ]
}
