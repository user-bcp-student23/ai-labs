from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.constants import (
    CORS_ORIGIN_ENV,
    DB_PATH_ENV,
    DEFAULT_CORS_ORIGIN,
    DEFAULT_DB_PATH,
    DEFAULT_UPLOAD_DIR,
    UPLOAD_DIR_ENV,
)
from app.database import open_database
from app.repository import TaskRepository
from app.routes import health, requirements, tasks
from app.security import load_token_secret


def create_app(db_path: str | None = None, upload_dir: str | None = None) -> FastAPI:
    token_secret = load_token_secret()
    selected_db = db_path or os.getenv(DB_PATH_ENV, DEFAULT_DB_PATH)
    selected_uploads = upload_dir or os.getenv(UPLOAD_DIR_ENV, DEFAULT_UPLOAD_DIR)
    Path(selected_uploads).mkdir(parents=True, exist_ok=True)

    connection = open_database(selected_db)

    app = FastAPI(title="Workshop Requirements API", version="0.1.0")
    app.state.connection = connection
    app.state.repository = TaskRepository(connection)
    app.state.upload_dir = selected_uploads
    app.state.token_secret = token_secret
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv(CORS_ORIGIN_ENV, DEFAULT_CORS_ORIGIN)],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(tasks.router)
    app.include_router(requirements.router)
    app.include_router(health.router)

    @app.on_event("shutdown")
    def close_connection() -> None:
        connection.close()

    return app


app = create_app()
