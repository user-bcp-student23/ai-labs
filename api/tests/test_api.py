import asyncio
import io
import time
from pathlib import Path
from types import SimpleNamespace

import jwt
import pytest
import urllib3
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from httpx import Response

from app import main as api_main
from app.main import create_app
from app.security import verified_identity
from app.services.upload_service import store_upload


TEST_JWT_SECRET = "test-only-secret-for-api-tests-0123456789"


@pytest.fixture(autouse=True)
def configure_test_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET", TEST_JWT_SECRET)


def token(username: str = "student", role: str = "STUDENT", expires_at: int | None = None) -> str:
    expiry = expires_at if expires_at is not None else int(time.time()) + 3600
    claims = {
        "username": username,
        "role": role,
        "exp": expiry,
        "iss": "ISS",
        "aud": "CLAIM",
    }
    return jwt.encode(claims, TEST_JWT_SECRET, algorithm="HS256")


def headers(
    username: str = "student",
    role: str = "STUDENT",
    expires_at: int | None = None,
) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(username, role, expires_at)}"}


def request_endpoint(
    client: TestClient,
    endpoint: str,
    request_headers: dict[str, str],
) -> Response:
    if endpoint == "list_tasks":
        return client.get("/api/tasks", headers=request_headers)
    if endpoint == "create_task":
        return client.post("/api/tasks", headers=request_headers, json={})
    if endpoint == "summary":
        return client.get("/api/summary", headers=request_headers)
    if endpoint == "upload":
        return client.post(
            "/api/requirements",
            headers=request_headers,
            files={"file": ("sample.txt", b"Test", "text/plain")},
        )
    if endpoint == "backend_health":
        return client.get("/api/backend-health", headers=request_headers)
    raise ValueError(f"Unknown test endpoint: {endpoint}")


API_ENDPOINTS = (
    "list_tasks",
    "create_task",
    "summary",
    "upload",
    "backend_health",
)


