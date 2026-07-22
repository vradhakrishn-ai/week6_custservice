import os
import sqlite3
import json
from typing import List, Optional
from .models import HITLTask

DB_PATH = os.getenv("HITL_DB_PATH", os.path.join(os.getcwd(), "data", "hitl_workflow.db"))

class PersistentHITLStore:
    """Manages transactional state persistence for human validation tasks using an isolated SQLite engine."""
    
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hitl_tasks (
                    task_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    trigger_rule TEXT,
                    proposed_action TEXT,
                    context_data TEXT,
                    status TEXT,
                    reviewer_comments TEXT
                )
            """)
            conn.commit()

    def save_task(self, task: HITLTask):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO hitl_tasks VALUES (?, ?, ?, ?, ?, ?, ?)",
                (task.task_id, task.session_id, task.trigger_rule, task.proposed_action, 
                 json.dumps(task.context_data), task.status, task.reviewer_comments)
            )
            conn.commit()

    def get_pending(self) -> List[HITLTask]:
        tasks = []
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT * FROM hitl_tasks WHERE status = 'pending'")
            for row in cursor.fetchall():
                tasks.append(HITLTask(
                    task_id=row[0], session_id=row[1], trigger_rule=row[2],
                    proposed_action=row[3], context_data=json.loads(row[4]),
                    status=row[5], reviewer_comments=row[6]
                ))
        return tasks

    def update_task_status(self, task_id: str, status: str, comments: str) -> bool:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                "UPDATE hitl_tasks SET status = ?, reviewer_comments = ? WHERE task_id = ?",
                (status, comments, task_id)
            )
            conn.commit()
            return cursor.rowcount > 0