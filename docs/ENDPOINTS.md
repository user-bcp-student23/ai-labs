# Contrato de la API (`api/`)

Documento de integración para la API FastAPI de tareas y requerimientos. Describe el comportamiento observado en el código de `api/app/` y las respuestas reales capturadas con `TestClient` (ver [Evidencia de captura](#evidencia-de-captura)).

Tres categorías, separadas a propósito:

- **Contrato observado:** lo que hace el código hoy. Es lo que este documento describe.
- **Contrato acordado:** decisiones aprobadas en `PLAN.md` (sección "Aprobaciones registradas" y "Decisiones recibidas").
- **Riesgos pendientes:** lo que aún no está corregido. Se remite a `HALLAZGOS.md`.

## Base y autenticación común

- Prefijo de rutas: `/api` (`api/app/routes/__init__.py`).
- Todas las rutas requieren el header `Authorization` con un token firmado. El prefijo `Bearer ` es opcional (`api/app/dependencies.py:12`, `authorization.removeprefix(TOKEN_PREFIX)`). Ejemplo: `Authorization: Bearer <token>`.
- Formato del token: `base64url(payload).base64url(HMAC-SHA256(payload))`, firmado con la variable de entorno `WORKSHOP_TOKEN_SECRET` (`api/app/security.py:24`, `:31`, `:36`).
- Claims obligatorios: `sub` (usuario), `role`, `exp` (entero, expiración en segundos Unix), `iss` = `ai-labs-auth`, `aud` = `ai-labs-api` (`api/app/constants.py`). Tolerancia de reloj: 0 segundos.
- Si el token falta, es inválido o está expirado: `401` con `{"detail": "Invalid token"}` (`api/app/dependencies.py:16`).
- La identidad sale solo del token (`identity.username`). No hay parámetro de autenticación separado.

Error común de autenticación (aplica a todos los endpoints):

```json
{"detail": "Invalid token"}
```

Error de validación de FastAPI (aplica donde hay cuerpo o formulario): `422` con una lista `detail` (formato por defecto de FastAPI, ver cada endpoint).

---

## 1. `GET /api/tasks`

**Qué hace:** devuelve las tareas del usuario autenticado (`api/app/routes/tasks.py:13`).

**Autenticación:** sí. Header `Authorization: Bearer <token>`.

### Request

Query string:

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `owner` | string | No | Usuario cuyas tareas se piden. Si se omite o va vacío, se usa `identity.username`. Si es distinto del usuario del token, responde `403` (`api/app/services.py:11-13`). |

Ejemplo:

```http
GET /api/tasks HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

### Response exitosa

Código: `200 OK`. Cuerpo: arreglo de `TaskOut` (`api/app/schemas.py`).

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | integer | Identificador de la tarea. |
| `title` | string | Título. |
| `description` | string | Descripción. Vacío si no se envió. |
| `status` | string | Estado, por ejemplo `TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`. |
| `owner` | string | Usuario dueño de la tarea. |
| `priority` | string | Prioridad, por ejemplo `LOW`, `MEDIUM`, `HIGH`. |
| `createdAt` | string | Fecha de creación en formato `YYYY-MM-DD HH:MM:SS`. Viene del campo `created_at`. |

Ejemplo real (capturado en la ejecución de documentación; `createdAt` depende del momento de la carga):

```json
[
  {
    "id": 1,
    "title": "Refactor login",
    "description": "Separar responsabilidades en frontend",
    "status": "TODO",
    "owner": "student",
    "priority": "HIGH",
    "createdAt": "2026-11-02 22:12:22"
  },
  {
    "id": 2,
    "title": "Review API",
    "description": "Revisar seguridad de endpoints",
    "status": "IN_PROGRESS",
    "owner": "student",
    "priority": "MEDIUM",
    "createdAt": "2026-11-02 22:12:22"
  }
]
```

### Respuestas de error

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| `401` | Falta el token, es inválido o expiró. | `{"detail": "Invalid token"}` |
| `403` | `owner` pide tareas de otro usuario. | `{"detail": "Forbidden"}` |

Ejemplo `403`:

```json
{"detail": "Forbidden"}
```

### Notas de seguridad

- El filtro por dueño usa la identidad del token. Un `owner` ajeno se rechaza con `403`; no devuelve datos del otro usuario.
- El parámetro `owner` todavía se acepta desde el cliente. `docs/GOOD_PRACTICES.md` indica que el dueño no debería ser un parámetro del cliente. Esto queda como riesgo pendiente en `HALLAZGOS.md`.
- Las consultas son parametrizadas (ver `api/app/repository.py:15`).

---

## 2. `POST /api/tasks`

**Qué hace:** crea una tarea para el usuario autenticado (`api/app/routes/tasks.py:23`).

**Autenticación:** sí. Header `Authorization: Bearer <token>`.

### Request

Cuerpo JSON (`TaskCreate`):

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `title` | string | No | Título de la tarea. Por defecto `""`; el código no lo exige (`api/app/schemas.py:19`). |
| `description` | string | No | Descripción. Por defecto `""`. |
| `status` | string | No | Estado inicial. Por defecto `TODO`. |
| `priority` | string | No | Prioridad. Por defecto `MEDIUM`. |
| `owner` | string | No | Dueño. Por defecto `""`, que se resuelve al usuario del token. Si es distinto del usuario, responde `403`. |

Valores no string en los campos de texto se convierten a string (`api/app/schemas.py:11`, `_as_text`).

Ejemplo:

```json
{
  "title": "Demo",
  "description": "d",
  "status": "TODO",
  "priority": "HIGH"
}
```

### Response exitosa

Código: `201 Created`. Cuerpo: un `TaskOut` (mismos campos que en `GET /api/tasks`).

Ejemplo real:

```json
{
  "id": 4,
  "title": "Demo",
  "description": "d",
  "status": "TODO",
  "owner": "student",
  "priority": "HIGH",
  "createdAt": "2026-11-02 22:12:22"
}
```

Ejemplo con valores por defecto (solo `title`):

```json
{
  "id": 5,
  "title": "Solo titulo",
  "description": "",
  "status": "TODO",
  "owner": "student",
  "priority": "MEDIUM",
  "createdAt": "2026-11-02 22:12:22"
}
```

### Respuestas de error

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| `401` | Falta el token, es inválido o expiró. | `{"detail": "Invalid token"}` |
| `403` | El campo `owner` es distinto del usuario del token. | `{"detail": "Forbidden"}` |
| `422` | El cuerpo no es un objeto JSON válido (por ejemplo, una lista). | Lista `detail` de FastAPI (ver abajo). |

Ejemplo `422` con cuerpo que es una lista (`[1]`):

```json
{
  "detail": [
    {
      "type": "model_attributes_type",
      "loc": ["body"],
      "msg": "Input should be a valid dictionary or object to extract fields from",
      "input": [1]
    }
  ]
}
```

Ausencia de `title`: **no produce 422**. El payload `{}` se acepta con `201` porque `title` tiene default `""` (`api/app/schemas.py:19`). Se registra como brecha de validación pendiente (ver `docs/TESTING.md`).

### Notas de seguridad

- Un `owner` ajeno se rechaza con `403` antes de insertar (`api/app/services.py:11-13`).
- Los valores se insertan con SQL parametrizado (`api/app/repository.py:21`).
- Los campos `status` y `priority` aceptan cualquier string. No hay lista cerrada validada en el código observado. Pregunta abierta.

---

## 3. `GET /api/summary`

**Qué hace:** devuelve un resumen de las tareas del usuario: total, conteo por estado y número de tareas de prioridad alta abiertas (`api/app/routes/tasks.py:34`).

**Autenticación:** sí. Header `Authorization: Bearer <token>`.

### Request

Query string:

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `owner` | string | No | Igual que en `GET /api/tasks`. Si es ajeno, responde `403`. |

Ejemplo:

```http
GET /api/summary HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

### Response exitosa

Código: `200 OK`. Cuerpo: `SummaryOut`.

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Usuario del resumen. |
| `total` | integer | Número total de tareas del usuario. |
| `byStatus` | object (string → integer) | Conteo por estado. |
| `highPriorityOpen` | integer | Tareas con prioridad `HIGH` cuyo estado no es `DONE` ni `ARCHIVED` (`api/app/services.py:25`). |

Ejemplo real:

```json
{
  "owner": "student",
  "total": 4,
  "byStatus": {
    "TODO": 3,
    "IN_PROGRESS": 1
  },
  "highPriorityOpen": 2
}
```

### Respuestas de error

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| `401` | Falta el token, es inválido o expiró. | `{"detail": "Invalid token"}` |
| `403` | `owner` pide el resumen de otro usuario. | `{"detail": "Forbidden"}` |

### Notas de seguridad

- Mismas notas que en `GET /api/tasks`: la identidad sale del token y el `owner` ajeno se rechaza.
- El cálculo de `highPriorityOpen` se hace en `api/app/services.py`, no en SQL. Si cambia la lista de estados cerrados, cambia este valor.

---

## 4. `POST /api/requirements`

**Qué hace:** recibe un archivo de requerimientos por formulario multipart y lo guarda en el directorio de carga (`api/app/routes/requirements.py:13`).

**Autenticación:** sí. Header `Authorization: Bearer <token>`.

### Request

Formulario `multipart/form-data`:

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `file` | archivo | Sí | Archivo a guardar. Se guarda con `file.filename` tal como llega (`api/app/routes/requirements.py:19`). |

Ejemplo (curl):

```bash
curl -X POST http://localhost:8000/api/requirements \
  -H "Authorization: Bearer <token>" \
  -F "file=@req.txt;type=text/plain"
```

### Response exitosa

Código: `201 Created`. Cuerpo: `UploadOut`.

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Usuario autenticado que subió el archivo. |
| `fileName` | string | Nombre del archivo recibido. Puede ser `null` según el esquema; pregunta abierta. |
| `storedAt` | string | Ruta completa donde se guardó. Depende del sistema operativo y del directorio configurado. |
| `size` | integer | Tamaño en bytes del contenido leído. |

Ejemplo real (ruta de ejemplo en Windows; en otros sistemas cambia):

```json
{
  "owner": "student",
  "fileName": "req.txt",
  "storedAt": "C:\\Users\\Usuario\\AppData\\Local\\Temp\\ep_docs\\up\\req.txt",
  "size": 3
}
```

### Respuestas de error

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| `401` | Falta el token, es inválido o expiró. | `{"detail": "Invalid token"}` |
| `422` | No se envió el campo `file`. | Lista `detail` de FastAPI (ver abajo). |

Ejemplo `422`:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "file"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

### Notas de seguridad

- **Riesgo pendiente (H-API-05):** el nombre del archivo se usa tal cual para construir la ruta (`Path(upload_dir) / str(file.filename)`, `api/app/routes/requirements.py:19`). No hay normalización de ruta, lista de extensiones ni límite de tamaño en el código observado. Un nombre con `..` o una ruta absoluta puede escapar del directorio de carga.
- Decisiones aprobadas para H-API-05 (contrato acordado, aún no implementado en el código observado): extensiones permitidas `.pdf`, `.docx`, `.txt`. El tamaño máximo está **pendiente** de decisión.
- El `storedAt` expone la ruta del servidor en la respuesta. Pregunta abierta: si el cliente debe verla.

---

## 5. `GET /api/backend-health`

**Qué hace:** consulta el endpoint de salud del backend de autenticación (`AUTH_HEALTH_URL`, por defecto `http://localhost:8080/q/health`) y devuelve su estado (`api/app/routes/health.py:22`).

**Autenticación:** sí. Header `Authorization: Bearer <token>`.

### Request

Sin parámetros ni cuerpo.

```http
GET /api/backend-health HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

### Response exitosa

Código: `200 OK`. Cuerpo: `HealthOut`.

| Campo | Tipo | Descripción |
|---|---|---|
| `requestedBy` | string | Usuario que hizo la consulta. |
| `status` | integer | Código de estado devuelto por el backend. `0` si no hubo respuesta. |
| `body` | string | Cuerpo devuelto por el backend. Si falla, `"Auth backend unavailable"`. |

Ejemplo real (backend inaccesible, caso capturado):

```json
{
  "requestedBy": "student",
  "status": 0,
  "body": "Auth backend unavailable"
}
```

Ejemplo de respuesta con backend disponible: no capturado en esta ejecución. Pregunta abierta: el cuerpo devuelto no está acotado (H-API-12 pendiente).

### Respuestas de error

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| `401` | Falta el token, es inválido o expiró. | `{"detail": "Invalid token"}` |

Cuando el backend no responde, el endpoint **no** devuelve error HTTP. Devuelve `200` con `status: 0` y `body: "Auth backend unavailable"`, y registra la excepción en el log.

### Notas de seguridad

- **Riesgo pendiente (H-API-12):** el cuerpo remoto se devuelve completo, sin límite de caracteres. Límite propuesto: 200, pendiente de confirmación.
- La URL viene de la variable de entorno `AUTH_HEALTH_URL`. Pendiente: validar que sea `http` o `https` (ver `PLAN.md`).
- El timeout es de 3 segundos (`HEALTH_TIMEOUT_SECONDS`, `api/app/routes/health.py:26`).

---

## Preguntas abiertas

1. Decisión pendiente: ¿`title` debe ser obligatorio y no vacío en `POST /api/tasks`? Hoy `{}` responde `201` (brecha de validación).
2. Si `file.filename` puede ser `None` en `POST /api/requirements` (el esquema lo permite, `fileName: string | null`).
3. Cuerpo del `GET /api/backend-health` cuando el backend sí responde (no capturado).
4. Tamaño máximo de archivo para `POST /api/requirements` (H-API-05, pendiente).
5. Límite de caracteres del cuerpo de salud (H-API-12, pendiente; propuesta 200).
6. Formato del emisor de tokens en `auth/` (`iss`/`aud`): pendiente de confirmación; `auth/` está fuera de alcance de este paso.
7. Si `status` y `priority` deben tener una lista cerrada de valores.

## Riesgos pendientes (resumen)

| ID | Tema | Estado |
|---|---|---|
| H-API-05 | Carga de archivos sin límite de tamaño ni normalización de nombre | Pendiente |
| H-API-06 | Acción sobre versiones de dependencias (registrar o consultar advisories) | Pendiente |
| H-API-12 | Cuerpo de salud sin límite | Pendiente |
| — | Parámetro `owner` todavía aceptado desde el cliente (ver `docs/GOOD_PRACTICES.md`) | Revisar en `HALLAZGOS.md` |

Estado de los hallazgos confirmados: ver `HALLAZGOS.md`. Este documento no cambia ningún estado.

## Evidencia de captura

Respuestas capturadas con `TestClient` contra `create_app(...)`, ejecutadas desde `api/` con el entorno virtual del componente. Base de datos y directorio de carga temporales, fuera del repositorio. `WORKSHOP_TOKEN_SECRET` de prueba. `AUTH_HEALTH_URL` apuntando a un puerto no disponible. Ningún secreto real.

| Caso | Código | Cuerpo |
|---|---|---|
| `GET /api/tasks` válido | 200 | Lista de `TaskOut` |
| `GET /api/tasks` sin token | 401 | `{"detail": "Invalid token"}` |
| `GET /api/tasks` con `owner` ajeno | 403 | `{"detail": "Forbidden"}` |
| `GET /api/tasks` con token expirado | 401 | `{"detail": "Invalid token"}` |
| `GET /api/tasks` sin prefijo `Bearer ` | 200 | Lista (el prefijo es opcional) |
| `POST /api/tasks` válido | 201 | `TaskOut` |
| `POST /api/tasks` solo `title` | 201 | `TaskOut` con defaults |
| `POST /api/tasks` con `owner` ajeno | 403 | `{"detail": "Forbidden"}` |
| `POST /api/tasks` cuerpo `[1]` | 422 | Lista `detail` |
| `POST /api/tasks` sin token | 401 | `{"detail": "Invalid token"}` |
| `GET /api/summary` | 200 | `SummaryOut` |
| `POST /api/requirements` válido | 201 | `UploadOut` |
| `POST /api/requirements` sin archivo | 422 | Lista `detail` |
| `GET /api/backend-health` backend caído | 200 | `HealthOut` con `status: 0` |

Hallazgo de la captura: un token sin el prefijo `Bearer ` se acepta. Esto coincide con `api/app/dependencies.py:12` y se documenta como comportamiento observado.

## Documentos consultados

- `README.md` (sección api)
- `RETO.md`
- `docs/GOOD_PRACTICES.md`
- `HALLAZGOS.md`
- `PLAN.md`
- Código de `api/app/`: `main.py`, `constants.py`, `dependencies.py`, `schemas.py`, `services.py`, `repository.py`, `security.py`, `database.py`, `routes/tasks.py`, `routes/requirements.py`, `routes/health.py`.

`docs/TESTING.md` no se creó en este paso; se creará en su paso de documentación.
