/**
 * useCalendarApi.js
 *
 * React Query hooks for all Calendar API operations.
 * Imports API functions from api/calendarApi.js.
 * All serialization goes through api/calendarMapper.js — never inline here.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import toast from "react-hot-toast"
import * as calApi from "../api/calendarApi"

// ---------------------------------------------------------------------------
// Query key factory
// ---------------------------------------------------------------------------

export const calendarKeys = {
    all: () => ["calendar"],
    events: () => [...calendarKeys.all(), "events"],
    event: (id) => [...calendarKeys.events(), id],
    list: (start, end, filters) => [...calendarKeys.events(), "list", start, end, filters],
}

// ---------------------------------------------------------------------------
// List events — one hook for all calendar views
// ---------------------------------------------------------------------------

/**
 * @param {string} start   - ISO 8601 datetime with tz offset
 * @param {string} end     - ISO 8601 datetime with tz offset
 * @param {Object} [filters]
 * @param {string} [filters.search]
 * @param {string} [filters.event_type]  - uppercase enum value
 * @param {string} [filters.color]       - uppercase enum value
 */
export function useCalendarEvents(start, end, filters = {}) {
    const params = {
        start,
        end,
        ...(filters.search && { search: filters.search }),
        ...(filters.event_type && { event_type: filters.event_type }),
        ...(filters.color && { color: filters.color }),
    }

    return useQuery({
        queryKey: calendarKeys.list(start, end, filters),
        queryFn: async () => {
            const { data } = await calApi.listEvents(params)
            return Array.isArray(data) ? data : []
        },
        staleTime: 30_000,
        enabled: !!start && !!end,
    })
}

// ---------------------------------------------------------------------------
// Single event
// ---------------------------------------------------------------------------

export function useEvent(id) {
    return useQuery({
        queryKey: calendarKeys.event(id),
        queryFn: async () => {
            const { data } = await calApi.getEvent(id)
            return data
        },
        enabled: !!id,
        staleTime: 60_000,
    })
}

// ---------------------------------------------------------------------------
// Create event
// ---------------------------------------------------------------------------

export function useCreateEvent(onSuccessCb) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload) => calApi.createEvent(payload),
        onSuccess: ({ data }) => {
            qc.invalidateQueries({ queryKey: calendarKeys.all() })
            toast.success("Event created.")
            onSuccessCb?.(data)
        },
        onError: (err) => {
            const detail = err?.response?.data?.detail
            const msg = Array.isArray(detail)
                ? detail.map((d) => d.msg ?? d).join("; ")
                : detail || "Failed to create event."
            toast.error(msg)
        },
    })
}

// ---------------------------------------------------------------------------
// Update event (optimistic)
// ---------------------------------------------------------------------------

export function useUpdateEvent(onSuccessCb) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ id, payload }) => calApi.updateEvent(id, payload),
        onMutate: async ({ id, payload }) => {
            await qc.cancelQueries({ queryKey: calendarKeys.event(id) })
            const prev = qc.getQueryData(calendarKeys.event(id))
            qc.setQueryData(calendarKeys.event(id), (old) => (old ? { ...old, ...payload } : old))
            return { prev, id }
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: calendarKeys.all() })
            toast.success("Event updated.")
            onSuccessCb?.()
        },
        onError: (err, _vars, ctx) => {
            if (ctx?.prev) qc.setQueryData(calendarKeys.event(ctx.id), ctx.prev)
            const detail = err?.response?.data?.detail
            const msg = Array.isArray(detail)
                ? detail.map((d) => d.msg ?? d).join("; ")
                : detail || "Failed to update event."
            toast.error(msg)
        },
    })
}

// ---------------------------------------------------------------------------
// Delete event (optimistic)
// ---------------------------------------------------------------------------

export function useDeleteEvent(onSuccessCb) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (id) => calApi.deleteEvent(id),
        onMutate: async (id) => {
            await qc.cancelQueries({ queryKey: calendarKeys.all() })
            const prevCache = qc.getQueriesData({ queryKey: calendarKeys.all() })
            qc.setQueriesData({ queryKey: calendarKeys.all() }, (old) => {
                if (!old) return old
                if (Array.isArray(old)) return old.filter((e) => e.id !== id)
                return old
            })
            return { prevCache }
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: calendarKeys.all() })
            toast.success("Event deleted.")
            onSuccessCb?.()
        },
        onError: (err, _id, ctx) => {
            ctx?.prevCache?.forEach(([key, val]) => qc.setQueryData(key, val))
            toast.error(err?.response?.data?.detail || "Failed to delete event.")
        },
    })
}
