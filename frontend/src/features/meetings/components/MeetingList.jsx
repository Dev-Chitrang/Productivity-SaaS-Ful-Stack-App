import { MeetingCard } from "./MeetingCard"
import { MeetingListSkeleton } from "./LoadingSkeleton"
import { MeetingEmptyState } from "./EmptyState"

export function MeetingList({ meetings, isLoading }) {
  if (isLoading) {
    return <MeetingListSkeleton count={4} />
  }

  if (!meetings || meetings.length === 0) {
    return <MeetingEmptyState />
  }

  return (
    <div className="space-y-3" role="list" aria-label="Meetings list">
      {meetings.map((meeting) => (
        <div key={meeting.id} role="listitem">
          <MeetingCard meeting={meeting} />
        </div>
      ))}
    </div>
  )
}
