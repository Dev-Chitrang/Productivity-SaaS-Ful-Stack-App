import { createContext, useContext, useState, useCallback, useEffect } from "react"

const SidebarContext = createContext(null)

const STORAGE_KEY = "sidebar_collapsed"

export function SidebarProvider({ children }) {
    const [collapsed, setCollapsed] = useState(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY)
            return stored === "true"
        } catch {
            return false
        }
    })

    useEffect(() => {
        try {
            localStorage.setItem(STORAGE_KEY, String(collapsed))
        } catch {
            // localStorage unavailable
        }
    }, [collapsed])

    const toggleSidebar = useCallback(() => {
        setCollapsed((prev) => !prev)
    }, [])

    return (
        <SidebarContext.Provider value={{ collapsed, toggleSidebar }}>
            {children}
        </SidebarContext.Provider>
    )
}

export function useSidebar() {
    const ctx = useContext(SidebarContext)
    if (!ctx) throw new Error("useSidebar must be used within SidebarProvider")
    return ctx
}
