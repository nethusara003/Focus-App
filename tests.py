import unittest
import os
import tempfile
import json
from datetime import datetime, timedelta
from daily_focus.models import Task, Priority
from daily_focus.storage import Storage, get_default_db_path
from daily_focus.app import FocusApp

class TestFocusApp(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.test_dir.name, "tasks.json")
        self.storage = Storage(self.db_path)
        self.app = FocusApp(self.storage)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_add_task_valid(self):
        task = self.app.add_task("Write documentation", priority="high")
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Write documentation")
        self.assertEqual(task.priority, "high")
        self.assertFalse(task.completed)
        self.assertIsNotNone(task.created_at)
        self.assertIsNone(task.completed_at)

    def test_add_task_invalid_title(self):
        with self.assertRaises(ValueError):
            self.app.add_task("   ", priority="medium")

    def test_add_task_invalid_priority(self):
        with self.assertRaises(ValueError):
            self.app.add_task("Task", priority="urgent")

    def test_list_tasks_sorting(self):
        self.app.add_task("Low task", priority="low")
        self.app.add_task("High task", priority="high")
        t3 = self.app.add_task("Medium task", priority="medium")
        
        # Complete the medium priority task
        self.app.complete_task(t3.id)

        tasks = self.app.list_tasks()
        # Incomplete tasks first: 'High task' (high), then 'Low task' (low). Completed 'Medium task' last.
        self.assertEqual(tasks[0].title, "High task")
        self.assertEqual(tasks[1].title, "Low task")
        self.assertEqual(tasks[2].title, "Medium task")
        self.assertTrue(tasks[2].completed)

    def test_complete_task_valid(self):
        task = self.app.add_task("Test task")
        self.assertFalse(task.completed)
        completed_task = self.app.complete_task(task.id)
        self.assertTrue(completed_task.completed)
        self.assertIsNotNone(completed_task.completed_at)

    def test_complete_task_already_complete(self):
        task = self.app.add_task("Test task")
        self.app.complete_task(task.id)
        # Completing again should return the task without raising an error
        completed_task = self.app.complete_task(task.id)
        self.assertTrue(completed_task.completed)

    def test_complete_task_invalid_id(self):
        with self.assertRaises(ValueError):
            self.app.complete_task(999)

    def test_reopen_task_valid(self):
        task = self.app.add_task("Test task")
        self.app.complete_task(task.id)
        
        # Reopen
        reopened_task = self.app.reopen_task(task.id)
        self.assertFalse(reopened_task.completed)
        self.assertIsNone(reopened_task.completed_at)

    def test_reopen_task_already_incomplete(self):
        task = self.app.add_task("Test task")
        with self.assertRaises(ValueError):
            self.app.reopen_task(task.id)

    def test_reopen_task_invalid_id(self):
        with self.assertRaises(ValueError):
            self.app.reopen_task(999)

    def test_delete_task_valid(self):
        task = self.app.add_task("Delete me")
        deleted = self.app.delete_task(task.id)
        self.assertEqual(deleted.id, task.id)
        self.assertEqual(len(self.app.list_tasks()), 0)

    def test_delete_task_invalid_id(self):
        with self.assertRaises(ValueError):
            self.app.delete_task(999)

    def test_today_view(self):
        self.app.add_task("Low priority", priority="low")
        self.app.add_task("High priority 1", priority="high")
        self.app.add_task("Medium priority", priority="medium")
        self.app.add_task("High priority 2", priority="high")
        
        today_tasks = self.app.get_today_view()
        self.assertEqual(len(today_tasks), 3)
        # Should be sorted by priority: high first, then medium, then low
        self.assertEqual(today_tasks[0].title, "High priority 1")
        self.assertEqual(today_tasks[1].title, "High priority 2")
        self.assertEqual(today_tasks[2].title, "Medium priority")

    def test_today_view_overdue_sorting(self):
        # Add a task with due date in the past
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        self.app.add_task("Incomplete tomorrow task", priority="high", due_date=tomorrow)
        self.app.add_task("Overdue medium priority task", priority="medium", due_date=yesterday)
        self.app.add_task("Normal priority task", priority="high")
        
        today_tasks = self.app.get_today_view()
        # Overdue tasks should sort at the absolute top despite being medium priority
        self.assertEqual(today_tasks[0].title, "Overdue medium priority task")
        self.assertEqual(today_tasks[1].title, "Incomplete tomorrow task")
        self.assertEqual(today_tasks[2].title, "Normal priority task")

    def test_due_date_validation(self):
        # Valid due date
        task = self.app.add_task("Due soon", due_date="2026-12-31")
        self.assertEqual(task.due_date, "2026-12-31")

        # Invalid due date should raise ValueError
        with self.assertRaises(ValueError):
            self.app.add_task("Bad date", due_date="2026/12/31")
        with self.assertRaises(ValueError):
            self.app.add_task("Bad date 2", due_date="next-week")

    def test_edit_task_valid(self):
        task = self.app.add_task("Original title", priority="low")
        
        # Edit both
        edited = self.app.edit_task(task.id, title="New title", priority="high")
        self.assertEqual(edited.title, "New title")
        self.assertEqual(edited.priority, "high")
        
        # Edit only title
        edited = self.app.edit_task(task.id, title="Newer title")
        self.assertEqual(edited.title, "Newer title")
        self.assertEqual(edited.priority, "high")

        # Edit only priority
        edited = self.app.edit_task(task.id, priority="medium")
        self.assertEqual(edited.title, "Newer title")
        self.assertEqual(edited.priority, "medium")

    def test_edit_task_invalid(self):
        task = self.app.add_task("Task", priority="medium")
        
        # No edits provided
        with self.assertRaises(ValueError):
            self.app.edit_task(task.id)
        
        # Empty title
        with self.assertRaises(ValueError):
            self.app.edit_task(task.id, title="   ")
            
        # Invalid priority
        with self.assertRaises(ValueError):
            self.app.edit_task(task.id, priority="urgent")

    def test_stats(self):
        self.app.add_task("T1", priority="high")
        t2 = self.app.add_task("T2", priority="medium")
        t3 = self.app.add_task("T3", priority="low")
        
        self.app.complete_task(t2.id)
        self.app.complete_task(t3.id)
        
        stats = self.app.get_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["pending"], 1)
        self.assertEqual(stats["completed"], 2)
        self.assertEqual(stats["completed_today"], 2)

    def test_filters(self):
        self.app.add_task("Report quarterly", priority="high")
        self.app.add_task("Submit presentation", priority="high")
        self.app.add_task("Report monthly", priority="medium")
        self.app.add_task("Feed dog", priority="low")

        # Search only
        results = self.app.list_tasks(search="report")
        self.assertEqual(len(results), 2)
        titles = {r.title for r in results}
        self.assertIn("Report quarterly", titles)
        self.assertIn("Report monthly", titles)

        # Priority only
        results = self.app.list_tasks(priority="high")
        self.assertEqual(len(results), 2)
        titles = {r.title for r in results}
        self.assertIn("Report quarterly", titles)
        self.assertIn("Submit presentation", titles)

        # Search and priority combined
        results = self.app.list_tasks(search="report", priority="high")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Report quarterly")

    def test_data_safety_corruption_backup(self):
        # Create a corrupt JSON file
        with open(self.db_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")
        
        # Storage should handle the error, back up the file, and return an empty list
        tasks = self.storage.load_tasks()
        self.assertEqual(tasks, [])
        
        # Check that tasks.json.bak was created
        bak_path = self.db_path + ".bak"
        self.assertTrue(os.path.exists(bak_path))
        with open(bak_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read().strip(), "{ invalid json }")

    def test_data_safety_corruption_multiple_backups(self):
        # Create a corrupt JSON file and an existing backup
        bak_path = self.db_path + ".bak"
        with open(bak_path, "w", encoding="utf-8") as f:
            f.write("old backup")
            
        with open(self.db_path, "w", encoding="utf-8") as f:
            f.write("corrupt content")
            
        tasks = self.storage.load_tasks()
        self.assertEqual(tasks, [])
        
        # Should have created a timestamped backup instead of overwriting .bak
        files_in_dir = os.listdir(self.test_dir.name)
        backup_files = [f for f in files_in_dir if f.endswith(".bak") and f != "tasks.json.bak"]
        self.assertEqual(len(backup_files), 1)
        
        # Verify old backup still exists
        with open(bak_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "old backup")

    def test_data_safety_skipping_malformed_entries(self):
        # JSON list where one entry is completely invalid/malformed
        bad_entries = [
            {"id": 1, "title": "Valid Task", "priority": "high", "completed": False},
            {"id": 2, "title": "  ", "priority": "medium"}, # raises ValueError (empty title)
            {"id": 3, "title": "Valid Task 2", "priority": "invalid_priority"}, # raises ValueError
            "string entry instead of dict",
            {"id": 4, "title": "Valid Task 3", "priority": "low", "completed": True}
        ]
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(bad_entries, f)
            
        tasks = self.storage.load_tasks()
        # Entries 1 and 4 should be successfully loaded. Entries 2, 3 and the string should be skipped.
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].id, 1)
        self.assertEqual(tasks[1].id, 4)

    def test_data_safety_atomic_saving(self):
        self.app.add_task("Atomic Task")
        self.assertTrue(os.path.exists(self.db_path))
        
        # Ensure the tasks are saved correctly
        tasks = self.storage.load_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "Atomic Task")

    def test_backward_compatibility(self):
        # Save a file with traditional-style JSON lacking timestamps and due date
        old_data = [
            {"id": 1, "title": "Old Task", "priority": "medium", "completed": False}
        ]
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(old_data, f)
            
        tasks = self.storage.load_tasks()
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(task.title, "Old Task")
        self.assertIsNotNone(task.created_at) # filled with default/current datetime
        self.assertIsNone(task.completed_at)
        self.assertIsNone(task.due_date)

if __name__ == "__main__":
    unittest.main()
