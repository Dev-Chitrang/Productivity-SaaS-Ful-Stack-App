export const TaskStatus = Object.freeze({
    TODO: "TODO",
    IN_PROGRESS: "IN PROGRESS",
    DONE: "DONE",
})

export const TaskPriority = Object.freeze({
    LOW: "LOW",
    MEDIUM: "MEDIUM",
    HIGH: "HIGH",
})

export const TaskStatusColors = Object.freeze({
    [TaskStatus.TODO]: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
    [TaskStatus.IN_PROGRESS]: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
    [TaskStatus.DONE]: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
})

export const TaskPriorityColors = Object.freeze({
    [TaskPriority.LOW]: "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400",
    [TaskPriority.MEDIUM]: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
    [TaskPriority.HIGH]: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
})

export const TaskSortBy = Object.freeze({
    UPDATED_AT: "updated_at",
    CREATED_AT: "created_at",
    DUE_DATE: "due_date",
    TITLE: "title",
    PRIORITY: "priority",
})

export const TaskSortOrder = Object.freeze({
    ASC: "asc",
    DESC: "desc",
})
