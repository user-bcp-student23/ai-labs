from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.constants import TOKEN_AUDIENCE, TOKEN_ISSUER, TOKEN_SECRET_ENV
from app.main import create_app
from app.security import sign_claims


def signed_token(username: str = "student", role: str = "STUDENT", expires_in: int = 3600) -> str:
    claims = {
        "sub": username,
        "role": role,
        "exp": int(time.time()) + expires_in,
        "iss": TOKEN_ISSUER,
        "aud": TOKEN_AUDIENCE,
    }
    return sign_claims(claims, os.environ[TOKEN_SECRET_ENV])


def auth_headers(username: str = "student", role: str = "STUDENT", expires_in: int = 3600) -> dict[str, str]:
    return {"Authorization": f"Bearer {signed_token(username, role, expires_in)}"}


def uploads_dir(tmp_path: Path) -> Path:
    return tmp_path / "uploads"


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(str(tmp_path / "workshop.db"), str(uploads_dir(tmp_path)))
    return TestClient(app)
