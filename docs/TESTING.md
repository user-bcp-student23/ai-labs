# Pruebas de la API (`api/`)

Componente: `api` · IDs relacionados: H-API-05 (carga de archivos), H-API-12 (health), H-API-06 (pendiente)

## Cómo ejecutar

| Paso | Comando | Directorio |
|---|---|---|
| Suite completa con cobertura | `.\.venv\Scripts\python.exe -m pytest --cov --cov-report=term-missing` | `api/` |
| Solo pruebas de endpoints | `.\.venv\Scripts\python.exe -m pytest tests/test_endpoints.py` | `api/` |
| Pruebas H-API-05 sin `xfail` (evidencia de fallo) | `.\.venv\Scripts\python.exe -m pytest tests/test_endpoints.py --runxfail -k "upload"` | `api/` |

## Resultados ejecutados

| Ejecución | Comando | Código de salida | Resultado |
|---|---|---|---|
| Suite completa | Suite completa con cobertura | 0 | 61 passed, 4 xfailed |
| H-API-05 sin `xfail` | `--runxfail -k upload` | 1 | 3 failed (esperado: la validación aún no existe) |

Los 4 `xfailed` son: 3 de H-API-05 y 1 brecha de validación de `title` (ver Pendientes).

## Cobertura

Método: `pytest-cov` con `branch=true` y `source=["app"]` (`api/pyproject.toml`). Comando: `--cov --cov-report=term-missing`.

| Alcance | Numerador (cubierto) | Denominador | Resultado |
|---|---|---|---|
| Código de `app/` (sentencias) | 276 | 278 | 99% |
| Ramas de `app/` | 20 ramas, 0 parciales | 20 | 100% de ramas |
| Líneas sin cubrir | `app/security.py:68-69` | | |

Cobertura global: la medición se hace solo sobre `app/` (única fuente configurada), por lo que la global y la del código de la API son la misma cifra: 99%. No se midió por separado el "código modificado" en esta ejecución; el resultado cubre todo `app/`, que incluye los cambios.

## Tabla de casos por endpoint

Convención de tipo: **feliz** (dato válido), **borde** (payload vacío, archivo sin extensión, límite), **error** (respuesta de error documentada). Detalles de contrato en `docs/ENDPOINTS.md`.

| Endpoint | Caso | Tipo | Resultado esperado | Prueba (`api/tests/test_endpoints.py`) | Estado |
|---|---|---|---|---|---|
| Todos (5) | Sin token | error | 401 `Invalid token` | `test_every_endpoint_rejects_missing_token` (parametrizada) | pasa |
| Todos (5) | Token expirado | error | 401 `Invalid token` | `test_every_endpoint_rejects_expired_token` (parametrizada) | pasa |
| GET /api/tasks | Lista propia con campos del contrato | feliz | 200, solo tareas del owner | `test_get_tasks_returns_only_own_tasks_with_contract_fields` | pasa |
| GET /api/tasks | `owner` vacío usa la identidad del token | borde | 200, tareas del token | `test_get_tasks_with_empty_owner_uses_token_identity` | pasa |
| GET /api/tasks | Usuario sin tareas | borde | 200, lista vacía | `test_get_tasks_returns_empty_list_for_user_without_tasks` | pasa |
| GET /api/tasks | Token sin prefijo `Bearer ` | borde | 200 (el prefijo es opcional) | `test_get_tasks_accepts_token_without_bearer_prefix` | pasa |
| GET /api/tasks | Leer tareas de otro owner (IDOR, ambas direcciones) | error | 403 `Forbidden` | `test_get_tasks_forbids_reading_another_owner` (parametrizada) | pasa |
| POST /api/tasks | Creación válida | feliz | 201 con campos de `TaskOut` | `test_post_task_returns_201_with_contract_fields` | pasa |
| POST /api/tasks | Payload `{}` | borde | 422 y no inserta nada | `test_post_task_with_empty_payload_returns_422_and_inserts_nothing` | **xfail (brecha)** |
| POST /api/tasks | Cuerpo no objeto (`[1]`) | error | 422 | `test_post_task_with_non_object_body_returns_422` | pasa |
| POST /api/tasks | `owner` ajeno | error | 403 `Forbidden` y no inserta | `test_post_task_rejects_foreign_owner_and_inserts_nothing` | pasa |
| GET /api/summary | Resumen con campos del contrato | feliz | 200 | `test_summary_returns_contract_fields` | pasa |
| GET /api/summary | Usuario sin tareas | borde | 200, resumen vacío | `test_summary_for_user_without_tasks_is_empty` | pasa |
| GET /api/summary | `owner` ajeno | error | 403 `Forbidden` | `test_summary_rejects_foreign_owner` | pasa |
| POST /api/requirements | Archivo válido (`req.txt`, `spec.pdf`) | feliz | 201 con campos del contrato | `test_upload_stores_file_and_returns_contract_fields` (parametrizada) | pasa |
| POST /api/requirements | Archivo vacío | borde | 201, tamaño 0 | `test_upload_empty_file_is_stored_with_size_zero` | pasa |
| POST /api/requirements | Sin campo `file` | error | 422 | `test_upload_without_file_returns_422` | pasa |
| POST /api/requirements | Sin extensión (`README`) | borde | 4xx (H-API-05) | `test_upload_without_extension_is_rejected` | **xfail H-API-05** |
| POST /api/requirements | Extensión no permitida (`.exe`) | borde | 4xx (H-API-05) | `test_upload_disallowed_extension_is_rejected` | **xfail H-API-05** |
| POST /api/requirements | Path traversal (`../escape.txt`) | borde | No escribe fuera del directorio (H-API-05) | `test_upload_path_traversal_does_not_leave_upload_dir` | **xfail H-API-05** |
| GET /api/backend-health | Backend responde | feliz | 200 con estado y cuerpo del backend | `test_health_reports_backend_status_and_body` | pasa |
| GET /api/backend-health | Backend responde error HTTP | error | Pasa el código de estado del backend | `test_health_passes_through_backend_error_status` | pasa |
| GET /api/backend-health | Backend inaccesible | error | 200, `status: 0`, cuerpo `Auth backend unavailable` | `test_health_reports_unavailable_backend_without_http_error` | pasa |

