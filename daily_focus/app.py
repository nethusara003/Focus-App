from typing import List, Optional
from datetime import datetime
from .models import Task, Priority, PRIORITY_ORDER
from .storage import Storage

class FocusApp:
    def __init__(self, storage: Storage):
        self.storage = storage

    def _get_next_id(self, tasks: List[Task]) -> int:
        if not tasks:
            return 1
        return max(task.id for task in tasks) + 1

    def add_task(self, title: str, priority: str = "medium", due_date: Optional[str] = None) -> Task:
        tasks = self.storage.load_tasks()
        new_id = self._get_next_id(tasks)
        task = Task(id=new_id, title=title, priority=priority, completed=False, due_date=due_date)
        tasks.append(task)
        self.storage.save_tasks(tasks)
        return task

    def list_tasks(
        self,
        search: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Task]:
        tasks = self.storage.load_tasks()
        
        # Filter
        filtered = tasks
        if search:
            search_lower = search.lower()
            filtered = [t for t in filtered if search_lower in t.title.lower()]
        if priority:
            priority_lower = priority.lower()
            filtered = [t for t in filtered if t.priority == priority_lower]

        # Sort: incomplete tasks first (completed=False comes before True), then by priority order, then by ID
        return sorted(
            filtered,
            key=lambda t: (t.completed, PRIORITY_ORDER.get(t.priority, 2), t.id)
        )

    def complete_task(self, task_id: int) -> Task:
        tasks = self.storage.load_tasks()
        for task in tasks:
            if task.id == task_id:
                if task.completed:
                    # If already completed, do not change anything
                    return task
                task.completed = True
                task.completed_at = datetime.now().isoformat(timespec="seconds")
                self.storage.save_tasks(tasks)
                return task
        raise ValueError(f"Task with ID {task_id} not found.")

    def reopen_task(self, task_id: int) -> Task:
        tasks = self.storage.load_tasks()
        for task in tasks:
            if task.id == task_id:
                if not task.completed:
                    raise ValueError(f"Task {task_id} is already incomplete.")
                task.completed = False
                task.completed_at = None
                self.storage.save_tasks(tasks)
                return task
        raise ValueError(f"Task with ID {task_id} not found.")

    def edit_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        priority: Optional[str] = None
    ) -> Task:
        if title is None and priority is None:
            raise ValueError("At least one of --title or --priority must be provided for editing.")

        tasks = self.storage.load_tasks()
        for task in tasks:
            if task.id == task_id:
                if title is not None:
                    cleaned_title = title.strip()
                    if not cleaned_title:
                        raise ValueError("Task title cannot be empty.")
                    task.title = cleaned_title
                if priority is not None:
                    priority_lower = priority.lower()
                    if priority_lower not in Priority.list():
                        raise ValueError(f"Invalid priority '{priority}'. Must be one of: {', '.join(Priority.list())}.")
                    task.priority = priority_lower
                
                self.storage.save_tasks(tasks)
                return task
        raise ValueError(f"Task with ID {task_id} not found.")

    def delete_task(self, task_id: int) -> Task:
        tasks = self.storage.load_tasks()
        task_to_delete = None
        filtered_tasks = []
        for task in tasks:
            if task.id == task_id:
                task_to_delete = task
            else:
                filtered_tasks.append(task)
        
        if not task_to_delete:
            raise ValueError(f"Task with ID {task_id} not found.")
        
        self.storage.save_tasks(filtered_tasks)
        return task_to_delete

    def get_stats(self) -> dict:
        tasks = self.storage.load_tasks()
        total = len(tasks)
        pending = sum(1 for t in tasks if not t.completed)
        completed = total - pending

        # Completed today calculation
        today_str = datetime.now().strftime("%Y-%m-%d")
        completed_today = 0
        for t in tasks:
            if t.completed and t.completed_at:
                # completed_at starts with YYYY-MM-DD
                if t.completed_at.startswith(today_str):
                    completed_today += 1

        return {
            "total": total,
            "pending": pending,
            "completed": completed,
            "completed_today": completed_today
        }

    def get_today_view(self) -> List[Task]:
        tasks = self.storage.load_tasks()
        incomplete = [t for t in tasks if not t.completed]
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Overdue means: not completed, has due_date, and due_date < today_str
        def is_overdue(t: Task) -> bool:
            return bool(t.due_date and t.due_date < today_str)

        # Sort overdue tasks to the very top, then by priority, then by ID
        # is_overdue(t) is True (which is 1) or False (which is 0).
        # Since we want overdue tasks first, we want is_overdue(t) == True to sort before False.
        # So we can use: (not is_overdue(t), PRIORITY_ORDER.get(t.priority, 2), t.id)
        sorted_incomplete = sorted(
            incomplete,
            key=lambda t: (not is_overdue(t), PRIORITY_ORDER.get(t.priority, 2), t.id)
        )
        return sorted_incomplete[:3]