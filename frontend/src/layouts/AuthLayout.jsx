import { Link, Outlet } from "react-router-dom"
import { ArrowLeft } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import { ThemeToggle } from "@/components/ThemeToggle"

function AuthLayout() {
  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background p-4">
      <div className="absolute top-0 left-0 right-0 flex items-center justify-between px-4 py-3">
        <Link
          to="/"
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Back to home"
        >
          <ArrowLeft className="size-3.5" />
          Home
        </Link>
        <ThemeToggle />
      </div>
      <Card className="w-full max-w-sm">
        <CardContent className="pt-6">
          <Outlet />
        </CardContent>
      </Card>
    </div>
  )
}

export default AuthLayout
