import api from "@/lib/axios"

export const listNotes = (params) => {
    const clean = Object.fromEntries(
        Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""),
    )
    return api.get("/notes", { params: clean })
}

export const getNote = (id) => api.get(`/notes/${id}`)

export const createNote = (payload) => api.post("/notes", payload)

export const updateNote = (id, payload) => api.patch(`/notes/${id}`, payload)

export const deleteNote = (id) => api.delete(`/notes/${id}`)

export const restoreNote = (id) => api.patch(`/notes/${id}/restore`)

export const archiveNote = (id) => api.patch(`/notes/${id}/archive`)

export const unarchiveNote = (id) => api.patch(`/notes/${id}/unarchive`)

export const pinNote = (id) => api.patch(`/notes/${id}/pin`)

export const unpinNote = (id) => api.patch(`/notes/${id}/unpin`)

export const favoriteNote = (id) => api.patch(`/notes/${id}/favorite`)

export const unfavoriteNote = (id) => api.patch(`/notes/${id}/unfavorite`)
