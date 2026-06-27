import { createContext, useContext, useState, useEffect, useCallback } from "react"

const THEME_KEY = "app-theme"

function getInitialTheme() {
    const stored = localStorage.getItem(THEME_KEY)
    if (stored === "dark" || stored === "light") return stored
    if (window.matchMedia("(prefers-color-scheme: dark)").matches) return "dark"
    return "light"
}

const ThemeContext = createContext(null)

export function ThemeProvider({ children }) {
    const [theme, setThemeState] = useState(getInitialTheme)

    const setTheme = useCallback((t) => {
        setThemeState(t)
        localStorage.setItem(THEME_KEY, t)
        if (t === "dark") {
            document.documentElement.classList.add("dark")
        } else {
            document.documentElement.classList.remove("dark")
        }
    }, [])

    const toggleTheme = useCallback(() => {
        setTheme(theme === "dark" ? "light" : "dark")
    }, [theme, setTheme])

    useEffect(() => {
        setTheme(theme)
    }, []) // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        const mq = window.matchMedia("(prefers-color-scheme: dark)")
        const handler = (e) => {
            if (!localStorage.getItem(THEME_KEY)) {
                setTheme(e.matches ? "dark" : "light")
            }
        }
        mq.addEventListener("change", handler)
        return () => mq.removeEventListener("change", handler)
    }, [setTheme])

    return (
        <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
            {children}
        </ThemeContext.Provider>
    )
}

export function useThemeContext() {
    const ctx = useContext(ThemeContext)
    if (!ctx) throw new Error("useThemeContext must be used within ThemeProvider")
    return ctx
}
