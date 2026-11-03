from __future__ import annotations

import http.server
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from app.constants import HEALTH_URL_ENV
from helpers import auth_headers, make_client, uploads_dir

TASK_FIELDS = {"id", "title", "description", "status", "owner", "priority", "createdAt"}
SUMMARY_FIELDS = {"owner", "total", "byStatus", "highPriorityOpen"}
UPLOAD_FIELDS = {"owner", "fileName", "storedAt", "size"}
HEALTH_FIELDS = {"requestedBy", "status", "body"}
FORBIDDEN = {"detail": "Forbidden"}
INVALID_TOKEN = {"detail": "Invalid token"}
UNREACHABLE_HEALTH_URL = "http://127.0.0.1:9/q/health"
PDF_BYTES = b"%PDF-1.4 test"

PROTECTED_REQUESTS: list[tuple[str, str, dict[str, Any]]] = [
    ("GET", "/api/tasks", {}),
    ("POST", "/api/tasks", {"json": {"title": "x"}}),
    ("GET", "/api/summary", {}),
    ("POST", "/api/requirements", {"files": {"file": ("req.txt", b"abc", "text/plain")}}),
    ("GET", "/api/backend-health", {}),
]


@pytest.fixture
def backend_base_url() -> Iterator[str]:
    class HealthHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            status = 503 if self.path == "/down" else 200
            body = b"down" if status == 503 else b"ok"
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize(("method", "path", "kwargs"), PROTECTED_REQUESTS)
def test_every_endpoint_rejects_missing_token(tmp_path: Path, method: str, path: str, kwargs: dict[str, Any]) -> None:
    with make_client(tmp_path) as client:
        response = client.request(method, path, **kwargs)
    assert response.status_code == 401
    assert response.json() == INVALID_TOKEN


@pytest.mark.parametrize(("method", "path", "kwargs"), PROTECTED_REQUESTS)
def test_every_endpoint_rejects_expired_token(tmp_path: Path, method: str, path: str, kwargs: dict[str, Any]) -> None:
    with make_client(tmp_path) as client:
        response = client.request(method, path, headers=auth_headers(expires_in=-10), **kwargs)
    assert response.status_code == 401
    assert response.json() == INVALID_TOKEN


