import dayjs from "dayjs"
import relativeTime from "dayjs/plugin/relativeTime"

dayjs.extend(relativeTime)

export function formatRelativeTime(isoString) {
    return dayjs(isoString).fromNow()
}

export function formatDate(isoString, format = "MMM D, YYYY h:mm A") {
    return dayjs(isoString).format(format)
}

export function extractTitleFromContent(content) {
    try {
        const parsed = JSON.parse(content)
        if (parsed?.content?.[0]?.content?.[0]?.text) {
            return parsed.content[0].content[0].text.slice(0, 100)
        }
    } catch {
        return ""
    }
    return ""
}

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
