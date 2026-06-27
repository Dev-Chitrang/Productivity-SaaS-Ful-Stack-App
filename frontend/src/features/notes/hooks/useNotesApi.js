import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import toast from "react-hot-toast"
import * as notesApi from "../api/notesApi"
import { LIST_STALE_TIME, NOTE_STALE_TIME } from "../constants"

export const notesKeys = {
    all: () => ["notes"],
    lists: () => [...notesKeys.all(), "list"],
    list: (filters) => [...notesKeys.lists(), filters],
    details: () => [...notesKeys.all(), "detail"],
    detail: (id) => [...notesKeys.details(), id],
}

export function useNotes(filters = {}) {
    return useQuery({
        queryKey: notesKeys.list(filters),
        queryFn: async () => {
            const { data } = await notesApi.listNotes(filters)
            return data
        },
        staleTime: LIST_STALE_TIME,
    })
}

export function useNote(id) {
    return useQuery({
        queryKey: notesKeys.detail(id),
        queryFn: async () => {
            const { data } = await notesApi.getNote(id)
            return data
        },
        enabled: !!id,
        staleTime: NOTE_STALE_TIME,
    })
}

export function useCreateNote(onSuccessCb) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload) => notesApi.createNote(payload),
        onSuccess: ({ data }) => {
            qc.invalidateQueries({ queryKey: notesKeys.lists() })
            toast.success("Note created.")
            onSuccessCb?.(data)
        },
        onError: (err) => {
            const detail = err?.response?.data?.detail
            const msg = Array.isArray(detail)
                ? detail.map((d) => d.msg ?? d).join("; ")
                : detail || "Failed to create note."
            toast.error(msg)
        },
    })
}

export function useUpdateNote() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ id, payload }) => notesApi.updateNote(id, payload),
        onMutate: async ({ id, payload }) => {
            await qc.cancelQueries({ queryKey: notesKeys.detail(id) })
            const prev = qc.getQueryData(notesKeys.detail(id))
            qc.setQueryData(notesKeys.detail(id), (old) => (old ? { ...old, ...payload } : old))
            return { prev, id }
        },
        onSuccess: (_data, { id }) => {
            qc.invalidateQueries({ queryKey: notesKeys.lists() })
            qc.invalidateQueries({ queryKey: notesKeys.detail(id) })
        },
        onError: (err, _vars, ctx) => {
            if (ctx?.prev) qc.setQueryData(notesKeys.detail(ctx.id), ctx.prev)
            const detail = err?.response?.data?.detail
            const msg = Array.isArray(detail)
                ? detail.map((d) => d.msg ?? d).join("; ")
                : detail || "Failed to update note."
            toast.error(msg)
        },
    })
}

export function useDeleteNote(onSuccessCb) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (id) => notesApi.deleteNote(id),
        onSuccess: (_data, id) => {
            qc.invalidateQueries({ queryKey: notesKeys.all() })
            toast.success("Note moved to trash.")
            onSuccessCb?.(id)
        },
        onError: (err) => {
            toast.error(err?.response?.data?.detail || "Failed to delete note.")
        },
    })
}

export function useRestoreNote(onSuccessCb) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (id) => notesApi.restoreNote(id),
        onSuccess: (_data, id) => {
            qc.invalidateQueries({ queryKey: notesKeys.all() })
            toast.success("Note restored.")
            onSuccessCb?.(id)
        },
        onError: (err) => {
            toast.error(err?.response?.data?.detail || "Failed to restore note.")
        },
    })
}

export function useToggleArchive() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ id, currentlyArchived }) =>
            currentlyArchived ? notesApi.unarchiveNote(id) : notesApi.archiveNote(id),
        onSuccess: (_data, { id }) => {
            qc.invalidateQueries({ queryKey: notesKeys.lists() })
            qc.invalidateQueries({ queryKey: notesKeys.detail(id) })
        },
        onError: (err) => {
            toast.error(err?.response?.data?.detail || "Failed to update archive status.")
        },
    })
}

export function useTogglePin() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ id, currentlyPinned }) =>
            currentlyPinned ? notesApi.unpinNote(id) : notesApi.pinNote(id),
        onMutate: async ({ id, currentlyPinned }) => {
            await qc.cancelQueries({ queryKey: notesKeys.detail(id) })
            const prev = qc.getQueryData(notesKeys.detail(id))
            qc.setQueryData(notesKeys.detail(id), (old) =>
                old ? { ...old, is_pinned: !currentlyPinned } : old,
            )
            return { prev, id }
        },
        onSuccess: (_data, { id }) => {
            qc.invalidateQueries({ queryKey: notesKeys.lists() })
            qc.invalidateQueries({ queryKey: notesKeys.detail(id) })
        },
        onError: (err, _vars, ctx) => {
            if (ctx?.prev) qc.setQueryData(notesKeys.detail(ctx.id), ctx.prev)
        },
    })
}

export function useToggleFavorite() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ id, currentlyFavorited }) =>
            currentlyFavorited ? notesApi.unfavoriteNote(id) : notesApi.favoriteNote(id),
        onMutate: async ({ id, currentlyFavorited }) => {
            await qc.cancelQueries({ queryKey: notesKeys.detail(id) })
            const prev = qc.getQueryData(notesKeys.detail(id))
            qc.setQueryData(notesKeys.detail(id), (old) =>
                old ? { ...old, is_favorite: !currentlyFavorited } : old,
            )
            return { prev, id }
        },
        onSuccess: (_data, { id }) => {
            qc.invalidateQueries({ queryKey: notesKeys.lists() })
            qc.invalidateQueries({ queryKey: notesKeys.detail(id) })
        },
        onError: (err, _vars, ctx) => {
            if (ctx?.prev) qc.setQueryData(notesKeys.detail(ctx.id), ctx.prev)
        },
    })
}
