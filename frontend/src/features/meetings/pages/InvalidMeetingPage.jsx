import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { XCircle } from "@phosphor-icons/react"

export function InvalidMeetingPage({ message }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
          <div className="flex size-14 items-center justify-center rounded-full bg-red-50 dark:bg-red-950">
            <XCircle className="size-7 text-red-500" weight="fill" />
          </div>
          <h1 className="text-xl font-semibold text-foreground">
            Invalid or Expired Meeting
          </h1>
          <p className="text-sm text-muted-foreground">
            {message || "This meeting link is invalid or the meeting has expired."}
          </p>
          <Button asChild variant="outline" className="mt-2">
            <Link to="/">Go to Home</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
