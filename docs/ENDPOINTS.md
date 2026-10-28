# Contrato de API — componente `api`

## Estado del contrato

- **Contrato observado:** derivado del código actual de `api/` y de comprobaciones locales con `TestClient`; las rutas y formatos exitosos existentes se conservaron en las pruebas.
- **Contrato acordado:** el usuario confirmó JWT HS256 con `iss=ISS`, `aud=CLAIM`, `exp` y username/role requeridos, clave de entorno `SECRET`; la API responde 403 ante owner distinto; cargas `.txt` y `.pdf` hasta 4 bytes responden 201 y colisiones reciben nombre único; extensión inválida responde 415 y tamaño excedido 413, ambos con `{"detail":"Invalid upload"}`.
- **Riesgos y preguntas pendientes:** el servidor de autenticación centralizado emite JWT conforme al contrato local; falta validar la integración real con TrackingProcessor v1.0 y provisionar `SECRET` en ambos servicios. Los valores de `AUTH_HEALTH_URL` y `WORKSHOP_UPLOAD_DIR` pueden cambiar según el entorno.
- **H-API-03:** los valores SQL dinamicos de filtros, inserciones y lectura por ID se enlazan como parametros SQLite; hallazgo Resuelto.

## Autenticación compartida

Las cinco rutas documentadas requieren el header:

```http
Authorization: Bearer <token>
```

El API no expone una ruta para emitir tokens. Valida la firma HS256, `iss=ISS`, `aud=CLAIM`, `exp`, `username` y `role`; la clave de verificación se lee de la variable de entorno `SECRET` y debe tener al menos 32 bytes. Los ejemplos usan `$API_TOKEN` como variable del cliente: debe contener un JWT compatible obtenido por el mecanismo configurado fuera de esta API. **Pendiente:** validar la integración real con TrackingProcessor v1.0.

El servidor centralizado de autenticación emite los tokens mediante `POST /auth/login`. El contrato de emisión para TrackingProcessor v1.0 está en [`auth/contracts/tracking-processor-v1.yaml`](../auth/contracts/tracking-processor-v1.yaml); esta API no incluye una muestra de token ni valores de credenciales.

Si falta el header o el token no se valida, las rutas responden HTTP 401. Ejemplo comprobado sin header:

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{"detail":"Invalid token"}
```

Para tokens malformados, expirados, con firma o claims incorrectos, se responde con el mismo detalle genérico.

---

## GET `/api/tasks`

### 1. Qué hace

Devuelve las tareas asociadas a la identidad solicitada por medio del parámetro `owner`; si se omite o está vacío, usa el username del JWT validado.

### 2. Autenticación

Requerida: `Authorization: Bearer <token>`.

### 3. Request

| campo/parámetro | tipo | obligatorio | descripción |
|---|---|---:|---|
| `owner` (query) | string | No | Owner cuyas tareas se consultan. Si se omite o está vacío, se usa el `username` del JWT validado; si no coincide con esa identidad, responde 403. |

Ejemplo completo (requiere que `API_TOKEN` ya contenga un token válido):

```bash
curl -H "Authorization: Bearer $API_TOKEN" \
  "http://localhost:8000/api/tasks?owner=student"
