import api from "@/lib/axios"

export const listTasks = (params) => {
    const clean = Object.fromEntries(
        Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""),
    )
    return api.get("/tasks", { params: clean })
}

export const getTask = (id) => api.get(`/tasks/${id}`)

export const createTask = (payload) => api.post("/tasks", payload)

export const updateTask = (id, payload) => api.patch(`/tasks/${id}`, payload)

export const deleteTask = (id) => api.delete(`/tasks/${id}`)

export const restoreTask = (id) => api.patch(`/tasks/${id}/restore`)

export const archiveTask = (id) => api.patch(`/tasks/${id}/archive`)

export const unarchiveTask = (id) => api.patch(`/tasks/${id}/unarchive`)

export const pinTask = (id) => api.patch(`/tasks/${id}/pin`)

export const unpinTask = (id) => api.patch(`/tasks/${id}/unpin`)

export const favoriteTask = (id) => api.patch(`/tasks/${id}/favorite`)

export const unfavoriteTask = (id) => api.patch(`/tasks/${id}/unfavorite`)

export const getTaskHistory = (id) => api.get(`/tasks/${id}/history`)
