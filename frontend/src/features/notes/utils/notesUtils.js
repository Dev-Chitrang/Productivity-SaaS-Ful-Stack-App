import dayjs from "dayjs"
import relativeTime from "dayjs/plugin/relativeTime"

dayjs.extend(relativeTime)

export function formatRelativeTime(isoString) {
    return dayjs(isoString).fromNow()
}

export function formatDate(isoString, format = "MMM D, YYYY h:mm A") {
    return dayjs(isoString).format(format)
}

export { getEmptyDoc, noteHasContent, extractTextFromContent } from "@/shared/editor"
