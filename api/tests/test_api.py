import base64
import json
import os
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.constants import TOKEN_AUDIENCE, TOKEN_ISSUER, TOKEN_SECRET_ENV
from app.main import create_app
from app.security import sign_claims


def token(username: str = "student", role: str = "STUDENT") -> str:
    claims = {
        "sub": username,
        "role": role,
        "exp": int(time.time()) + 3600,
        "iss": TOKEN_ISSUER,
        "aud": TOKEN_AUDIENCE,
    }
    return sign_claims(claims, os.environ[TOKEN_SECRET_ENV])


def headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(username, role)}"}


def test_lists_seeded_tasks(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers())
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_creates_task_and_summary(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Add tests", "description": "Improve coverage", "status": "TODO", "priority": "HIGH"},
        )
        summary = client.get("/api/summary", headers=headers())
    assert created.status_code == 201
    assert created.json()["owner"] == "student"
    assert summary.json()["total"] == 3


def test_uploads_requirement(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"Login must be accessible", "text/plain")},
        )
    assert response.status_code == 201
    assert (upload_dir / "requirements.txt").exists()


def test_rejects_invalid_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_summary_counts_seeded_tasks_by_status_and_priority(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary", headers=headers())
    assert response.json() == {
        "owner": "student",
        "total": 2,
        "byStatus": {"TODO": 1, "IN_PROGRESS": 1},
        "highPriorityOpen": 1,
    }


def test_listing_returns_task_shape(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers())
    first = response.json()[0]
    assert set(first) == {"id", "title", "description", "status", "owner", "priority", "createdAt"}
    assert first["title"] == "Refactor login"


def test_closed_high_priority_tasks_are_not_counted_as_open(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        for status in ("DONE", "ARCHIVED"):
            client.post("/api/tasks", headers=headers(), json={"title": status, "status": status, "priority": "HIGH"})
        summary = client.get("/api/summary", headers=headers())
    assert summary.json()["total"] == 4
    assert summary.json()["highPriorityOpen"] == 1


def test_create_task_applies_defaults(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post("/api/tasks", headers=headers(), json={"title": "Only title"})
    created = response.json()
    assert response.status_code == 201
    assert created["description"] == ""
    assert created["status"] == "TODO"
    assert created["priority"] == "MEDIUM"
    assert created["owner"] == "student"


def test_owner_equal_to_identity_behaves_like_default(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        default_list = client.get("/api/tasks", headers=headers()).json()
        explicit_list = client.get("/api/tasks", params={"owner": "student"}, headers=headers()).json()
        created = client.post("/api/tasks", headers=headers(), json={"title": "Mine", "owner": "student"})
    assert explicit_list == default_list
    assert created.status_code == 201
    assert created.json()["owner"] == "student"


def test_owner_query_cannot_inject_sql(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", params={"owner": "x' OR '1'='1"}, headers=headers())
    assert response.status_code != 200 or response.json() == []


def test_create_task_stores_quotes_as_literal_text(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    injected_title = "x','a','TODO','student','HIGH',datetime('now'))--"
    with TestClient(app) as client:
        created = client.post("/api/tasks", headers=headers(), json={"title": injected_title, "description": "d"})
        summary = client.get("/api/summary", headers=headers())
    assert created.json()["title"] == injected_title
    assert summary.json()["total"] == 3


def test_student_cannot_list_trainer_tasks(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", params={"owner": "trainer"}, headers=headers())
    assert response.status_code == 403


def test_student_cannot_create_task_for_trainer(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post("/api/tasks", headers=headers(), json={"title": "t", "owner": "trainer"})
    assert response.status_code == 403


def test_rejects_legacy_token_with_embedded_secret(tmp_path: Path) -> None:
    raw = f"student|STUDENT|{int(time.time()) + 3600}|WORKSHOP_SECRET_2026"
    legacy = base64.b64encode(raw.encode()).decode()
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": f"Bearer {legacy}"})
    assert response.status_code == 401


def test_rejects_unsigned_claims(tmp_path: Path) -> None:
    claims = {"sub": "student", "role": "STUDENT", "exp": int(time.time()) + 3600}
    unsigned = base64.b64encode(json.dumps(claims).encode()).decode()
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": f"Bearer {unsigned}"})
    assert response.status_code == 401
