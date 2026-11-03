from __future__ import annotations

import sqlite3

from fastapi import HTTPException

from app.constants import CLOSED_STATUSES, HIGH_PRIORITY
from app.schemas import SummaryOut


def resolve_owner(requested_owner: str | None, username: str) -> str:
    if requested_owner and requested_owner != username:
        raise HTTPException(status_code=403, detail="Forbidden")
    return username


def summarize_tasks(owner: str, rows: list[sqlite3.Row]) -> SummaryOut:
    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
    high_priority_open = sum(1 for row in rows if _is_open_high_priority(row))
    return SummaryOut(owner=owner, total=len(rows), byStatus=by_status, highPriorityOpen=high_priority_open)


def _is_open_high_priority(row: sqlite3.Row) -> bool:
    return row["priority"] == HIGH_PRIORITY and row["status"] not in CLOSED_STATUSES
