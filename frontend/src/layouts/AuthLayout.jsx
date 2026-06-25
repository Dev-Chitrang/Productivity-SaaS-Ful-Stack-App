import { Outlet } from "react-router-dom"

import { Card, CardContent } from "@/components/ui/card"

function AuthLayout() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <CardContent className="pt-6">
          <Outlet />
        </CardContent>
      </Card>
    </div>
  )
}

export default AuthLayout
