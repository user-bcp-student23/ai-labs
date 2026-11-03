from __future__ import annotations

import sqlite3
from pathlib import Path

_CREATE_TASKS_TABLE = (
    "CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, "
    "description TEXT NOT NULL, status TEXT NOT NULL, owner TEXT NOT NULL, priority TEXT NOT NULL, "
    "created_at TEXT NOT NULL)"
)
_SEED_TASKS = [
    ("Refactor login", "Separar responsabilidades en frontend", "TODO", "student", "HIGH"),
    ("Review API", "Revisar seguridad de endpoints", "IN_PROGRESS", "student", "MEDIUM"),
    ("Trainer notes", "Preparar retrospectiva", "TODO", "trainer", "LOW"),
]
_INSERT_SEED_TASK = (
    "INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES (?,?,?,?,?,datetime('now'))"
)


def open_database(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute(_CREATE_TASKS_TABLE)
    _seed_if_empty(connection)
    return connection


def _seed_if_empty(connection: sqlite3.Connection) -> None:
    count = connection.execute("SELECT COUNT(*) AS total FROM tasks").fetchone()["total"]
    if count:
        return
    connection.executemany(_INSERT_SEED_TASK, _SEED_TASKS)
    connection.commit()