```

### 4. Response exitosa

HTTP **200**. El cuerpo es una lista de tareas; puede ser `[]` si no hay filas para ese owner.

| campo | tipo | descripción |
|---|---|---|
| `id` | integer | Identificador SQLite de la tarea. |
| `title` | string | Título. |
| `description` | string | Descripción. |
| `status` | string | Estado almacenado. |
| `owner` | string | Owner de la fila. |
| `priority` | string | Prioridad almacenada. |
| `createdAt` | string | Valor SQLite de `created_at`. |

Ejemplo obtenido con la base SQLite temporal inicializada por `create_app`:

```json
[
  {
    "id": 1,
    "title": "Refactor login",
    "description": "Separar responsabilidades en frontend",
    "status": "TODO",
    "owner": "student",
    "priority": "HIGH",
    "createdAt": "2026-10-26 22:02:21"
  },
  {
    "id": 2,
    "title": "Review API",
    "description": "Revisar seguridad de endpoints",
    "status": "IN_PROGRESS",
    "owner": "student",
    "priority": "MEDIUM",
    "createdAt": "2026-10-26 22:02:21"
  }
]
```

Los timestamps y los IDs dependen de la base; los del ejemplo corresponden a una base nueva de la comprobación local.

### 5. Respuestas de error

| código | cuándo ocurre | ejemplo de cuerpo |
|---|---|---|
| 401 | Header ausente o JWT inválido/expirado. | `{"detail":"Invalid token"}` |
| 403 | Se envía `owner` distinto del username del JWT. | `{"detail":"Owner does not match authenticated identity"}` |
| 500 | `SECRET` falta o es demasiado corto, o ocurre un error no controlado al consultar SQLite. | `Internal Server Error` (texto plano, respuesta predeterminada observada de Starlette). |

No hay validación adicional del query `owner`; el parámetro se tipa como string.

### 6. Notas de seguridad

La respuesta se limita al username del JWT validado; un owner distinto recibe 403. El owner se enlaza como parametro SQLite, no se concatena al SQL.

**Evidencia de implementación:** `api/app/main.py:65-77`; `api/app/services/task_service.py:8-11`.

---

## POST `/api/tasks`

### 1. Qué hace

Crea una tarea y devuelve la fila insertada.

### 2. Autenticación

Requerida: `Authorization: Bearer <token>`.

### 3. Request

El body debe ser un objeto JSON. La ruta lee los siguientes campos; todos son opcionales en el código. Sus valores se convierten con `str()` y los campos adicionales no se usan.

| campo/parámetro | tipo | obligatorio | descripción |
|---|---|---:|---|
| `title` (body) | cualquier valor JSON | No | Convertido a string; predeterminado `""`. |
| `description` (body) | cualquier valor JSON | No | Convertido a string; predeterminado `""`. |
| `status` (body) | cualquier valor JSON | No | Convertido a string; predeterminado `"TODO"`. |
| `priority` (body) | cualquier valor JSON | No | Convertido a string; predeterminado `"MEDIUM"`. |
| `owner` (body) | cualquier valor JSON | No | Si se omite, se usa el username del JWT validado. Si se proporciona, se convierte a string y debe coincidir; de otro modo responde 403. |

Ejemplo completo:

```http
POST /api/tasks HTTP/1.1
Host: localhost:8000
Authorization: Bearer $API_TOKEN
Content-Type: application/json

{
  "title": "Example",
  "description": "Example body",
  "status": "TODO",
  "priority": "HIGH"
}
```

### 4. Response exitosa

HTTP **201**.

| campo | tipo | descripción |
|---|---|---|
| `id` | integer | Identificador SQLite de la tarea. |
| `title` | string | Título convertido a string. |
| `description` | string | Descripción convertida a string. |
| `status` | string | Estado convertido a string. |
| `owner` | string | Owner convertido a string. |
| `priority` | string | Prioridad convertida a string. |
| `createdAt` | string | Valor SQLite de `created_at`. |

Ejemplo comprobado en una base temporal nueva:

```json
{
  "id": 4,
  "title": "Example",
  "description": "Example body",
  "status": "TODO",
  "owner": "student",
  "priority": "HIGH",
  "createdAt": "2026-10-26 22:02:22"
}
```

El ID y el timestamp dependen de la base y del momento de creación.

### 5. Respuestas de error

| código | cuándo ocurre | ejemplo de cuerpo |
|---|---|---|
| 401 | Header ausente o JWT inválido/expirado. | `{"detail":"Invalid token"}` |
| 422 | Body ausente, JSON no válido o raíz que no sea un objeto JSON. Ejemplos comprobados: body ausente `{"detail":[{"type":"missing","loc":["body"],"msg":"Field required","input":null}]}`; raíz array `{"detail":[{"type":"model_attributes_type","loc":["body"],"msg":"Input should be a valid dictionary or object to extract fields from","input":[]}]}`. |
| 403 | El campo `owner`, si se proporciona, no coincide con el username del JWT. | `{"detail":"Owner does not match authenticated identity"}` |
| 500 | `SECRET` falta o es demasiado corto, o ocurre un error no controlado al insertar, confirmar o leer SQLite. | `Internal Server Error` (texto plano, respuesta predeterminada observada de Starlette). |

### 6. Notas de seguridad

El owner se toma de la identidad validada; si se proporciona un owner distinto se responde 403. El body usa `TaskCreateRequest` y conserva la conversión observada a string y los defaults. Los campos del insert y la lectura de la fila creada se envian mediante parametros SQLite (H-API-03, Resuelto).

**Evidencia de implementación:** `api/app/main.py:78-104`; `api/app/schemas.py:18-24`; `api/app/services/task_service.py:8-11`.

---

## GET `/api/summary`

### 1. Qué hace

Resume el número de tareas, el recuento por estado y las tareas de prioridad alta que siguen abiertas para un owner.

### 2. Autenticación

Requerida: `Authorization: Bearer <token>`.

### 3. Request

| campo/parámetro | tipo | obligatorio | descripción |
|---|---|---:|---|
| `owner` (query) | string | No | Owner que se resume. Si se omite o está vacío, se usa el `username` del JWT validado; si no coincide con esa identidad, responde 403. |

Ejemplo completo:

```bash
curl -H "Authorization: Bearer $API_TOKEN" \
  "http://localhost:8000/api/summary?owner=student"
