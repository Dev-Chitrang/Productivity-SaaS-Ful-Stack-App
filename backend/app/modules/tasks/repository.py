from datetime import datetime, timezone
from typing import Optional, Sequence, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update, asc, desc, func
from app.models.tasks import Task, TaskHistory
from app.modules.tasks.enums import TaskStatus, TaskPriority

class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: UUID, task_data: dict) -> Task:
        try:
            task = Task(user_id=user_id, **task_data)
            self.db.add(task)
            await self.db.flush()
            return task
        except Exception:
            await self.db.rollback()
            raise

    async def get_by_id(self, task_id: UUID, include_deleted: bool = False) -> Optional[Task]:
        conditions = [Task.id == task_id]
        if not include_deleted:
            conditions.append(Task.deleted_at.is_(None))

        stmt = select(Task).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, task: Task, update_data: dict) -> Task:
        try:
            for key, value in update_data.items():
                setattr(task, key, value)
            self.db.add(task)
            await self.db.flush()
            return task
        except Exception:
            await self.db.rollback()
            raise

    async def soft_delete(self, task: Task) -> None:
        try:
            task.deleted_at = datetime.now(timezone.utc)
            self.db.add(task)
            await self.db.flush()
        except Exception:
            await self.db.rollback()
            raise

    async def restore(self, task: Task) -> Task:
        try:
            task.deleted_at = None
            self.db.add(task)
            await self.db.flush()
            return task
        except Exception:
            await self.db.rollback()
            raise

    async def list_and_filter(
        self,
        user_id: UUID,
        search: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        label: Optional[str] = None,
        favorite: Optional[bool] = None,
        pinned: Optional[bool] = None,
        archived: Optional[bool] = False,
        deleted: bool = False,
        due_date: Optional[datetime] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ) -> Sequence[Task]:
        conditions = [Task.user_id == user_id]

        if deleted:
            conditions.append(Task.deleted_at.is_not(None))
        else:
            conditions.append(Task.deleted_at.is_(None))

        if archived is not None:
            conditions.append(Task.is_archived == archived)
        if favorite is not None:
            conditions.append(Task.is_favorite == favorite)
        if pinned is not None:
            conditions.append(Task.is_pinned == pinned)
        if status:
            conditions.append(Task.status == status)
        if priority:
            conditions.append(Task.priority == priority)
        if due_date:
            conditions.append(func.date(Task.due_date) == due_date.date())
        if label:
            conditions.append(Task.labels.contains([label.strip().lower()]))

        if search:
            search_pattern = f"%{search.strip().lower()}%"
            # Cast description path parameters to text cleanly within the JSONB search hierarchy
            conditions.append(
                or_(
                    func.lower(Task.title).ilike(search_pattern),
                    Task.description.cast(String).ilike(search_pattern),
                    Task.labels.contains([search.strip().lower()])
                )
            )

        stmt = select(Task).where(and_(*conditions))

        # Build clean dynamic order indices across target mapping enums
        # Map priority sorting strings directly to database-level order weights
        if sort_by == "priority":
            priority_order = func.case(
                (Task.priority == TaskPriority.HIGH, 1),
                (Task.priority == TaskPriority.MEDIUM, 2),
                (Task.priority == TaskPriority.LOW, 3)
            )
            stmt = stmt.order_by(asc(priority_order) if sort_order.lower() == "asc" else desc(priority_order))
        else:
            sort_column = getattr(Task, sort_by, Task.updated_at)
            stmt = stmt.order_by(asc(sort_column) if sort_order.lower() == "asc" else desc(sort_column))

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_history_bulk(self, history_records: List[dict]) -> None:
        try:
            if not history_records:
                return
            for record_data in history_records:
                record = TaskHistory(**record_data)
                self.db.add(record)
            await self.db.flush()
        except Exception:
            await self.db.rollback()
            raise

    async def get_history_by_task_id(self, task_id: UUID) -> Sequence[dict]:
        from app.models.user import User
        stmt = (
            select(TaskHistory, User.full_name)
            .join(User, TaskHistory.user_id == User.id)
            .where(TaskHistory.task_id == task_id)
            .order_by(desc(TaskHistory.created_at))
        )
        result = await self.db.execute(stmt)
        return [
            {
                "id": record.id,
                "action": record.action,
                "field_name": record.field_name,
                "old_value": record.old_value,
                "new_value": record.new_value,
                "created_at": record.created_at,
                "user": {"id": record.user_id, "name": name},
            }
            for record, name in result.all()
        ]