def test_lists_seeded_tasks(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks?owner=student", headers=headers())
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["owner"] == "student"
    assert response.json()[0]["title"] == "Refactor login"


def test_empty_owner_query_uses_authenticated_identity(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks?owner=", headers=headers())
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert {task["owner"] for task in response.json()} == {"student"}


def test_every_endpoint_requires_bearer_authentication(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        for endpoint in API_ENDPOINTS:
            response = request_endpoint(client, endpoint, {})
            assert response.status_code == 401
            assert response.json() == {"detail": "Invalid token"}


def test_missing_secret_returns_server_error_on_every_endpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SECRET")
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app, raise_server_exceptions=False) as client:
        for endpoint in API_ENDPOINTS:
            response = request_endpoint(client, endpoint, headers())
            assert response.status_code == 500
            assert response.text == "Internal Server Error"


def test_task_filter_treats_sql_syntax_in_username_as_literal(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get(
            "/api/tasks",
            headers=headers(username="student' OR '1'='1"),
        )
    assert response.status_code == 200
    assert response.json() == []


def test_summary_filter_treats_sql_syntax_in_username_as_literal(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get(
            "/api/summary",
            headers=headers(username="student' OR '1'='1"),
        )
    assert response.status_code == 200
    assert response.json() == {
        "owner": "student' OR '1'='1",
        "total": 0,
        "byStatus": {},
        "highPriorityOpen": 0,
    }


def test_summary_empty_owner_query_uses_authenticated_identity(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary?owner=", headers=headers())
    assert response.status_code == 200
    assert response.json()["owner"] == "student"
    assert response.json()["total"] == 2


def test_rejects_tasks_for_different_owner(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks?owner=trainer", headers=headers())
    assert response.status_code == 403
    assert response.json() == {"detail": "Owner does not match authenticated identity"}


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
    assert created.json()["title"] == "Add tests"
    assert created.json()["description"] == "Improve coverage"
    assert created.json()["status"] == "TODO"
    assert created.json()["priority"] == "HIGH"
    assert created.json()["owner"] == "student"
    assert summary.json()["total"] == 3


def test_summary_returns_complete_counts_for_owner(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary?owner=student", headers=headers())
    assert response.status_code == 200
    assert response.json() == {
        "owner": "student",
        "total": 2,
        "byStatus": {"TODO": 1, "IN_PROGRESS": 1},
        "highPriorityOpen": 1,
    }


def test_task_fields_containing_quotes_are_persisted_literally(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post(
            "/api/tasks",
            headers=headers(),
            json={
                "title": "O'Reilly",
                "description": "author's test",
                "status": "TODO",
                "priority": "HIGH",
            },
        )
    assert response.status_code == 201
    assert response.json()["title"] == "O'Reilly"
    assert response.json()["description"] == "author's test"


def test_empty_task_object_uses_documented_defaults(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post("/api/tasks", headers=headers(), json={})
    assert response.status_code == 201
    assert response.json()["title"] == ""
    assert response.json()["description"] == ""
    assert response.json()["status"] == "TODO"
    assert response.json()["priority"] == "MEDIUM"
    assert response.json()["owner"] == "student"


@pytest.mark.parametrize(
    ("body_kind", "expected_error_type"),
    [
        ("missing", "missing"),
        ("invalid_json", "json_invalid"),
        ("array", "model_attributes_type"),
    ],
)
def test_task_body_validation_returns_422(
    tmp_path: Path,
    body_kind: str,
    expected_error_type: str,
) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        if body_kind == "missing":
            response = client.post("/api/tasks", headers=headers())
        elif body_kind == "invalid_json":
            response = client.post(
                "/api/tasks",
                headers={**headers(), "Content-Type": "application/json"},
                content="{",
            )
        else:
            response = client.post("/api/tasks", headers=headers(), json=[])
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == expected_error_type


def test_coerces_json_values_as_before_and_keeps_defaults(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": 42},
        )
    assert response.status_code == 201
    assert response.json()["title"] == "42"
    assert response.json()["description"] == ""
    assert response.json()["status"] == "TODO"
    assert response.json()["priority"] == "MEDIUM"
    assert response.json()["owner"] == "student"


def test_rejects_creating_task_for_different_owner(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Cross-owner task", "owner": "trainer"},
        )
    assert response.status_code == 403
    assert response.json() == {"detail": "Owner does not match authenticated identity"}


def test_rejects_empty_explicit_owner_in_task_body(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Task", "owner": ""},
        )
    assert response.status_code == 403
    assert response.json() == {"detail": "Owner does not match authenticated identity"}


def test_rejects_summary_for_different_owner(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary?owner=trainer", headers=headers())
    assert response.status_code == 403
    assert response.json() == {"detail": "Owner does not match authenticated identity"}


def test_uploads_requirement(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"Test", "text/plain")},
        )
    assert response.status_code == 201
    assert (upload_dir / "requirements.txt").exists()
    assert response.json()["fileName"] == "requirements.txt"
    assert response.json()["size"] == 4
    assert (upload_dir / "requirements.txt").read_bytes() == b"Test"


def test_accepts_pdf_upload(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("brief.pdf", b"PDF!", "application/pdf")},
        )
    assert response.status_code == 201
    assert response.json()["fileName"] == "brief.pdf"


def test_accepts_uppercase_allowed_extension(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("brief.PDF", b"PDF!", "application/pdf")},
        )
    assert response.status_code == 201
    assert response.json()["fileName"] == "brief.PDF"


def test_accepts_empty_upload_as_size_boundary(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("empty.txt", b"", "text/plain")},
        )
    assert response.status_code == 201
    assert response.json()["size"] == 0
    assert (upload_dir / "empty.txt").read_bytes() == b""


def test_rejects_upload_filename_without_extension(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements", b"test", "text/plain")},
        )
    assert response.status_code == 415
    assert response.json() == {"detail": "Invalid upload"}


def test_missing_upload_file_returns_422(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post("/api/requirements", headers=headers())
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "missing"


def test_rejects_disallowed_extension(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.exe", b"test", "application/octet-stream")},
        )
    assert response.status_code == 415
    assert response.json() == {"detail": "Invalid upload"}
    assert not (tmp_path / "uploads" / "requirements.exe").exists()


def test_rejects_oversized_file(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"12345", "text/plain")},
        )
    assert response.status_code == 413
    assert response.json() == {"detail": "Invalid upload"}
    assert not (tmp_path / "uploads" / "requirements.txt").exists()


def test_assigns_unique_name_when_uploaded_filename_exists(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        first = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"one", "text/plain")},
        )
        second = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"two", "text/plain")},
        )
    assert first.status_code == second.status_code == 201
    assert first.json()["fileName"] == "requirements.txt"
    assert second.json()["fileName"] == "requirements_1.txt"
    assert (upload_dir / "requirements.txt").read_bytes() == b"one"
    assert (upload_dir / "requirements_1.txt").read_bytes() == b"two"


