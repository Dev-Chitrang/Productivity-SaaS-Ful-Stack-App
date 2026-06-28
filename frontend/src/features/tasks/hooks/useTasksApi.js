import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import toast from "react-hot-toast"
import * as tasksApi from "../api/tasksApi"
import { LIST_STALE_TIME, TASK_STALE_TIME } from "../constants"

export const tasksKeys = {
    all: () => ["tasks"],
    lists: () => [...tasksKeys.all(), "list"],
    list: (filters) => [...tasksKeys.lists(), filters],
    details: () => [...tasksKeys.all(), "detail"],
    detail: (id) => [...tasksKeys.details(), id],
    history: (id) => [...tasksKeys.all(), "history", id],
}

export function useTasks(filters = {}) {
    return useQuery({
        queryKey: tasksKeys.list(filters),
        queryFn: async () => {
            const { data } = await tasksApi.listTasks(filters)
            return data
        },
        staleTime: LIST_STALE_TIME,
    })
}

export function useTask(id) {
    return useQuery({
        queryKey: tasksKeys.detail(id),
        queryFn: async () => {
            const { data } = await tasksApi.getTask(id)
            return data
        },
        enabled: !!id,
        staleTime: TASK_STALE_TIME,
    })
}

export function useTaskHistory(id) {
    return useQuery({
        queryKey: tasksKeys.history(id),
        queryFn: async () => {
            const { data } = await tasksApi.getTaskHistory(id)
            return data
        },
        enabled: !!id,
        staleTime: TASK_STALE_TIME,
    })
}

export function useCreateTask(onSuccessCb) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload) => tasksApi.createTask(payload),
        onSuccess: ({ data }) => {
            qc.invalidateQueries({ queryKey: tasksKeys.lists() })
            qc.invalidateQueries({ queryKey: tasksKeys.history(data.id) })
            toast.success("Task created.")
            onSuccessCb?.(data)
        },
        onError: (err) => {
            const detail = err?.response?.data?.detail
            const msg = Array.isArray(detail)
                ? detail.map((d) => d.msg ?? d).join("; ")
                : detail || "Failed to create task."
            toast.error(msg)
        },
    })
}

export function useUpdateTask() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ id, payload }) => tasksApi.updateTask(id, payload),
        onMutate: async ({ id, payload }) => {
            await qc.cancelQueries({ queryKey: tasksKeys.detail(id) })
            const prev = qc.getQueryData(tasksKeys.detail(id))
            qc.setQueryData(tasksKeys.detail(id), (old) => (old ? { ...old, ...payload } : old))
            return { prev, id }
        },
        onSuccess: (_data, { id }) => {
            qc.invalidateQueries({ queryKey: tasksKeys.lists() })
            qc.invalidateQueries({ queryKey: tasksKeys.detail(id) })
            qc.invalidateQueries({ queryKey: tasksKeys.history(id) })
        },
        onError: (err, _vars, ctx) => {
            if (ctx?.prev) qc.setQueryData(tasksKeys.detail(ctx.id), ctx.prev)
            const detail = err?.response?.data?.detail
            const msg = Array.isArray(detail)
                ? detail.map((d) => d.msg ?? d).join("; ")
                : detail || "Failed to update task."
            toast.error(msg)
        },
    })
}

export function useDeleteTask(onSuccessCb) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (id) => tasksApi.deleteTask(id),
        onSuccess: (_data, id) => {
            qc.invalidateQueries({ queryKey: tasksKeys.all() })
            toast.success("Task moved to trash.")
            onSuccessCb?.(id)
        },
        onError: (err) => {
            toast.error(err?.response?.data?.detail || "Failed to delete task.")
        },
    })
}

export function useRestoreTask(onSuccessCb) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (id) => tasksApi.restoreTask(id),
        onSuccess: (_data, id) => {
            qc.invalidateQueries({ queryKey: tasksKeys.all() })
            toast.success("Task restored.")
            onSuccessCb?.(id)
        },
        onError: (err) => {
            toast.error(err?.response?.data?.detail || "Failed to restore task.")
        },
    })
}

export function useToggleArchive() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ id, currentlyArchived }) =>
            currentlyArchived ? tasksApi.unarchiveTask(id) : tasksApi.archiveTask(id),
        onSuccess: (_data, { id }) => {
            qc.invalidateQueries({ queryKey: tasksKeys.lists() })
            qc.invalidateQueries({ queryKey: tasksKeys.detail(id) })
            qc.invalidateQueries({ queryKey: tasksKeys.history(id) })
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
            currentlyPinned ? tasksApi.unpinTask(id) : tasksApi.pinTask(id),
        onMutate: async ({ id, currentlyPinned }) => {
            await qc.cancelQueries({ queryKey: tasksKeys.detail(id) })
            const prev = qc.getQueryData(tasksKeys.detail(id))
            qc.setQueryData(tasksKeys.detail(id), (old) =>
                old ? { ...old, is_pinned: !currentlyPinned } : old,
            )
            return { prev, id }
        },
        onSuccess: (_data, { id }) => {
            qc.invalidateQueries({ queryKey: tasksKeys.lists() })
            qc.invalidateQueries({ queryKey: tasksKeys.detail(id) })
            qc.invalidateQueries({ queryKey: tasksKeys.history(id) })
        },
        onError: (err, _vars, ctx) => {
            if (ctx?.prev) qc.setQueryData(tasksKeys.detail(ctx.id), ctx.prev)
        },
    })
}

export function useToggleFavorite() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ id, currentlyFavorited }) =>
            currentlyFavorited ? tasksApi.unfavoriteTask(id) : tasksApi.favoriteTask(id),
        onMutate: async ({ id, currentlyFavorited }) => {
            await qc.cancelQueries({ queryKey: tasksKeys.detail(id) })
            const prev = qc.getQueryData(tasksKeys.detail(id))
            qc.setQueryData(tasksKeys.detail(id), (old) =>
                old ? { ...old, is_favorite: !currentlyFavorited } : old,
            )
            return { prev, id }
        },
        onSuccess: (_data, { id }) => {
            qc.invalidateQueries({ queryKey: tasksKeys.lists() })
            qc.invalidateQueries({ queryKey: tasksKeys.detail(id) })
            qc.invalidateQueries({ queryKey: tasksKeys.history(id) })
        },
        onError: (err, _vars, ctx) => {
            if (ctx?.prev) qc.setQueryData(tasksKeys.detail(ctx.id), ctx.prev)
        },
    })
}
