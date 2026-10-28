# Pruebas — componente `api`

Los casos de esta matriz verifican el contrato de [ENDPOINTS.md](./ENDPOINTS.md). El código ejecutable completo, incluidos los tests existentes, está en [`api/tests/test_api.py`](../api/tests/test_api.py). Los ejemplos de código bajo este cuadro corresponden a los casos añadidos para cubrir los huecos detectados.

## Matriz de casos

| endpoint | caso | tipo | resultado esperado |
|---|---|---|---|
| `GET /api/tasks` | Listar tareas semilla para `student` (`test_lists_seeded_tasks`; `api/tests/test_api.py:79`) | Camino feliz | HTTP 200; dos tareas del owner autenticado. |
| `GET /api/tasks` | `owner=` vacío usa la identidad del token (`test_empty_owner_query_uses_authenticated_identity`; `api/tests/test_api.py:89`) | Borde | HTTP 200; devuelve las tareas de `student`. |
| `GET /api/tasks` | Username firmado que contiene sintaxis SQL (`test_task_filter_treats_sql_syntax_in_username_as_literal`; `api/tests/test_api.py:120`) | Borde | HTTP 200 y lista vacía; ningún filtro SQL se altera. H-API-03. |
| `GET /api/tasks` | Owner de otro usuario (`test_rejects_tasks_for_different_owner`; `api/tests/test_api.py:156`) | Error | HTTP 403, `{"detail":"Owner does not match authenticated identity"}`. H-API-02. |
| `GET /api/tasks` | Sin Bearer token (`test_every_endpoint_requires_bearer_authentication`; `api/tests/test_api.py:98`) | Error | HTTP 401, `{"detail":"Invalid token"}`. |
| `GET /api/tasks` | `SECRET` ausente (`test_missing_secret_returns_server_error_on_every_endpoint`; `api/tests/test_api.py:107`) | Error | HTTP 500, cuerpo `Internal Server Error`. |
| `POST /api/tasks` | Crear tarea válida (`test_creates_task_and_summary`; `api/tests/test_api.py:164`) | Camino feliz | HTTP 201; respuesta con los campos de la tarea y owner autenticado. |
| `POST /api/tasks` | Objeto JSON vacío (`test_empty_task_object_uses_documented_defaults`; `api/tests/test_api.py:213`) | Borde | HTTP 201; defaults: título/descripción vacíos, estado `TODO`, prioridad `MEDIUM` y owner autenticado. |
| `POST /api/tasks` | Texto con comillas (`test_task_fields_containing_quotes_are_persisted_literally`; `api/tests/test_api.py:195`) | Borde | HTTP 201; los valores se conservan literalmente. H-API-03. |
| `POST /api/tasks` | Body ausente, JSON no válido o raíz que no sea objeto (`test_task_body_validation_returns_422`; `api/tests/test_api.py:233`) | Error | HTTP 422; detalle de validación FastAPI/Pydantic. |
| `POST /api/tasks` | Owner distinto o vacío explícito (`test_rejects_creating_task_for_different_owner`, `test_rejects_empty_explicit_owner_in_task_body`; `api/tests/test_api.py:270,282`) | Error | HTTP 403 con detalle genérico de discrepancia. H-API-02. |
| `POST /api/tasks` | Sin Bearer token / `SECRET` ausente | Error | HTTP 401 / HTTP 500, respectivamente; ver tests compartidos en `api/tests/test_api.py:98,107`. |
| `GET /api/summary` | Resumen de tareas de `student` (`test_summary_returns_complete_counts_for_owner`; `api/tests/test_api.py:182`) | Camino feliz | HTTP 200; `total: 2`, `byStatus: {"TODO": 1, "IN_PROGRESS": 1}` y `highPriorityOpen: 1`. |
| `GET /api/summary` | `owner=` vacío y username sin tareas (`test_summary_empty_owner_query_uses_authenticated_identity`, `test_summary_filter_treats_sql_syntax_in_username_as_literal`; `api/tests/test_api.py:147,131`) | Borde | HTTP 200; owner de la identidad y contadores vacíos cuando no tiene filas. H-API-03. |
| `GET /api/summary` | Owner de otro usuario (`test_rejects_summary_for_different_owner`; `api/tests/test_api.py:294`) | Error | HTTP 403 con detalle genérico de discrepancia. H-API-02. |
| `GET /api/summary` | Sin Bearer token / `SECRET` ausente | Error | HTTP 401 / HTTP 500, respectivamente; ver tests compartidos en `api/tests/test_api.py:98,107`. |
| `POST /api/requirements` | Cargar `.txt` y `.pdf` válidos (`test_uploads_requirement`, `test_accepts_pdf_upload`; `api/tests/test_api.py:302,318`) | Camino feliz | HTTP 201; metadatos de archivo y contenido guardado. H-API-04. |
| `POST /api/requirements` | Archivo vacío, límite inclusivo de 4 bytes y extensión permitida en mayúsculas (`test_accepts_empty_upload_as_size_boundary`, `test_uploads_requirement`, `test_accepts_uppercase_allowed_extension`; `api/tests/test_api.py:342,302,330`) | Borde | HTTP 201; tamaño 0 y tamaño 4 aceptados; `.PDF` es válido. H-API-04. |
| `POST /api/requirements` | Nombre repetido o nombre con separadores (`test_assigns_unique_name_when_uploaded_filename_exists`, `test_normalizes_uploaded_path_to_filename`; `api/tests/test_api.py:402,423`) | Borde | HTTP 201; nombre único y destino contenido en el directorio de carga. H-API-04. |
| `POST /api/requirements` | Falta el campo `file` (`test_missing_upload_file_returns_422`; `api/tests/test_api.py:368`) | Error | HTTP 422, detalle `missing` del campo multipart `file`. |
| `POST /api/requirements` | Extensión no permitida o nombre sin extensión (`test_rejects_disallowed_extension`, `test_rejects_upload_filename_without_extension`; `api/tests/test_api.py:376,356`) | Error | HTTP 415, `{"detail":"Invalid upload"}`. H-API-04. |
| `POST /api/requirements` | Archivo de 5 bytes (`test_rejects_oversized_file`; `api/tests/test_api.py:389`) | Error | HTTP 413, `{"detail":"Invalid upload"}`. H-API-04. |
| `POST /api/requirements` | Sin Bearer token / `SECRET` ausente | Error | HTTP 401 / HTTP 500, respectivamente; ver tests compartidos en `api/tests/test_api.py:98,107`. |
| `GET /api/backend-health` | Backend responde 200 (`test_backend_health_uses_verified_identity_attribute`; `api/tests/test_api.py:551`) | Camino feliz | HTTP 200; incluye username validado, status upstream y body. H-API-06. |
| `GET /api/backend-health` | Backend responde 503 (`test_backend_health_preserves_upstream_503_status`; `api/tests/test_api.py:577`) | Borde | HTTP 200 de la API con `status: 503` y body upstream. |
| `GET /api/backend-health` | Fallo HTTP de urllib3 (`test_backend_health_hides_transport_exception_details`; `api/tests/test_api.py:621`) | Error controlado | HTTP 200 con `status: 0` y `body: "Health check unavailable"`; no filtra el texto de la excepción. H-API-06. |
| `GET /api/backend-health` | Bytes upstream que no son UTF-8 (`test_backend_health_replaces_invalid_utf8_bytes`; `api/tests/test_api.py:602`) | Borde | HTTP 200; bytes inválidos se sustituyen por `�`. |
| `GET /api/backend-health` | Sin Bearer token / `SECRET` ausente | Error | HTTP 401 / HTTP 500, respectivamente; ver tests compartidos en `api/tests/test_api.py:98,107`. |