Las pruebas previas (`tests/test_api.py`, `tests/test_hardening.py`, `tests/test_security.py`) también forman parte de la suite de 61 pasadas.

## Fallos y brechas (no ocultos)

1. **Brecha de validación de `title` en `POST /api/tasks`** (no es H-API-05). `TaskCreate.title` tiene valor por defecto `""` (`api/app/schemas.py:19`), así que `{}` responde `201`. La prueba espera `422` y está marcada `xfail(strict=True)` para no ocultar el hallazgo ni ajustarla al comportamiento actual. `docs/ENDPOINTS.md` se corrigió: ya no afirma que `title` sea obligatorio. Decisión pendiente: ¿`title` debe ser obligatorio y no vacío?
2. **H-API-05** (`api/app/routes/requirements.py:19`): sin validación de extensión, sin límite de tamaño y sin normalización del nombre. Las 3 pruebas fallan con `--runxfail`:
   - sin extensión: responde `201` (se esperaba 4xx);
   - `.exe`: responde `201` (se esperaba 4xx);
   - path traversal: `escape.txt` se escribe fuera del directorio de subida.
   H-API-05 permanece en **Pendiente**.

## Pendientes y pruebas propuestas (no ejecutadas)

- **H-API-05, límite de tamaño de subida**: no hay decisión del usuario; no existe prueba.
- **H-API-12, límite del cuerpo de health**: propuesto 200 bytes, pendiente de aprobación; no existe prueba.
- **H-API-06**: su acción sigue pendiente de decisión; no hay evidencia en el repositorio.
- **Emisor del token (`auth/`)**: no verificado en esta ejecución; no hay prueba.
- **Brecha de `title`**: prueba `xfail` ya escrita; falta decisión.
- Cuando se corrija H-API-05, las 3 pruebas pasarán a `XPASS`, lo que falla con `strict=True`; ese fallo indica que hay que quitar el marcador `xfail`.
- Advertencia no relacionada: `app/main.py:48` usa `on_event` (deprecado). No se corrige aquí.

## Documentos consultados

`README.md`, `RETO.md`, `docs/GOOD_PRACTICES.md`, `docs/ENDPOINTS.md`, `HALLAZGOS.md`, `PLAN.md`, `api/pyproject.toml`, `api/app/schemas.py`, `api/app/routes/requirements.py`, `api/app/routes/health.py`, y los tests de `api/tests/`.
