from __future__ import annotations

import sqlite3

from app.schemas import TaskCreate

_SELECT_TASKS = "SELECT id,title,description,status,owner,priority,created_at FROM tasks"
_INSERT_TASK = "INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES (?,?,?,?,?,datetime('now'))"


class TaskRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def list_by_owner(self, owner: str) -> list[sqlite3.Row]:
        return self._connection.execute(_SELECT_TASKS + " WHERE owner = ? ORDER BY id", (owner,)).fetchall()

    def status_and_priority_by_owner(self, owner: str) -> list[sqlite3.Row]:
        return self._connection.execute("SELECT status,priority FROM tasks WHERE owner = ?", (owner,)).fetchall()

    def insert(self, task: TaskCreate, owner: str) -> int:
        cursor = self._connection.execute(
            _INSERT_TASK,
            (task.title, task.description, task.status, owner, task.priority),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    def get_by_id(self, task_id: int) -> sqlite3.Row:
        return self._connection.execute(_SELECT_TASKS + " WHERE id = ?", (task_id,)).fetchone()
