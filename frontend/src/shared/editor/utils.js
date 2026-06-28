export function getEmptyDoc() {
    return {
        type: "doc",
        content: [{ type: "paragraph" }],
    }
}

export function noteHasContent(json) {
    if (!json) return false
    if (json.content && json.content.length > 0) {
        for (const node of json.content) {
            if (node.type === "paragraph") {
                if (node.content && node.content.length > 0) return true
            } else {
                return true
            }
        }
    }
    return false
}

export function extractTextFromContent(content) {
    if (!content) return ""
    const parsed = typeof content === "string" ? JSON.parse(content) : content
    let text = ""
    const walk = (nodes) => {
        if (!nodes) return
        for (const node of nodes) {
            if (node.type === "text" && node.text) text += node.text + " "
            if (node.content) walk(node.content)
        }
    }
    if (parsed.content) walk(parsed.content)
    return text.trim()
}
