import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.constants import TOKEN_AUDIENCE, TOKEN_ISSUER, TOKEN_SECRET_ENV
from app.main import create_app
from app.security import sign_claims

FRONTEND_ORIGIN = "http://localhost:4200"
UNLISTED_ORIGIN = "https://evil.example"
UNREACHABLE_HEALTH_URL = "http://127.0.0.1:9/q/health"


def auth_headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    claims = {
        "sub": username,
        "role": role,
        "exp": int(time.time()) + 3600,
        "iss": TOKEN_ISSUER,
        "aud": TOKEN_AUDIENCE,
    }
    return {"Authorization": f"Bearer {sign_claims(claims, os.environ[TOKEN_SECRET_ENV])}"}


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    return TestClient(app)


def test_cors_allows_frontend_origin(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/tasks", headers={**auth_headers(), "Origin": FRONTEND_ORIGIN})
    assert response.headers.get("access-control-allow-origin") == FRONTEND_ORIGIN


def test_cors_omits_header_for_unlisted_origin(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/tasks", headers={**auth_headers(), "Origin": UNLISTED_ORIGIN})
    assert "access-control-allow-origin" not in response.headers


def test_health_error_body_hides_exception_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_HEALTH_URL", UNREACHABLE_HEALTH_URL)
    with make_client(tmp_path) as client:
        response = client.get("/api/backend-health", headers=auth_headers())
    body = response.json()
    assert body["status"] == 0
    assert "127.0.0.1" not in body["body"]
    assert "Max retries" not in body["body"]


def test_health_response_shape_is_kept(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_HEALTH_URL", UNREACHABLE_HEALTH_URL)
    with make_client(tmp_path) as client:
        response = client.get("/api/backend-health", headers=auth_headers())
    assert set(response.json()) == {"requestedBy", "status", "body"}
    assert response.json()["requestedBy"] == "student"


def test_upload_response_shape_is_kept(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.post(
            "/api/requirements",
            headers=auth_headers(),
            files={"file": ("requirements.txt", b"abc", "text/plain")},
        )
    assert response.status_code == 201
    assert set(response.json()) == {"owner", "fileName", "storedAt", "size"}
    assert response.json()["size"] == 3


def test_trainer_summary_counts_own_tasks(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/summary", headers=auth_headers("trainer", "TRAINER"))
    assert response.json() == {
        "owner": "trainer",
        "total": 1,
        "byStatus": {"TODO": 1},
        "highPriorityOpen": 0,
    }
