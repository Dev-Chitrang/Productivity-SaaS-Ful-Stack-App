import { Card, CardContent, CardHeader } from "@/components/ui/card"

export function MeetingCardSkeleton() {
  return (
    <Card size="sm">
      <CardHeader>
        <div className="h-4 w-3/5 animate-pulse rounded bg-muted" />
        <div className="h-3 w-2/5 animate-pulse rounded bg-muted" />
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="h-3 w-1/3 animate-pulse rounded bg-muted" />
          <div className="h-3 w-1/2 animate-pulse rounded bg-muted" />
        </div>
      </CardContent>
    </Card>
  )
}

export function MeetingListSkeleton({ count = 3 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <MeetingCardSkeleton key={i} />
      ))}
    </div>
  )
}

export function MeetingDetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="h-6 w-2/5 animate-pulse rounded bg-muted" />
        <div className="h-4 w-1/3 animate-pulse rounded bg-muted" />
      </div>
      <div className="space-y-3">
        <div className="h-4 w-full animate-pulse rounded bg-muted" />
        <div className="h-4 w-4/5 animate-pulse rounded bg-muted" />
        <div className="h-4 w-3/5 animate-pulse rounded bg-muted" />
      </div>
      <div className="flex gap-2">
        <div className="h-8 w-24 animate-pulse rounded bg-muted" />
        <div className="h-8 w-24 animate-pulse rounded bg-muted" />
      </div>
    </div>
  )
}
