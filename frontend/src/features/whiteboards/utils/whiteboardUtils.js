import dayjs from "dayjs"
import relativeTime from "dayjs/plugin/relativeTime"

dayjs.extend(relativeTime)

export function formatRelativeTime(isoString) {
    if (!isoString) return ""
    return dayjs(isoString).fromNow()
}

export function formatDate(isoString, format = "MMM D, YYYY") {
    if (!isoString) return ""
    return dayjs(isoString).format(format)
}

export function formatDateTime(isoString) {
    if (!isoString) return ""
    return dayjs(isoString).format("MMM D, YYYY h:mm A")
}

let elementIdCounter = 0

export function generateElementId() {
    elementIdCounter += 1
    return `el_${Date.now()}_${elementIdCounter}_${Math.random().toString(36).slice(2, 7)}`
}

export function createElement(type, attrs = {}) {
    return {
        id: generateElementId(),
        type,
        x: 0,
        y: 0,
        width: 0,
        height: 0,
        radius: 0,
        points: [],
        text: "",
        fontSize: 18,
        fill: "transparent",
        stroke: "#000000",
        strokeWidth: 2,
        rotation: 0,
        scaleX: 1,
        scaleY: 1,
        ...attrs,
    }
}
