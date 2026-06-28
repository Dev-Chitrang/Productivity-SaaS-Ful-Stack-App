import { TaskCard } from "./TaskCard"
import { TaskListSkeleton } from "./LoadingSkeleton"
import { EmptyState } from "./EmptyState"

export function TaskList({
    tasks,
    isLoading,
    selectedTaskId,
    onSelectTask,
    onTogglePin,
    onToggleFavorite,
    onArchive,
    onDelete,
    onRestore,
    onCreateTask,
    emptyType = "no-tasks",
}) {
    if (isLoading) return <TaskListSkeleton />

    if (!tasks || tasks.length === 0) {
        return <EmptyState type={emptyType} onCreateTask={onCreateTask} />
    }

    return (
        <div className="flex flex-col">
            {tasks.map((task) => (
                <TaskCard
                    key={task.id}
                    task={task}
                    isSelected={selectedTaskId === task.id}
                    onSelect={onSelectTask}
                    onTogglePin={onTogglePin}
                    onToggleFavorite={onToggleFavorite}
                    onArchive={onArchive}
                    onDelete={onDelete}
                    onRestore={onRestore}
                />
            ))}
        </div>
    )
}
