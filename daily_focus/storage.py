import json
import os
import sys
import tempfile
from datetime import datetime
from typing import List, Tuple
from .models import Task

def get_default_db_path(env_var: str = "FOCUS_DB") -> Tuple[str, bool]:
    """
    Returns (resolved_db_path, printed_warning_flag)
    Resolves the database path according to the rules:
    1. Check environmental variable.
    2. Check if local tasks.json exists.
    3. Default to ~/.config/focus/tasks.json
    """
    env_path = os.getenv(env_var)
    if env_path:
        return os.path.abspath(env_path), False

    # Check local tasks.json
    local_path = "tasks.json"
    default_dir = os.path.expanduser("~/.config/focus")
    default_path = os.path.join(default_dir, "tasks.json")

    # If default database does not exist but ./tasks.json does, continue using the local file.
    if not os.path.exists(default_path) and os.path.exists(local_path):
        return os.path.abspath(local_path), True

    return os.path.abspath(default_path), False

class Storage:
    def __init__(self, filepath: str):
        self.filepath = os.path.abspath(filepath)

    def _handle_corruption(self) -> None:
        """
        Renames corrupt tasks.json to tasks.json.bak (or timestamped backup if that exists).
        """
        if not os.path.exists(self.filepath):
            return

        base, ext = os.path.splitext(self.filepath)
        bak_path = self.filepath + ".bak"
        
        if os.path.exists(bak_path):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            bak_path = f"{self.filepath}.{timestamp}.bak"

        try:
            os.rename(self.filepath, bak_path)
            print(
                f"Warning: The data file was corrupt. It has been backed up to '{bak_path}' and a new task list has been started.",
                file=sys.stderr
            )
        except Exception as e:
            print(
                f"Error: Failed to backup corrupt data file to '{bak_path}': {e}",
                file=sys.stderr
            )

    def load_tasks(self) -> List[Task]:
        if not os.path.exists(self.filepath):
            return []

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            self._handle_corruption()
            return []

        if not isinstance(data, list):
            self._handle_corruption()
            return []

        valid_tasks: List[Task] = []
        skipped_count = 0

        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                skipped_count += 1
                continue
            try:
                # Task instantiation will validate and throw errors
                task = Task.from_dict(item)
                valid_tasks.append(task)
            except Exception:
                skipped_count += 1

        if skipped_count > 0:
            print(
                f"Warning: Skipped {skipped_count} malformed task entry/entries from the data file.",
                file=sys.stderr
            )

        return valid_tasks

    def save_tasks(self, tasks: List[Task]) -> None:
        # Ensure parent directories exist
        dir_name = os.path.dirname(self.filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        data = [task.to_dict() for task in tasks]

        # Save atomically
        # Create temp file in the same directory as the target filepath
        temp_fd, temp_path = tempfile.mkstemp(dir=dir_name if dir_name else ".", prefix="tasks_temp_")
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            # Atomic replacement
            os.replace(temp_path, self.filepath)
        except Exception as e:
            # Clean up the temp file if saving failed
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise IOError(f"Failed to save tasks atomically: {e}")