import dayjs from "dayjs"
import relativeTime from "dayjs/plugin/relativeTime"

dayjs.extend(relativeTime)

const fieldLabels = {
    title: "Title",
    status: "Status",
    priority: "Priority",
    description: "Description",
    due_date: "Due Date",
    labels: "Labels",
    is_archived: "Archived",
    is_pinned: "Pinned",
    is_favorite: "Favorite",
}

const actionLabels = {
    CREATED: "Created task",
    UPDATED: "Updated",
    DELETED: "Deleted task",
    RESTORED: "Restored task",
    ARCHIVED: "Archived task",
    UNARCHIVED: "Unarchived task",
    PINNED: "Pinned task",
    UNPINNED: "Unpinned task",
    FAVORITED: "Favorited task",
    UNFAVORITED: "Unfavorited task",
}

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

export function formatFieldName(field) {
    if (!field) return ""
    return fieldLabels[field] || field
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function formatActionLabel(action, fieldName) {
    if (!action) return ""
    if (action === "UPDATED" && fieldName) {
        return `Updated ${formatFieldName(fieldName).toLowerCase()}`
    }
    return actionLabels[action] || action
}

export function formatFieldValue(field, value) {
    if (value === null || value === undefined) return "\u2014"
    if (field === "status") {
        return value === "IN PROGRESS" ? "In Progress" : value.charAt(0) + value.slice(1).toLowerCase()
    }
    if (field === "priority") {
        return value.charAt(0) + value.slice(1).toLowerCase()
    }
    if (field === "due_date") {
        return formatDate(value)
    }
    if (field === "is_archived" || field === "is_pinned" || field === "is_favorite") {
        return value === "True" ? "Yes" : "No"
    }
    if (field === "description") {
        return value
    }
    if (typeof value === "string" && value.length > 60) return value.slice(0, 60) + "\u2026"
    return value
}

export function isOverdue(dueDate) {
    if (!dueDate) return false
    return dayjs(dueDate).isBefore(dayjs(), "day")
}

export function isDueToday(dueDate) {
    if (!dueDate) return false
    return dayjs(dueDate).isSame(dayjs(), "day")
}


