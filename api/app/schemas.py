from __future__ import annotations

import sqlite3
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.constants import DEFAULT_PRIORITY, DEFAULT_STATUS


def _as_text(value: object) -> str:
    return str(value)


Text = Annotated[str, BeforeValidator(_as_text)]


class TaskCreate(BaseModel):
    title: Text = ""
    description: Text = ""
    status: Text = DEFAULT_STATUS
    priority: Text = DEFAULT_PRIORITY
    owner: Text = ""


class TaskOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    title: str
    description: str
    status: str
    owner: str
    priority: str
    created_at: str = Field(alias="createdAt")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> TaskOut:
        return cls(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            owner=row["owner"],
            priority=row["priority"],
            created_at=row["created_at"],
        )


class SummaryOut(BaseModel):
    owner: str
    total: int
    byStatus: dict[str, int]
    highPriorityOpen: int


class Identity(BaseModel):
    username: str
    role: str


class UploadOut(BaseModel):
    owner: str
    fileName: str | None
    storedAt: str
    size: int


class HealthOut(BaseModel):
    requestedBy: str
    status: int
    body: str