## Código de los tests añadidos

El helper hace requests válidos a cada ruta para probar de forma común las respuestas de autenticación y configuración:

```python
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
```

Los casos de borde específicos se implementan en el mismo módulo:

```python
def test_empty_owner_query_uses_authenticated_identity(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks?owner=", headers=headers())
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert {task["owner"] for task in response.json()} == {"student"}


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


def test_missing_upload_file_returns_422(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post("/api/requirements", headers=headers())
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "missing"
```

Las validaciones del body de tarea y el passthrough del status upstream también se prueban explícitamente:

```python
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
```

El resto del código de tests para camino feliz, autorización, JWT, carga, path normalization, SQL y health está en [`api/tests/test_api.py`](../api/tests/test_api.py); la matriz mapea esos tests por endpoint.

## Ejecuciones

Todos los comandos se ejecutaron el 2026-10-26 con el directorio de trabajo `api/`, en Windows con Python 3.14.7. Los IDs corresponden a hallazgos de `api`.

| componente e IDs | comando | directorio | código de salida | resultado |
|---|---|---|---:|---|
| `api`; H-API-01, H-API-02, H-API-03, H-API-04, H-API-06; línea base antes de añadir cobertura | `python -m pytest --cov=app --cov-report=term-missing` | `api/` | 0 | 27 pasaron; cobertura global reportada 98%. |
| `api`; H-API-01, H-API-02, H-API-03, H-API-04, H-API-06; casos añadidos | `python -m pytest tests/test_api.py -k "empty_owner or every_endpoint or missing_secret_returns_server_error or empty_task_object or task_body_validation or accepts_empty_upload or filename_without_extension or missing_upload_file or backend_health_preserves_upstream_503" -q` | `api/` | 0 | 11 pasaron. |
| `api`; H-API-02; validación del body de creación | `python -m pytest tests/test_api.py::test_task_body_validation_returns_422 -q` | `api/` | 0 | 3 pasaron: body ausente, JSON no válido y raíz array. |
| `api`; H-API-01, H-API-02, H-API-03, H-API-04, H-API-06; regresión final y cobertura | `python -m pytest --cov=app --cov-report=term-missing` | `api/` | 0 | 42 pasaron; 83 warnings de deprecación; cobertura global 98%. |
| `api`; H-API-01, H-API-02, H-API-03, H-API-04, H-API-06; detalle de sentencias por módulo, usando los datos de cobertura de la ejecución final | `python -c "from coverage import Coverage; c=Coverage(); c.load(); files=['app/main.py','app/schemas.py','app/security.py','app/services/task_service.py','app/services/upload_service.py']; [print(f'{f}: {len(c.analysis2(f)[1])-len(c.analysis2(f)[3])}/{len(c.analysis2(f)[1])} statements') for f in files]"` | `api/` | 0 | `main.py` 79/79; `schemas.py` 39/39; `security.py` 26/26; `task_service.py` 7/7; `upload_service.py` 36/37. |

