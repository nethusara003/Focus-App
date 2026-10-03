# Daily Focus

A modular, clean, and highly robust command-line "Daily Focus" task management application built in Python using only the standard library.

## Project Architecture

- `daily_focus/` - Core package
  - `models.py`: Task definitions, priorities, date validation, and timestamps.
  - `storage.py`: Atomic database operations, error-resilient load/save, auto-backup of corrupt data files, and directory setup.
  - `app.py`: Logic layer containing sorting algorithms, filters, task editing, statistics, and reopen mechanics.
  - `focus.py`: Parse-level and terminal CLI interaction (Argparse).
  - `timer.py`: Pomodoro-style focus countdown logic (pure, testable functions).
  - `__main__.py`: Allows running the package as `python3 -m daily_focus`.
- `focus.py`: Top-level wrapper script (re-exports `daily_focus`).
- `tests.py`: Broad-coverage automated unit test suite.

## Requirements

- Python 3.8+
- No third-party dependencies required.

## Installation

Install it as a proper command-line tool (editable mode, so code changes take effect immediately):

```bash
git clone https://github.com/nethusara003/Focus-App.git
cd Focus-App
pip install -e .
```

This creates a global `focus` command you can run from any directory:

```bash
focus add "Write report" -p high
focus list
focus timer 25
```

Your tasks live in `~/.config/focus/tasks.json` by default, so they follow you regardless of where you run the command.

## Execution Workflows

You can run Daily Focus either through the top-level script or as a module:

```bash
# Workflow 1: Via the executable script
python3 focus.py [command]

# Workflow 2: Via python module execution
python3 -m daily_focus [command]

# Workflow 3: Via the installed `focus` command (after `pip install -e .`)
focus [command]
```

## Storage & Resiliency Behavior

- **Fallback Migration**: If the default configuration database (`~/.config/focus/tasks.json`) does not exist but a local `tasks.json` in the current working directory is present, the app uses that file to preserve backward compatibility.
- **Data Safety**:
  - **Atomic Saves**: Saving is atomic. It writes to a temporary file in the same folder first, and then uses `os.replace` to atomically write over the database.
  - **Corrupted Data Backups**: If a file is corrupt (invalid JSON), the app avoids resetting or wiping it. It backs it up as `tasks.json.bak` (or `tasks.json.<timestamp>.bak` if a backup already exists) and prints a helpful warning.
  - **Skipping Malformed Rows**: If individual tasks within the database are corrupt, it gracefully skips them instead of crashing, warning the user about the number of corrupt entries.

## Database Location Customization

By default, data is saved in `~/.config/focus/tasks.json`. You can override this using:
- **Global Flag**: `python3 focus.py --db /path/to/tasks.json [command]`
- **Environment Variable**: `FOCUS_DB=/path/to/tasks.json python3 focus.py [command]`

---

## Command Reference & Usage Examples

### 1. Adding Tasks
Add tasks with optional due dates (`YYYY-MM-DD`) and priority (`high`, `medium`, `low`):
```bash
python3 focus.py add "Finish quarterly report"
python3 focus.py add "Prepare presentation" --priority high --due 2026-10-10
python3 focus.py add "Water plants" -p low --due 2026-10-15
```

### 2. Listing Tasks
List all tasks, sorted by incomplete tasks first, then priority (`high` > `medium` > `low`), then by ID.
```bash
python3 focus.py list
```

**Filter by priority:**
```bash
python3 focus.py list --priority high
```

**Filter by search term (case-insensitive):**
```bash
python3 focus.py list --search report
```

Filters can be used together!

### 3. Show Today's Focus
Shows the top 3 incomplete tasks. Overdue tasks are sorted prominently to the absolute top of this list and marked with `[OVERDUE]`:
```bash
python3 focus.py today
```

### 4. Edit a Task
Modify a task's title, priority, or both. Preserves task ID, creation timestamps, and completion state.
```bash
python3 focus.py edit 2 --title "New task title" --priority high
```

### 5. Mark Task Complete / Reopen
Mark task complete (sets `completed_at` to current time):
```bash
python3 focus.py complete 2
```

Reopen completed task (resets `completed_at` to null):
```bash
python3 focus.py reopen 2
```

### 6. Delete a Task
Prompts the user for confirmation before deletion to prevent accidents.
```bash
python3 focus.py delete 2
```

Skip confirmation in shell/automation scripts:
```bash
python3 focus.py delete 2 --yes
```

### 7. Task Statistics
Displays task counts and statistics, including total tasks, pending tasks, completed tasks, and tasks completed today:
```bash
python3 focus.py stats
```

### 8. Focus Timer
Start a pomodoro-style focus countdown with a live timer in your terminal. Press Ctrl+C to cancel at any time.
```bash
python3 focus.py timer              # 25-minute focus session (default)
python3 focus.py timer 50           # 50-minute focus session
python3 focus.py timer 25 --break 5 # 25 min focus, then a 5 min break
python3 focus.py timer 25 --task 2  # focus on task 2 (shows its title)
```

---

## Running the Tests

To run the full suite of 24 unit tests covering every single edge-case, sorting rule, and data safety mechanism:

```bash
python3 -m unittest tests.py
```