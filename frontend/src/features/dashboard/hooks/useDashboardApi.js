import { useQuery } from "@tanstack/react-query"
import * as dashboardApi from "../api/dashboardApi"

export const dashboardKeys = {
    all: () => ["dashboard"],
    notesAnalytics: () => [...dashboardKeys.all(), "notes-analytics"],
    tasksAnalytics: () => [...dashboardKeys.all(), "tasks-analytics"],
    calendarAnalytics: () => [...dashboardKeys.all(), "calendar-analytics"],
}

export function useNotesAnalytics() {
    return useQuery({
        queryKey: dashboardKeys.notesAnalytics(),
        queryFn: async () => {
            const { data } = await dashboardApi.getNotesAnalytics()
            return data
        },
        staleTime: 30_000,
    })
}

export function useTasksAnalytics() {
    return useQuery({
        queryKey: dashboardKeys.tasksAnalytics(),
        queryFn: async () => {
            const { data } = await dashboardApi.getTasksAnalytics()
            return data
        },
        staleTime: 30_000,
    })
}

export function useCalendarAnalytics() {
    return useQuery({
        queryKey: dashboardKeys.calendarAnalytics(),
        queryFn: async () => {
            const { data } = await dashboardApi.getCalendarAnalytics()
            return data
        },
        staleTime: 30_000,
    })
}
