import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useLinkedTasks, useSessionLinkedTasks, useCreateEntityLink, useDeleteEntityLink } from "@/features/entityLinks/hooks/useEntityLinksApi"
import { useTasks } from "@/features/tasks/hooks/useTasksApi"
import { ListChecks, Link, LinkSimpleBreak, Plus, MagnifyingGlass, ArrowUpRight } from "@phosphor-icons/react"
import toast from "react-hot-toast"

function PriorityBadge({ priority }) {
  const colors = {
    HIGH: "bg-red-100 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300 dark:border-red-800",
    MEDIUM: "bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-300 dark:border-yellow-800",
    LOW: "bg-green-100 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-300 dark:border-green-800",
  }
  const color = colors[priority] || colors.MEDIUM
  return (
    <span className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-medium ${color}`}>
      {priority}
    </span>
  )
}

function StatusBadge({ status }) {
  const colors = {
    TODO: "bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700",
    "IN PROGRESS": "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800",
    DONE: "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-300 dark:border-green-800",
  }
  const color = colors[status] || colors.TODO
  const label = status === "IN PROGRESS" ? "In Progress" : status?.charAt(0) + status?.slice(1).toLowerCase()
  return (
    <span className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-medium ${color}`}>
      {label}
    </span>
  )
}

export function LinkedTasksPanel({ meetingId, sessionId }) {
  const navigate = useNavigate()
  const isSession = !!sessionId
  const sessionResult = useSessionLinkedTasks(isSession ? meetingId : null, isSession ? sessionId : null)
  const meetingResult = useLinkedTasks(!isSession ? meetingId : null)
  const { data: linkedTasks = [], isLoading } = isSession ? sessionResult : meetingResult
  const createLink = useCreateEntityLink()
  const deleteLink = useDeleteEntityLink()

  const [linkDialogOpen, setLinkDialogOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedTaskId, setSelectedTaskId] = useState(null)

  const { data: tasksData } = useTasks({ search: searchQuery || undefined })

  const allTasks = tasksData?.tasks ?? []

  const linkedIds = new Set(linkedTasks.map((t) => t.id))
  const availableTasks = allTasks.filter((t) => !linkedIds.has(t.id) && !t.deleted_at && !t.is_archived)

  const handleLinkTask = async () => {
    if (!selectedTaskId) {
      toast.error("Select a task to link.")
      return
    }
    try {
      await createLink.mutateAsync({
        source_type: isSession ? "meeting_session" : "meeting",
        source_id: isSession ? sessionId : meetingId,
        target_type: "task",
        target_id: selectedTaskId,
      })
      setLinkDialogOpen(false)
      setSelectedTaskId(null)
      setSearchQuery("")
    } catch {
      // link created but UI updated via invalidation
    }
  }

  const handleRemoveLink = async (taskId) => {
    const link = linkedTasks.find((t) => t.id === taskId)
    if (!link) {
      toast.error("Link not found.")
      return
    }
    try {
      await deleteLink.mutateAsync(link.link_id)
    } catch {
      // link removed but UI updated via invalidation
    }
  }

  const handleOpenTask = (taskId) => {
    navigate(`/tasks?task=${taskId}`)
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ListChecks className="size-4 text-muted-foreground" weight="light" />
            <CardTitle className="text-sm">Linked Tasks</CardTitle>
            {linkedTasks.length > 0 && (
              <span className="text-[11px] text-muted-foreground">({linkedTasks.length})</span>
            )}
          </div>
          <Button variant="outline" size="sm" onClick={() => setLinkDialogOpen(true)}>
            <Link className="size-3.5" />
            Link Task
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            <div className="h-8 animate-pulse rounded bg-muted" />
            <div className="h-8 animate-pulse rounded bg-muted" />
          </div>
        ) : linkedTasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <ListChecks className="size-8 text-muted-foreground/40 mb-2" weight="light" />
            <p className="text-xs text-muted-foreground">No linked tasks</p>
            <Button variant="ghost" size="sm" className="mt-2" onClick={() => setLinkDialogOpen(true)}>
              <Plus className="size-3.5" />
              Link a task
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            {linkedTasks.map((task) => (
              <div
                key={task.id}
                role="button"
                tabIndex={0}
                onClick={() => handleOpenTask(task.id)}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); handleOpenTask(task.id) } }}
                className="flex items-center justify-between gap-2 rounded border border-border p-2.5 cursor-pointer hover:bg-muted/50 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="truncate text-xs font-medium text-foreground">
                      {task.title}
                    </span>
                    <ArrowUpRight className="size-3 shrink-0 text-muted-foreground" weight="bold" />
                  </div>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <PriorityBadge priority={task.priority} />
                    <StatusBadge status={task.status} />
                    {task.due_date && (
                      <span className="text-[10px] text-muted-foreground">
                        Due: {new Date(task.due_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); handleRemoveLink(task.id) }}
                  className="shrink-0 p-1 text-muted-foreground hover:text-destructive transition-colors"
                  title="Remove link"
                  aria-label={`Remove link to ${task.title}`}
                >
                  <LinkSimpleBreak className="size-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      <Dialog open={linkDialogOpen} onOpenChange={(v) => { if (!v) { setLinkDialogOpen(false); setSelectedTaskId(null); setSearchQuery("") } }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-sm">Link a Task</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="relative">
              <MagnifyingGlass className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search tasks..."
                className="pl-8 text-xs h-8"
              />
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1">
              {availableTasks.length === 0 ? (
                <p className="text-xs text-muted-foreground text-center py-4">
                  {searchQuery ? "No tasks match your search." : "No tasks available to link."}
                </p>
              ) : (
                availableTasks.map((task) => (
                  <button
                    key={task.id}
                    type="button"
                    onClick={() => setSelectedTaskId(task.id)}
                    className={`w-full text-left px-3 py-2 rounded text-xs border transition-colors ${
                      selectedTaskId === task.id
                        ? "border-primary bg-primary/5 text-foreground"
                        : "border-border text-muted-foreground hover:bg-muted hover:text-foreground"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate font-medium">{task.title}</span>
                      <PriorityBadge priority={task.priority} />
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" size="sm" onClick={() => { setLinkDialogOpen(false); setSelectedTaskId(null); setSearchQuery("") }}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleLinkTask} disabled={!selectedTaskId || createLink.isPending}>
              {createLink.isPending ? "Linking..." : "Link Task"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
