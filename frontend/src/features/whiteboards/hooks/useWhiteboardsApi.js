import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import toast from "react-hot-toast"
import * as whiteboardsApi from "../api/whiteboardsApi"
import { LIST_STALE_TIME, BOARD_STALE_TIME } from "../constants"

export const whiteboardsKeys = {
    all: () => ["whiteboards"],
    lists: () => [...whiteboardsKeys.all(), "list"],
    list: (filters) => [...whiteboardsKeys.lists(), filters],
    details: () => [...whiteboardsKeys.all(), "detail"],
    detail: (id) => [...whiteboardsKeys.details(), id],
}

export function useWhiteboards(filters = {}) {
    return useQuery({
        queryKey: whiteboardsKeys.list(filters),
        queryFn: async () => {
            const { data } = await whiteboardsApi.listWhiteboards(filters)
            return data
        },
        staleTime: LIST_STALE_TIME,
    })
}

export function useWhiteboard(id) {
    return useQuery({
        queryKey: whiteboardsKeys.detail(id),
        queryFn: async () => {
            const { data } = await whiteboardsApi.getWhiteboard(id)
            return data
        },
        enabled: !!id,
        staleTime: BOARD_STALE_TIME,
    })
}

export function useCreateWhiteboard(onSuccessCb) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload) => whiteboardsApi.createWhiteboard(payload),
        onSuccess: ({ data }) => {
            qc.invalidateQueries({ queryKey: whiteboardsKeys.lists() })
            toast.success("Whiteboard created.")
            onSuccessCb?.(data)
        },
        onError: (err) => {
            const detail = err?.response?.data?.detail
            const msg = Array.isArray(detail)
                ? detail.map((d) => d.msg ?? d).join("; ")
                : detail || "Failed to create whiteboard."
            toast.error(msg)
        },
    })
}

export function useRenameWhiteboard() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ id, payload }) => whiteboardsApi.renameWhiteboard(id, payload),
        onSuccess: (_data, { id }) => {
            qc.invalidateQueries({ queryKey: whiteboardsKeys.lists() })
            qc.invalidateQueries({ queryKey: whiteboardsKeys.detail(id) })
            toast.success("Whiteboard renamed.")
        },
        onError: (err) => {
            toast.error(err?.response?.data?.detail || "Failed to rename whiteboard.")
        },
    })
}

export function useAutosaveWhiteboard() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ id, payload }) => whiteboardsApi.autosaveWhiteboard(id, payload),
        onSuccess: (_data, { id }) => {
            qc.invalidateQueries({ queryKey: whiteboardsKeys.detail(id) })
            qc.invalidateQueries({ queryKey: whiteboardsKeys.lists() })
        },
        onError: () => {
            // Silently fail for autosave
        },
    })
}

export function useDeleteWhiteboard(onSuccessCb) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (id) => whiteboardsApi.deleteWhiteboard(id),
        onSuccess: (_data, id) => {
            qc.invalidateQueries({ queryKey: whiteboardsKeys.all() })
            toast.success("Whiteboard moved to trash.")
            onSuccessCb?.(id)
        },
        onError: (err) => {
            toast.error(err?.response?.data?.detail || "Failed to delete whiteboard.")
        },
    })
}

export function useRestoreWhiteboard(onSuccessCb) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (id) => whiteboardsApi.restoreWhiteboard(id),
        onSuccess: (_data, id) => {
            qc.invalidateQueries({ queryKey: whiteboardsKeys.all() })
            toast.success("Whiteboard restored.")
            onSuccessCb?.(id)
        },
        onError: (err) => {
            toast.error(err?.response?.data?.detail || "Failed to restore whiteboard.")
        },
    })
}

export function useToggleFavorite() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ id, currentlyFavorited }) =>
            whiteboardsApi.toggleFavoriteWhiteboard(id, !currentlyFavorited),
        onMutate: async ({ id, currentlyFavorited }) => {
            await qc.cancelQueries({ queryKey: whiteboardsKeys.detail(id) })
            const prev = qc.getQueryData(whiteboardsKeys.detail(id))
            qc.setQueryData(whiteboardsKeys.detail(id), (old) =>
                old ? { ...old, is_favorite: !currentlyFavorited } : old,
            )
            return { prev, id }
        },
        onSuccess: (_data, { id }) => {
            qc.invalidateQueries({ queryKey: whiteboardsKeys.lists() })
            qc.invalidateQueries({ queryKey: whiteboardsKeys.detail(id) })
        },
        onError: (err, _vars, ctx) => {
            if (ctx?.prev) qc.setQueryData(whiteboardsKeys.detail(ctx.id), ctx.prev)
            toast.error(err?.response?.data?.detail || "Failed to update favorite.")
        },
    })
}

export function useToggleArchive() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ id, currentlyArchived }) =>
            whiteboardsApi.toggleArchiveWhiteboard(id, !currentlyArchived),
        onSuccess: (_data, { id }) => {
            qc.invalidateQueries({ queryKey: whiteboardsKeys.lists() })
            qc.invalidateQueries({ queryKey: whiteboardsKeys.detail(id) })
        },
        onError: (err) => {
            toast.error(err?.response?.data?.detail || "Failed to update archive status.")
        },
    })
}
