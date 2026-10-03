#!/usr/bin/env python3
import argparse
import sys
from datetime import datetime
from .storage import Storage, get_default_db_path
from .app import FocusApp
from .models import Priority
from .timer import run_timer

def format_task(task: "Task") -> str:
    status = "[x]" if task.completed else "[ ]"
    priority_str = f"({task.priority.upper()})"
    due_str = f" [Due: {task.due_date}]" if task.due_date else ""
    
    # Check if overdue
    today_str = datetime.now().strftime("%Y-%m-%d")
    overdue_label = "" 
    if not task.completed and task.due_date and task.due_date < today_str:
        overdue_label = " [OVERDUE]"

    return f"{task.id}: {status} {priority_str} {task.title}{due_str}{overdue_label}"

def main():
    parser = argparse.ArgumentParser(
        description="Daily Focus - A simple command-line task management app"
    )
    # Global option --db PATH
    parser.add_argument(
        "--db",
        type=str,
        help="Database path override"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", type=str, help="Title of the task")
    add_parser.add_argument(
        "-p", "--priority",
        type=str,
        default="medium",
        choices=Priority.list(),
        help="Priority level (high, medium, low)"
    )
    add_parser.add_argument(
        "--due",
        type=str,
        help="Optional due date in YYYY-MM-DD format"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--search", type=str, help="Filter tasks by search term (case-insensitive)")
    list_parser.add_argument("--priority", type=str, choices=Priority.list(), help="Filter tasks by priority")

    # Complete command
    complete_parser = subparsers.add_parser("complete", help="Mark a task as complete")
    complete_parser.add_argument("id", type=int, help="ID of the task to complete")

    # Reopen command
    reopen_parser = subparsers.add_parser("reopen", help="Reopen a completed task")
    reopen_parser.add_argument("id", type=int, help="ID of the task to reopen")

    # Edit command
    edit_parser = subparsers.add_parser("edit", help="Edit a task's title or priority")
    edit_parser.add_argument("id", type=int, help="ID of the task to edit")
    edit_parser.add_argument("--title", type=str, help="New title for the task")
    edit_parser.add_argument(
        "-p", "--priority",
        type=str,
        choices=Priority.list(),
        help="New priority level (high, medium, low)"
    )

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("id", type=int, help="ID of the task to delete")
    delete_parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip delete confirmation prompt"
    )

    # Today view command
    subparsers.add_parser("today", help="Show today's focus (top 3 incomplete/overdue tasks)")

    # Stats command
    subparsers.add_parser("stats", help="Show task statistics")

    # Timer command
    timer_parser = subparsers.add_parser("timer", help="Start a focus timer (pomodoro)")
    timer_parser.add_argument(
        "minutes",
        type=int,
        nargs="?",
        default=25,
        help="Focus duration in minutes (default: 25)"
    )
    timer_parser.add_argument(
        "--break",
        dest="break_minutes",
        type=int,
        default=0,
        help="Break duration in minutes after the focus session (default: 0)"
    )
    timer_parser.add_argument(
        "--task",
        type=int,
        default=None,
        help="Task ID to focus on (shows its title while timing)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Resolve DB path
    printed_warning = False
    if args.db:
        db_path = args.db
    else:
        db_path, printed_warning = get_default_db_path()

    if printed_warning:
        print("Note: Using existing local database 'tasks.json' as fallback.", file=sys.stderr)

    storage = Storage(db_path)
    app = FocusApp(storage)

    try:
        if args.command == "add":
            task = app.add_task(args.title, args.priority, args.due)
            print(f"Added task {task.id}: {task.title} [{task.priority}]" + (f" [Due: {task.due_date}]" if task.due_date else ""))
        
        elif args.command == "list":
            tasks = app.list_tasks(search=args.search, priority=args.priority)
            if not tasks:
                print("No tasks found.")
            else:
                print("Tasks:")
                for t in tasks:
                    print(f"  {format_task(t)}")
        
        elif args.command == "complete":
            # First check if it exists and status
            # We can load them first to give precise feedback if already completed
            # Let's see if the app already does that: app.complete_task(args.id)
            tasks_before = {t.id: t.completed for t in storage.load_tasks()}
            task = app.complete_task(args.id)
            if args.id in tasks_before and tasks_before[args.id]:
                print(f"Task {args.id} is already completed.")
            else:
                print(f"Marked task {task.id} as complete.")
        
        elif args.command == "reopen":
            task = app.reopen_task(args.id)
            print(f"Reopened task {task.id}.")

        elif args.command == "edit":
            task = app.edit_task(args.id, title=args.title, priority=args.priority)
            print(f"Updated task {task.id}: {task.title} [{task.priority}]")

        elif args.command == "delete":
            if not args.yes:
                confirm = input(f"Are you sure you want to delete task {args.id}? (y/N): ").strip().lower()
                if confirm not in ("y", "yes"):
                    print("Deletion cancelled.")
                    sys.exit(0)
            task = app.delete_task(args.id)
            print(f"Deleted task {task.id}: {task.title}")
        
        elif args.command == "today":
            tasks = app.get_today_view()
            if not tasks:
                print("No pending tasks for today. Great job!")
            else:
                print("Today's Focus (Top Incomplete Tasks):")
                for t in tasks:
                    print(f"  {format_task(t)}")

        elif args.command == "stats":
            stats = app.get_stats()
            print("Task Statistics:")
            print(f"  Total Tasks:       {stats['total']}")
            print(f"  Pending Tasks:     {stats['pending']}")
            print(f"  Completed Tasks:   {stats['completed']}")
            print(f"  Completed Today:   {stats['completed_today']}")

        elif args.command == "timer":
            if args.minutes <= 0:
                raise ValueError("Timer duration must be a positive number of minutes.")
            if args.break_minutes < 0:
                raise ValueError("Break duration cannot be negative.")

            task_title = None
            if args.task is not None:
                tasks_by_id = {t.id: t for t in storage.load_tasks()}
                if args.task not in tasks_by_id:
                    raise ValueError(f"Task with ID {args.task} not found.")
                task_title = tasks_by_id[args.task].title

            session_desc = f" on '{task_title}'" if task_title else ""
            print(f"Starting {args.minutes}-minute focus session{session_desc}. Press Ctrl+C to cancel.")
            completed = run_timer(args.minutes * 60, label="Focus")

            if not completed:
                print("\nTimer cancelled.")
                sys.exit(0)

            print("\a", end="", flush=True)
            print("\nFocus session complete! Well done.")

            if args.break_minutes > 0:
                print(f"Starting {args.break_minutes}-minute break. Press Ctrl+C to skip.")
                break_done = run_timer(args.break_minutes * 60, label="Break")
                print("\a", end="", flush=True)
                if break_done:
                    print("\nBreak over! Back to it.")
                else:
                    print("\nBreak skipped.")

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