## Cobertura

Coverage.py ejecutó medición de sentencias y ramas con `--cov=app --cov-report=term-missing`.

- **Módulos runtime de API bajo prueba:** `main.py` 79/79 sentencias (100%); `schemas.py` 39/39 (100%); `security.py` 26/26 (100%); `task_service.py` 7/7 (100%); `upload_service.py` 36/37 (97,3%). Todos superan el objetivo de 85%.
- **Global de `app/`:** 187/188 sentencias cubiertas (99,5% de sentencias); la métrica combinada de sentencias y ramas de Coverage.py reportó 98% (24 branches, 3 parciales). La única sentencia no cubierta es el rechazo de un candidato fuera del directorio en `_filename_candidates` (`api/app/services/upload_service.py:49`); los tests de colisión sí se ejecutaron.
- En esta tarea se modificó el módulo de tests; Coverage.py mide `app/`, no el código de tests en sí. La suite ejecutó los 42 tests y los módulos de API relacionados quedaron medidos por separado arriba.

## Fallos, pendientes y propuestas

### Fallos

- Ninguno en la suite final. Los 83 warnings son deprecaciones de `FastAPI.on_event`/Starlette y no fallos de tests; no se ocultaron.

### Pendientes

- No se ejecutó una integración con el emisor JWT real ni con un servicio externo de autenticación. Los tests usan una clave ficticia y un mock local para `backend-health`; H-API-01 y H-API-02 siguen sujetos a confirmar el contrato y la configuración externa.
- No se ejecutó el servicio real indicado por `AUTH_HEALTH_URL`; las respuestas upstream 200, 503 y error de transporte se verificaron con mocks locales.
- La línea de colisión no cubierta del servicio de carga se reporta explícitamente; no se bajó ni excluyó ningún quality gate.

### Pruebas propuestas

- Cuando esté disponible el entorno integrado, obtener un token de prueba del emisor acordado y ejecutar los cinco endpoints contra la API local, comprobando `iss`, `aud`, `exp`, `username`, `role` y configuración de `SECRET`.
- Con el servicio de autenticación local activo, comprobar que `/api/backend-health` devuelve el status y body reales; no se realizó esta prueba en esta ejecución.

## Documentos y código consultados

- `README.md`, `RETO.md`, `docs/GOOD_PRACTICES.md`, `HALLAZGOS.md`, `PLAN.md` y `docs/ENDPOINTS.md`.
- Código del alcance `api/`: `api/app/main.py`, `api/app/schemas.py`, `api/app/security.py`, `api/app/services/task_service.py`, `api/app/services/upload_service.py` y `api/tests/test_api.py`.

## Componente auth — H-AUTH-01

La suite comprueba que `POST /auth/login` conserva su respuesta observable, que el JWT se firma con HS256 e incluye los claims del contrato, que su expiración no excede 300 segundos, que una firma alterada falla y que una clave menor a 32 bytes se rechaza. Los resultados y pendientes reales están en [EVIDENCIA-AUTH.md](../EVIDENCIA-AUTH.md).