def test_normalizes_uploaded_path_to_filename(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("../../outside.txt", b"safe", "text/plain")},
        )
    stored_path = Path(response.json()["storedAt"])
    assert response.status_code == 201
    assert stored_path.resolve().parent == upload_dir.resolve()
    assert response.json()["fileName"] == "outside.txt"
    assert not (tmp_path / "outside.txt").exists()


def test_rejects_upload_without_filename(tmp_path: Path) -> None:
    upload = UploadFile(filename="", file=io.BytesIO(b"test"))
    with pytest.raises(HTTPException) as error:
        asyncio.run(store_upload(upload, tmp_path))
    assert error.value.status_code == 415
    assert error.value.detail == "Invalid upload"


def test_rejects_malformed_bearer_header(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get(
            "/api/tasks",
            headers={"Authorization": "Basic token"},
        )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_requires_configured_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SECRET")
    with pytest.raises(RuntimeError, match="JWT verification key is not configured correctly"):
        verified_identity(authorization="Bearer token")


def test_rejects_invalid_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


@pytest.mark.parametrize(
    ("issuer", "audience"),
    [("wrong-issuer", "CLAIM"), ("ISS", "wrong-audience")],
)
def test_rejects_token_with_invalid_issuer_or_audience(
    tmp_path: Path,
    issuer: str,
    audience: str,
) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    claims = {
        "username": "student",
        "role": "STUDENT",
        "exp": int(time.time()) + 3600,
        "iss": issuer,
        "aud": audience,
    }
    invalid_token = jwt.encode(claims, TEST_JWT_SECRET, algorithm="HS256")
    with TestClient(app) as client:
        response = client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_rejects_token_with_invalid_signature(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    invalid_token = jwt.encode(
        {
            "username": "student",
            "role": "STUDENT",
            "exp": int(time.time()) + 3600,
            "iss": "ISS",
            "aud": "CLAIM",
        },
        "different-test-only-secret-0123456789",
        algorithm="HS256",
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_rejects_token_missing_required_claim(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    incomplete_token = jwt.encode(
        {
            "username": "student",
            "role": "STUDENT",
            "exp": int(time.time()) + 3600,
            "iss": "ISS",
        },
        TEST_JWT_SECRET,
        algorithm="HS256",
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {incomplete_token}"},
        )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_rejects_expired_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get(
            "/api/tasks",
            headers=headers(expires_at=int(time.time()) - 1),
        )
    assert response.status_code == 401


def test_backend_health_uses_verified_identity_attribute(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class SuccessfulPoolManager:
        def request(self, method: str, url: str, timeout: float) -> SimpleNamespace:
            assert method == "GET"
            assert url.startswith("http")
            assert timeout == 3.0
            return SimpleNamespace(
                status=200,
                data=b'{"status":"UP"}',
            )

    monkeypatch.setattr(api_main.urllib3, "PoolManager", SuccessfulPoolManager)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.status_code == 200
    assert response.json() == {
        "requestedBy": "student",
        "status": 200,
        "body": '{"status":"UP"}',
    }


def test_backend_health_preserves_upstream_503_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_HEALTH_URL", "http://auth.local/q/health")

    class UnavailablePoolManager:
        def request(self, method: str, url: str, timeout: float) -> SimpleNamespace:
            assert method == "GET"
            assert url == "http://auth.local/q/health"
            assert timeout == 3.0
            return SimpleNamespace(status=503, data=b"unavailable")

    monkeypatch.setattr(api_main.urllib3, "PoolManager", UnavailablePoolManager)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.status_code == 200
    assert response.json() == {
        "requestedBy": "student",
        "status": 503,
        "body": "unavailable",
    }


def test_backend_health_replaces_invalid_utf8_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class InvalidUtf8PoolManager:
        def request(self, method: str, url: str, timeout: float) -> SimpleNamespace:
            assert method == "GET"
            assert url.startswith("http")
            assert timeout == 3.0
            return SimpleNamespace(status=200, data=b"\xff")

    monkeypatch.setattr(api_main.urllib3, "PoolManager", InvalidUtf8PoolManager)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.status_code == 200
    assert response.json()["body"] == "\ufffd"


def test_backend_health_hides_transport_exception_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingPoolManager:
        def request(self, method: str, url: str, timeout: float) -> None:
            assert method == "GET"
            assert url.startswith("http")
            assert timeout == 3.0
            raise urllib3.exceptions.HTTPError("sensitive connection detail")

    monkeypatch.setattr(api_main.urllib3, "PoolManager", FailingPoolManager)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.status_code == 200
    assert response.json() == {
        "requestedBy": "student",
        "status": 0,
        "body": "Health check unavailable",
    }
    assert "sensitive connection detail" not in response.text