```

### 4. Response exitosa

HTTP **200**.

| campo | tipo | descripción |
|---|---|---|
| `owner` | string | Owner usado para el resumen. |
| `total` | integer | Número total de tareas consultadas. |
| `byStatus` | object de string a integer | Recuento por cada estado presente. |
| `highPriorityOpen` | integer | Tareas `HIGH` cuyo estado no es `DONE` ni `ARCHIVED`. |

Ejemplo comprobado con las filas semilla para `student`:

```json
{
  "owner": "student",
  "total": 2,
  "byStatus": {
    "TODO": 1,
    "IN_PROGRESS": 1
  },
  "highPriorityOpen": 1
}
```

### 5. Respuestas de error

| código | cuándo ocurre | ejemplo de cuerpo |
|---|---|---|
| 401 | Header ausente o JWT inválido/expirado. | `{"detail":"Invalid token"}` |
| 403 | Se envía `owner` distinto del username del JWT. | `{"detail":"Owner does not match authenticated identity"}` |
| 500 | `SECRET` falta o es demasiado corto, o ocurre un error no controlado al consultar SQLite o construir el resumen. | `Internal Server Error` (texto plano, respuesta predeterminada observada de Starlette). |

### 6. Notas de seguridad

La respuesta se limita al username del JWT validado; un owner distinto recibe 403. El owner del filtro se enlaza como parametro SQLite, no se concatena al SQL.

**Evidencia de implementación:** `api/app/main.py:106-128`; `api/app/services/task_service.py:8-11`.

---

## POST `/api/requirements`

### 1. Qué hace

Guarda un archivo de requisitos recibido como multipart y devuelve metadatos de la carga.

### 2. Autenticación

Requerida: `Authorization: Bearer <token>`.

### 3. Request

| campo/parámetro | tipo | obligatorio | descripción |
|---|---|---:|---|
| `file` (multipart) | archivo (`UploadFile`) | Sí | Nombre con extensión `.txt` o `.pdf` (sin distinción de mayúsculas) y hasta 4 bytes. Se guarda bajo el directorio configurado por `WORKSHOP_UPLOAD_DIR`, predeterminado `./uploads`. |

Ejemplo completo con un archivo local de exactamente 4 bytes:

```bash
printf 'Test' > ./sample.txt
curl -X POST "http://localhost:8000/api/requirements" \
  -H "Authorization: Bearer $API_TOKEN" \
  -F "file=@./sample.txt;type=text/plain"
