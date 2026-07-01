import { useState, useCallback, useEffect } from "react"

export function useModuleSidebarCollapse(storageKey, defaultExpandedWidth = 320) {
    const [collapsed, setCollapsed] = useState(() => {
        try {
            const stored = localStorage.getItem(storageKey)
            return stored === "true"
        } catch {
            return false
        }
    })

    useEffect(() => {
        try {
            localStorage.setItem(storageKey, String(collapsed))
        } catch {
            // localStorage unavailable
        }
    }, [collapsed, storageKey])

    const toggleSidebar = useCallback(() => {
        setCollapsed((prev) => !prev)
    }, [])

    const sidebarWidth = collapsed ? 52 : defaultExpandedWidth

    return { collapsed, toggleSidebar, sidebarWidth }
}
