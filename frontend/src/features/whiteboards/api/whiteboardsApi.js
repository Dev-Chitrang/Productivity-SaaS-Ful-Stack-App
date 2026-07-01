import api from "@/lib/axios"

export const listWhiteboards = (params) => {
    const clean = Object.fromEntries(
        Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""),
    )
    return api.get("/whiteboards", { params: clean })
}

export const getWhiteboard = (id) => api.get(`/whiteboards/${id}`)

export const createWhiteboard = (payload) => api.post("/whiteboards", payload)

export const renameWhiteboard = (id, payload) => api.patch(`/whiteboards/${id}`, payload)

export const autosaveWhiteboard = (id, payload) => api.patch(`/whiteboards/${id}/board`, payload)

export const toggleFavoriteWhiteboard = (id, isFavorite) =>
    api.patch(`/whiteboards/${id}/favorite`, null, { params: { is_favorite: isFavorite } })

export const toggleArchiveWhiteboard = (id, isArchived) =>
    api.patch(`/whiteboards/${id}/archive`, null, { params: { is_archived: isArchived } })

export const deleteWhiteboard = (id) => api.delete(`/whiteboards/${id}`)

export const restoreWhiteboard = (id) => api.patch(`/whiteboards/${id}/restore`)
