import { useEffect, useRef } from "react"
import { useEditor, EditorContent } from "@tiptap/react"
import { getExtensions } from "./extensions"
import { getEmptyDoc } from "./utils"
import { cn } from "@/lib/utils"

export function RichTextEditor({
    content,
    onUpdate,
    editable = true,
    placeholder = "Start writing…",
    editorRef,
    className,
    editorClassName,
}) {
    const isExternalUpdate = useRef(false)
    const onUpdateRef = useRef(onUpdate)
    const prevContentRef = useRef(content)

    useEffect(() => { onUpdateRef.current = onUpdate }, [onUpdate])

    const editor = useEditor({
        extensions: getExtensions(placeholder),
        content: content || getEmptyDoc(),
        onUpdate: ({ editor: ed }) => {
            if (isExternalUpdate.current) return
            onUpdateRef.current?.(ed.getJSON())
        },
        editable,
        editorProps: {
            attributes: {
                class: "prose prose-sm max-w-none focus:outline-none min-h-[300px] text-xs",
            },
        },
    })

    useEffect(() => {
        if (editor) {
            editorRef?.(editor)
        }
    }, [editor, editorRef])

    useEffect(() => {
        if (!editor || !content) return
        if (prevContentRef.current === content) return
        prevContentRef.current = content
        isExternalUpdate.current = true
        editor.commands.setContent(content)
        isExternalUpdate.current = false
    }, [editor, content])

    useEffect(() => {
        if (editor && editable !== undefined) {
            editor.setEditable(editable)
        }
    }, [editor, editable])

    if (!editor) return null

    return (
        <div className={cn("", className)}>
            <EditorContent editor={editor} className={cn(editorClassName)} />
        </div>
    )
}
