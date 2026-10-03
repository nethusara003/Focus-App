from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def list(cls):
        return [p.value for p in cls]

PRIORITY_ORDER: Dict[str, int] = {
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3
}

class Task:
    def __init__(
        self,
        id: int,
        title: str,
        priority: str = Priority.MEDIUM,
        completed: bool = False,
        created_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        due_date: Optional[str] = None
    ):
        self.id = id
        self.title = title.strip()
        if not self.title:
            raise ValueError("Task title cannot be empty.")
        
        priority_lower = priority.lower()
        if priority_lower not in Priority.list():
            raise ValueError(f"Invalid priority '{priority}'. Must be one of: {', '.join(Priority.list())}.")
        
        self.priority = priority_lower
        self.completed = completed
        
        now_str = datetime.now().isoformat(timespec="seconds")
        self.created_at = created_at if created_at else now_str
        
        if self.completed:
            self.completed_at = completed_at if completed_at else now_str
        else:
            self.completed_at = None

        if due_date:
            due_date_clean = due_date.strip()
            try:
                datetime.strptime(due_date_clean, "%Y-%m-%d")
                self.due_date = due_date_clean
            except ValueError:
                raise ValueError(f"Invalid due date format '{due_date}'. Must be YYYY-MM-DD.")
        else:
            self.due_date = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "completed": self.completed,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "due_date": self.due_date
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            id=data["id"],
            title=data["title"],
            priority=data.get("priority", Priority.MEDIUM),
            completed=data.get("completed", False),
            created_at=data.get("created_at"),
            completed_at=data.get("completed_at"),
            due_date=data.get("due_date")
        )