def test_get_tasks_returns_only_own_tasks_with_contract_fields(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/tasks", headers=auth_headers())
    assert response.status_code == 200
    tasks = response.json()
    assert tasks
    assert all(set(task) == TASK_FIELDS for task in tasks)
    assert all(task["owner"] == "student" for task in tasks)


def test_get_tasks_with_empty_owner_uses_token_identity(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        default = client.get("/api/tasks", headers=auth_headers())
        empty_owner = client.get("/api/tasks", params={"owner": ""}, headers=auth_headers())
    assert empty_owner.status_code == 200
    assert empty_owner.json() == default.json()


def test_get_tasks_returns_empty_list_for_user_without_tasks(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/tasks", headers=auth_headers("nobody"))
    assert response.status_code == 200
    assert response.json() == []


def test_get_tasks_accepts_token_without_bearer_prefix(tmp_path: Path) -> None:
    raw_token = auth_headers()["Authorization"].removeprefix("Bearer ")
    with make_client(tmp_path) as client:
        response = client.get("/api/tasks", headers={"Authorization": raw_token})
    assert response.status_code == 200


@pytest.mark.parametrize(("token_user", "owner"), [("student", "trainer"), ("trainer", "student")])
def test_get_tasks_forbids_reading_another_owner(tmp_path: Path, token_user: str, owner: str) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/tasks", params={"owner": owner}, headers=auth_headers(token_user))
    assert response.status_code == 403
    assert response.json() == FORBIDDEN


def test_post_task_returns_201_with_contract_fields(tmp_path: Path) -> None:
    payload = {"title": "Demo", "description": "d", "status": "TODO", "priority": "HIGH"}
    with make_client(tmp_path) as client:
        response = client.post("/api/tasks", json=payload, headers=auth_headers())
    assert response.status_code == 201
    body = response.json()
    assert set(body) == TASK_FIELDS
    assert body["title"] == "Demo"
    assert body["owner"] == "student"


@pytest.mark.xfail(
    strict=True,
    reason="Brecha: TaskCreate.title tiene default vacio (api/app/schemas.py:19); el payload {} se acepta con 201",
)
def test_post_task_with_empty_payload_returns_422_and_inserts_nothing(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        before = client.get("/api/tasks", headers=auth_headers()).json()
        response = client.post("/api/tasks", json={}, headers=auth_headers())
        after = client.get("/api/tasks", headers=auth_headers()).json()
    assert response.status_code == 422
    assert after == before


def test_post_task_with_non_object_body_returns_422(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.post("/api/tasks", json=[1], headers=auth_headers())
    assert response.status_code == 422


def test_post_task_rejects_foreign_owner_and_inserts_nothing(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        before = client.get("/api/tasks", headers=auth_headers()).json()
        response = client.post("/api/tasks", json={"title": "x", "owner": "trainer"}, headers=auth_headers())
        after = client.get("/api/tasks", headers=auth_headers()).json()
        trainer_tasks = client.get("/api/tasks", headers=auth_headers("trainer", "TRAINER")).json()
    assert response.status_code == 403
    assert response.json() == FORBIDDEN
    assert after == before
    assert all(task["title"] != "x" for task in trainer_tasks)


def test_summary_returns_contract_fields(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/summary", headers=auth_headers())
    assert response.status_code == 200
    body = response.json()
    assert set(body) == SUMMARY_FIELDS
    assert body["owner"] == "student"
    assert body["total"] == sum(body["byStatus"].values())


def test_summary_for_user_without_tasks_is_empty(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/summary", headers=auth_headers("nobody"))
    assert response.status_code == 200
    assert response.json() == {"owner": "nobody", "total": 0, "byStatus": {}, "highPriorityOpen": 0}


def test_summary_rejects_foreign_owner(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/summary", params={"owner": "trainer"}, headers=auth_headers())
    assert response.status_code == 403
    assert response.json() == FORBIDDEN


@pytest.mark.parametrize(("file_name", "content"), [("req.txt", b"abc"), ("spec.pdf", PDF_BYTES)])
def test_upload_stores_file_and_returns_contract_fields(tmp_path: Path, file_name: str, content: bytes) -> None:
    with make_client(tmp_path) as client:
        response = client.post(
            "/api/requirements",
            files={"file": (file_name, content, "application/octet-stream")},
            headers=auth_headers(),
        )
    assert response.status_code == 201
    body = response.json()
    assert set(body) == UPLOAD_FIELDS
    assert body["size"] == len(content)
    assert (uploads_dir(tmp_path) / file_name).read_bytes() == content


def test_upload_empty_file_is_stored_with_size_zero(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.post(
            "/api/requirements",
            files={"file": ("empty.txt", b"", "text/plain")},
            headers=auth_headers(),
        )
    assert response.status_code == 201
    assert response.json()["size"] == 0


def test_upload_without_file_returns_422(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.post("/api/requirements", headers=auth_headers())
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "file"]


@pytest.mark.xfail(strict=True, reason="H-API-05: sin validacion de extension (PLAN.md, pendiente de implementar)")
def test_upload_without_extension_is_rejected(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.post(
            "/api/requirements",
            files={"file": ("README", b"x", "text/plain")},
            headers=auth_headers(),
        )
    assert 400 <= response.status_code < 500
    assert not (uploads_dir(tmp_path) / "README").exists()


@pytest.mark.xfail(strict=True, reason="H-API-05: extension .exe no esta en la lista blanca (pendiente)")
def test_upload_disallowed_extension_is_rejected(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.post(
            "/api/requirements",
            files={"file": ("malware.exe", b"x", "application/octet-stream")},
            headers=auth_headers(),
        )
    assert 400 <= response.status_code < 500
    assert not (uploads_dir(tmp_path) / "malware.exe").exists()


@pytest.mark.xfail(strict=True, reason="H-API-05: el nombre se une sin normalizar (path traversal)")
def test_upload_path_traversal_does_not_leave_upload_dir(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        client.post(
            "/api/requirements",
            files={"file": ("../escape.txt", b"x", "text/plain")},
            headers=auth_headers(),
        )
    assert not (tmp_path / "escape.txt").exists()


def test_health_reports_backend_status_and_body(tmp_path: Path, backend_base_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(HEALTH_URL_ENV, f"{backend_base_url}/ok")
    with make_client(tmp_path) as client:
        response = client.get("/api/backend-health", headers=auth_headers())
    assert response.status_code == 200
    assert set(response.json()) == HEALTH_FIELDS
    assert response.json() == {"requestedBy": "student", "status": 200, "body": "ok"}


def test_health_passes_through_backend_error_status(tmp_path: Path, backend_base_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(HEALTH_URL_ENV, f"{backend_base_url}/down")
    with make_client(tmp_path) as client:
        response = client.get("/api/backend-health", headers=auth_headers())
    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 503, "body": "down"}


def test_health_reports_unavailable_backend_without_http_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(HEALTH_URL_ENV, UNREACHABLE_HEALTH_URL)
    with make_client(tmp_path) as client:
        response = client.get("/api/backend-health", headers=auth_headers())
    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 0, "body": "Auth backend unavailable"}
