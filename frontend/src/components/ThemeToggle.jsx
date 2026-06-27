import { Sun, Moon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useThemeContext } from "@/context/ThemeContext"

export function ThemeToggle() {
    const { theme, toggleTheme } = useThemeContext()

    return (
        <Button
            variant="ghost"
            size="icon-sm"
            onClick={toggleTheme}
            aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
        >
            {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
        </Button>
    )
}
