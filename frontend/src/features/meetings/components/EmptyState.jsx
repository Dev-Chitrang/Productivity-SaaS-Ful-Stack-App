import { Video, ClipboardText } from "@phosphor-icons/react"

export function EmptyState({ icon: Icon = Video, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="flex size-16 items-center justify-center rounded-full bg-muted mb-4">
        <Icon className="size-8 text-muted-foreground" weight="light" />
      </div>
      <h3 className="text-sm font-medium text-foreground mb-1">{title}</h3>
      {description && (
        <p className="text-xs text-muted-foreground max-w-xs mb-4">{description}</p>
      )}
      {action}
    </div>
  )
}

export function MeetingEmptyState({ onCreate }) {
  return (
    <EmptyState
      icon={Video}
      title="No meetings yet"
      description="Create your first meeting to get started."
      action={onCreate}
    />
  )
}