```

### 4. Response exitosa

HTTP **201**.

| campo | tipo | descripción |
|---|---|---|
| `owner` | string | Username del JWT validado. |
| `fileName` | string | Nombre normalizado asignado al archivo guardado; puede llevar sufijo numérico si ya existe. |
| `storedAt` | string | Ruta absoluta resultante del archivo guardado. Depende de la configuración y del sistema operativo. |
| `size` | integer | Número de bytes guardados (máximo 4). |

Ejemplo de respuesta para el contenido de 4 bytes `Test` en `sample.txt`, con `WORKSHOP_UPLOAD_DIR=C:\workshop\uploads` en Windows:

```json
{
  "owner": "student",
  "fileName": "sample.txt",
  "storedAt": "C:\\workshop\\uploads\\sample.txt",
  "size": 4
}
```

La transformación de respuesta y el tamaño se comprobaron localmente; `storedAt` depende del directorio y plataforma indicados.

### 5. Respuestas de error

| código | cuándo ocurre | ejemplo de cuerpo |
|---|---|---|
| 401 | Header ausente o JWT inválido/expirado. | `{"detail":"Invalid token"}` |
| 422 | Falta el campo multipart requerido `file`. Ejemplo comprobado: | `{"detail":[{"type":"missing","loc":["body","file"],"msg":"Field required","input":null}]}` |
| 413 | El archivo excede 4 bytes. | `{"detail":"Invalid upload"}` |
| 415 | La extensión no es `.txt` ni `.pdf`, o el nombre no es válido. | `{"detail":"Invalid upload"}` |
| 500 | `SECRET` falta o es demasiado corto, o ocurre un error no controlado al leer o escribir el archivo. | `Internal Server Error` (texto plano, respuesta predeterminada observada de Starlette). |

### 6. Notas de seguridad

El nombre recibido se normaliza a un nombre base y el destino se verifica dentro del directorio de carga. La lectura de la ruta de aplicación se limita a 5 bytes para detectar el límite de 4; el archivo no se escribe si se excede. Las colisiones generan un nombre único mediante creación exclusiva. La respuesta `storedAt` expone la ruta del archivo guardado. No se verificó un límite de tamaño del cuerpo multipart impuesto por middleware externo.

**Evidencia de implementación:** `api/app/main.py:129-139`; `api/app/services/upload_service.py:7-54`.

---

## GET `/api/backend-health`

### 1. Qué hace

Consulta el endpoint de health del backend de autenticación configurado y devuelve el status HTTP y el body recibido.

### 2. Autenticación

Requerida: `Authorization: Bearer <token>`.

### 3. Request

| campo/parámetro | tipo | obligatorio | descripción |
|---|---|---:|---|
| Query y body | ninguno | No aplica | No recibe parámetros de query ni body; solo requiere el header de autenticación indicado. |

Ejemplo completo:

```bash
curl -H "Authorization: Bearer $API_TOKEN" \
  "http://localhost:8000/api/backend-health"
```

La URL de destino se toma de `AUTH_HEALTH_URL`; si no está definida, usa `http://localhost:8080/q/health`.

### 4. Response exitosa

HTTP **200** para cualquier respuesta HTTP recibida del destino, incluso cuando ese destino devuelve un status no exitoso.

| campo | tipo | descripción |
|---|---|---|
| `requestedBy` | string | Username del JWT validado. |
| `status` | integer | Status HTTP del destino; `0` si la llamada produce un error HTTP de urllib3. |
| `body` | string | Body del destino decodificado como UTF-8, reemplazando bytes no válidos; ante un error HTTP de urllib3, `Health check unavailable`. |

Ejemplo comprobado con un mock local que devuelve HTTP 200 y `{"status":"UP"}`:

```json
{
  "requestedBy": "student",
  "status": 200,
  "body": "{\"status\":\"UP\"}"
}
```

Si el destino responde HTTP 503 con body `unavailable`, la API comprobada responde HTTP 200:

```json
{
  "requestedBy": "student",
  "status": 503,
  "body": "unavailable"
}
```

### 5. Respuestas de error

| código | cuándo ocurre | ejemplo de cuerpo |
|---|---|---|
| 401 | Header ausente o JWT inválido/expirado. | `{"detail":"Invalid token"}` |
| 500 | `SECRET` falta o es demasiado corto, o ocurre un error no controlado fuera del manejo de errores HTTP de urllib3. | `Internal Server Error` (texto plano, respuesta predeterminada de Starlette). |

Los errores HTTP de urllib3 dentro de la llamada no producen un status HTTP de error de la API: se registran y se devuelven como HTTP 200 con `status: 0` y un cuerpo generico. El ejemplo observado es:

```json
{
  "requestedBy": "student",
  "status": 0,
  "body": "Health check unavailable"
}
```

### 6. Notas de seguridad

La URL puede ser configurada mediante `AUTH_HEALTH_URL`; el body recibido del servicio se devuelve sin filtrado. Los errores HTTP de urllib3 se registran en el servidor y se responden con texto generico, sin exponer el detalle de la excepcion. El timeout de la peticion saliente es 3 segundos.

**Evidencia de implementación:** `api/app/main.py:142-158`; `api/app/schemas.py:47-52`.

---

## Preguntas abiertas

1. Falta validar la integración con TrackingProcessor v1.0 y coordinar el aprovisionamiento de `SECRET` para auth y api. La API no emite tokens y esta página no incluye un token real.
