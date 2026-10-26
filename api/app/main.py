from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path

import urllib3
from fastapi import Body, Depends, FastAPI, File, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    BackendHealthResponse,
    Identity,
    TaskCreateRequest,
    TaskResponse,
    TaskSummaryResponse,
    UploadResponse,
)
from app.security import verified_identity
from app.services.task_service import resolve_authorized_owner
from app.services.upload_service import store_upload

LOGGER = logging.getLogger(__name__)


def create_app(db_path: str | None = None, upload_dir: str | None = None) -> FastAPI:
    selected_db = db_path or os.getenv("WORKSHOP_DB_PATH", "./data/workshop.db")
    selected_uploads = upload_dir or os.getenv("WORKSHOP_UPLOAD_DIR", "./uploads")
    Path(selected_db).parent.mkdir(parents=True, exist_ok=True)
    Path(selected_uploads).mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(selected_db, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL, owner TEXT NOT NULL, priority TEXT NOT NULL, created_at TEXT NOT NULL)")
    count = connection.execute("SELECT COUNT(*) AS total FROM tasks").fetchone()["total"]
    if count == 0:
        connection.execute("INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('Refactor login','Separar responsabilidades en frontend','TODO','student','HIGH',datetime('now'))")
        connection.execute("INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('Review API','Revisar seguridad de endpoints','IN_PROGRESS','student','MEDIUM',datetime('now'))")
        connection.execute("INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('Trainer notes','Preparar retrospectiva','TODO','trainer','LOW',datetime('now'))")
        connection.commit()

    app = FastAPI(title="Workshop Requirements API", version="0.1.0")
    app.state.connection = connection
    app.state.upload_dir = selected_uploads
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def as_task(row: sqlite3.Row) -> TaskResponse:
        return TaskResponse(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            owner=row["owner"],
            priority=row["priority"],
            createdAt=row["created_at"],
        )

    @app.get("/api/tasks")
    def list_tasks(
        owner: str | None = Query(default=None),
        identity: Identity = Depends(verified_identity),
    ) -> list[TaskResponse]:
        requested_owner = resolve_authorized_owner(identity, owner or None)
        rows = connection.execute(
            "SELECT id,title,description,status,owner,priority,created_at "
            "FROM tasks WHERE owner = ? ORDER BY id",
            (requested_owner,),
        ).fetchall()
        return [as_task(row) for row in rows]

    @app.post("/api/tasks", status_code=201, response_model=TaskResponse)
    def create_task(
        payload: TaskCreateRequest = Body(...),
        identity: Identity = Depends(verified_identity),
    ) -> TaskResponse:
        title = str(payload.title)
        description = str(payload.description)
        status = str(payload.status)
        priority = str(payload.priority)
        requested_owner = (
            str(payload.owner)
            if "owner" in payload.model_fields_set
            else None
        )
        owner = resolve_authorized_owner(identity, requested_owner)
        cursor = connection.execute(
            "INSERT INTO tasks(title,description,status,owner,priority,created_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (title, description, status, owner, priority),
        )
        connection.commit()
        row = connection.execute(
            "SELECT id,title,description,status,owner,priority,created_at "
            "FROM tasks WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return as_task(row)

    @app.get("/api/summary", response_model=TaskSummaryResponse)
    def summary(
        owner: str | None = Query(default=None),
        identity: Identity = Depends(verified_identity),
    ) -> TaskSummaryResponse:
        requested_owner = resolve_authorized_owner(identity, owner or None)
        rows = connection.execute(
            "SELECT status,priority FROM tasks WHERE owner = ?",
            (requested_owner,),
        ).fetchall()
        response = TaskSummaryResponse(
            owner=requested_owner,
            total=0,
            byStatus={},
            highPriorityOpen=0,
        )
        for row in rows:
            response.total += 1
            response.by_status[row["status"]] = response.by_status.get(row["status"], 0) + 1
            if row["priority"] == "HIGH" and row["status"] not in {"DONE", "ARCHIVED"}:
                response.high_priority_open += 1
        return response

    @app.post("/api/requirements", status_code=201, response_model=UploadResponse)
    async def upload_requirement(
        file: UploadFile = File(...),
        identity: Identity = Depends(verified_identity),
    ) -> UploadResponse:
        target, size = await store_upload(file, Path(selected_uploads))
        return UploadResponse(
            owner=identity.username,
            fileName=target.name,
            storedAt=str(target),
            size=size,
        )

    @app.get("/api/backend-health", response_model=BackendHealthResponse)
    def backend_health(identity: Identity = Depends(verified_identity)) -> BackendHealthResponse:
        url = os.getenv("AUTH_HEALTH_URL", "http://localhost:8080/q/health")
        try:
            response = urllib3.PoolManager().request("GET", url, timeout=3.0)
            return BackendHealthResponse(
                requestedBy=identity.username,
                status=response.status,
                body=response.data.decode("utf-8", errors="replace"),
            )
        except urllib3.exceptions.HTTPError as error:
            LOGGER.warning("Backend health request failed: %s", type(error).__name__)
            return BackendHealthResponse(
                requestedBy=identity.username,
                status=0,
                body="Health check unavailable",
            )

    @app.on_event("shutdown")
    def close_connection() -> None:
        connection.close()

    return app


app = create_app()
