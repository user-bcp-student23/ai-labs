# Hallazgos

Matriz de seguimiento del componente `api` (Discovery). Ordenada de mayor a menor severidad. Estado inicial: `Pendiente`. Sin cambios de código; las evidencias son lectura estática de `api/app/main.py` y `api/requirements*.txt`.

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-API-01 | api | Filtro SQL concatenado en listado y resumen | Vulnerabilidad | El parámetro `owner` se une al texto SQL sin parametrizar. Un valor con comillas puede alterar la consulta y leer filas de otros dueños o romper la consulta. | api/app/main.py:70, api/app/main.py:93 | alta | Resuelto: consultas parametrizadas en `api/app/repository.py` (`?`), sin concatenar `owner`. Prueba de caracterización y de corrección en `api/tests/test_api.py`. |
| H-API-02 | api | Insert SQL concatenado con datos del cliente | Vulnerabilidad | `title`, `description`, `status`, `owner` y `priority` se concatenan en el `INSERT`. Un valor con comillas puede modificar la sentencia o insertar datos no previstos. | api/app/main.py:84, api/app/main.py:87 | alta | Resuelto: `TaskCreate` (Pydantic) en `api/app/schemas.py` y `INSERT` parametrizado en `api/app/repository.py`. La comilla se guarda como texto literal. |
| H-API-03 | api | Token Base64 con secreto embebido y sin firma | Vulnerabilidad | El token es Base64 con `\|` como separador y el secreto fijo `WORKSHOP_SECRET_2026`. Cualquiera que conozca el secreto puede fabricar un token válido. No hay firma, emisor ni audiencia. Sí se valida expiración (`parts[2]`). | api/app/main.py:14, api/app/main.py:20, api/app/main.py:22 | alta | Resuelto: firma HMAC-SHA256 con la biblioteca estándar en `api/app/security.py`, con `iss`, `aud`, `sub`, `role` y `exp` validados. El secreto sale de `WORKSHOP_TOKEN_SECRET` (sin valor por defecto; la app no arranca sin él). Tokens del formato anterior rechazados. Pendiente: confirmar que el emisor de `auth/` firma con el mismo formato. |
| H-API-04 | api | Autorización por `owner` enviado por el cliente | Vulnerabilidad | `owner` de la query (listado, resumen) o del body (creación) reemplaza la identidad del token. Un usuario autenticado puede consultar o crear tareas de otro dueño. | api/app/main.py:69, api/app/main.py:83, api/app/main.py:92 | alta | Resuelto: `resolve_owner` en `api/app/services.py` responde 403 si `owner` no coincide con la identidad. Listado, resumen y creación usan `identity["username"]`. |
| H-API-05 | api | Nombre de archivo subido usado sin normalizar ni limitar | Vulnerabilidad | `file.filename` se une directamente a la ruta de subida. Un nombre con `../` o absoluto puede escribir fuera de `uploads/`. No se validan extensión ni tamaño. | api/app/main.py:109, api/app/main.py:112 | alta | Pendiente |
| H-API-06 | api | Dependencias con posibles CVE: `urllib3 2.5.0` y `python-multipart 0.0.21` | Vulnerabilidad (SCA) | Versiones fijadas en el manifiesto. Falta verificar advisories y la versión corregida; no se comprobó en esta ejecución. | api/requirements.txt:4, api/requirements.txt:5 | media | Pendiente |
| H-API-07 | api | Secreto y CORS configurados en el código (adicional, no listado en RETO.md) | Vulnerabilidad | El secreto está fijo en el código y CORS permite cualquier origen con credenciales (`allow_origins=["*"]` junto con `allow_credentials=True`). Esta combinación debe revisarse. | api/app/main.py:14, api/app/main.py:50, api/app/main.py:51 | media | Resuelto: CORS usa un único origen desde `WORKSHOP_CORS_ORIGIN` (por defecto `http://localhost:4200`). Test: api/tests/test_hardening.py |
| H-API-08 | api | Respuestas de error exponen detalles internos | Vulnerabilidad | El detalle de error incluye `str(error)` en 401 y en la respuesta de salud. Puede revelar detalles de implementación. | api/app/main.py:26, api/app/main.py:120, api/app/main.py:121 | media | Resuelto: la salud devuelve `BACKEND_UNAVAILABLE_BODY` y registra el error en log (api/app/routes/health.py). Test: api/tests/test_hardening.py |
| H-API-09 | api | Todo el servicio en un solo `create_app` | Refactor | Rutas, conexión SQLite, reglas de resumen y serialización conviven en una función. Dificulta probar y cambiar cada capa por separado. | api/app/main.py:29, api/app/main.py:56, api/app/main.py:128 | media | Resuelto: separado en api/app/database.py, api/app/dependencies.py y api/app/routes/ (tasks, requirements, health). `create_app` solo ensambla. |
| H-API-10 | api | Tipos amplios y excepciones genéricas | Refactor | Se usa `dict[str, Any]` en cuerpos y respuestas, y `except Exception` en el token y en la salud del backend. Oculta errores concretos y reduce la validación. | api/app/main.py:25, api/app/main.py:78, api/app/main.py:108, api/app/main.py:120 | baja | Resuelto: modelos `Identity`, `UploadOut` y `HealthOut` en api/app/schemas.py con `response_model`; la salud captura `(urllib3.exceptions.HTTPError, OSError, ValueError)`. |
| H-API-11 | api | Condicionales anidados y SELECT duplicado | Refactor | Tres `if` anidados en el conteo de prioridad alta, y la lista de columnas se repite en dos consultas. | api/app/main.py:70, api/app/main.py:87, api/app/main.py:101, api/app/main.py:104 | baja | Resuelto: ya no existía en el código al ejecutar; el conteo usa `_is_open_high_priority` (api/app/services.py:25) y el SELECT es la constante `_SELECT_TASKS` (api/app/repository.py:7). Desviación: no hubo cambio nuevo. |
| H-API-12 | api | URL de salud configurable que devuelve el cuerpo remoto (adicional) | Sugerencia | La respuesta incluye el cuerpo de la URL configurada por `AUTH_HEALTH_URL`. Conviene limitar qué se devuelve y de dónde se consulta. | api/app/main.py:116, api/app/main.py:118, api/app/main.py:121 | baja | Pendiente |

## Notas de Discovery

- Recorrido de consulta: `Header Authorization` → `legacy_identity` (api/app/main.py:17-26) → ruta (`list_tasks` :67, `create_task` :77, `summary` :90) → SQL concatenado (api/app/main.py:70, :84, :93) → `connection.execute` de SQLite (api/app/main.py:35).
- Contrato observado en código, sin `docs/ENDPOINTS.md` (no existe; no se creó en este paso): `GET /api/tasks`, `POST /api/tasks`, `GET /api/summary`, `POST /api/requirements`, `GET /api/backend-health`.
- Todos los hallazgos de `RETO.md` para `api` aparecen en el código; ninguno quedó como `No encontrado`.
- No se ejecutaron pruebas ni consultas de advisories en esta ejecución. Pendiente: verificar CVE de H-API-06 y confirmar H-API-01/02 con pruebas locales.

## Componente web — Discovery

Hallazgos candidatos basados en la lectura estática de `web/`. No se modificó código. La suite no pudo ejecutarse porque no están disponibles las dependencias de Node (`vitest`).

### H-WEB-01 — Mensaje de login dinámico renderizado como HTML
- Estado: CANDIDATO
- Evidencia: `web/src/app/login/login.component.html:39` enlaza `message` con `[innerHTML]`; `web/src/app/login/login.component.ts:55-56` construye ese mensaje con el nombre ingresado y el mensaje de error devuelto por el backend. Angular sanitiza contenido enlazado a `innerHTML`; no se comprobó ejecución de contenido activo.
- Impacto: los datos de usuario y de la respuesta remota cruzan un límite de confianza y se interpretan como markup, con riesgo de presentación manipulada y dependencia de la sanitización del framework.
- Prioridad propuesta: Media.
- Contrato potencialmente afectado: presentación de errores del flujo `POST /auth/login`.
- Cómo validarlo: probar el componente con nombre y mensaje de error que contengan markup; verificar que se muestran como texto y no crean elementos activos, conservando el formato esperado del error.

### H-WEB-02 — Token de sesión accesible desde JavaScript en `localStorage`
- Estado: CANDIDATO
- Evidencia: `web/src/app/login/login.component.ts:47` guarda el token en `workshop_token`; `web/src/app/dashboard/dashboard.component.ts:36,43` lo lee y lo envía como `Authorization`.
- Impacto: cualquier script que llegue a ejecutarse en el mismo origen puede leer el bearer token y reutilizar la sesión hasta que deje de ser válido; el almacenamiento por sí solo no demuestra una vulnerabilidad explotable.
- Prioridad propuesta: Media.
- Contrato potencialmente afectado: sesión iniciada por `POST /auth/login` y autenticación de `GET /api/tasks`.
- Cómo validarlo: verificar en un navegador de prueba el almacenamiento, duración y eliminación del token al cerrar sesión; revisar la decisión de almacenamiento frente al modelo de amenaza del laboratorio y probar que solicitudes sin token siguen la respuesta de autenticación esperada.

### H-WEB-03 — JSON de usuario persistido se analiza fuera del manejo de errores
- Estado: CANDIDATO
- Evidencia: `web/src/app/dashboard/dashboard.component.ts:36-37` lee `workshop_token` y ejecuta `JSON.parse` sobre `workshop_user` antes del bloque `try` que comienza en la línea 42.
- Impacto: un valor persistido vacío, corrupto o incompatible puede lanzar una excepción durante `ngOnInit` e impedir que el dashboard cargue o redirija de forma controlada.
- Prioridad propuesta: Media.
- Contrato potencialmente afectado: restauración de sesión y navegación a `/dashboard` tras el login.
- Cómo validarlo: en un entorno local, guardar texto JSON inválido en `workshop_user`, navegar a `/dashboard` y comprobar que la aplicación responde con una recuperación o redirección controlada, sin excepción no gestionada.

### H-WEB-04 — URLs de servicios fijadas en los componentes
- Estado: Resuelto
- Evidencia: `web/src/app/login/login.component.ts:41-43` llama directamente a `http://localhost:8080/auth/login`; `web/src/app/dashboard/dashboard.component.ts:43` llama directamente a `http://localhost:8000/api/tasks`.
- Impacto: el frontend queda acoplado a puertos de localhost y los componentes combinan transporte con sesión y navegación, lo que dificulta cambiar el entorno y probar los flujos de forma aislada.
- Prioridad propuesta: Media.
- Contrato potencialmente afectado: conservación de `POST /auth/login` y `GET /api/tasks` al cambiar el host o entorno.
- Evidencia de resolución: `web/src/environments/environment.ts` define los orígenes locales; el build de producción genera configuración desde `AUTH_SERVICE_ORIGIN` y `API_SERVICE_ORIGIN`, y rechaza valores ausentes o que no sean orígenes HTTP(S). Los componentes usan los endpoints centralizados en `web/src/app/config/service-endpoints.ts`.
- Validación ejecutada: `npm run test:coverage` (13 pruebas pasaron; build script 87.75%, login 85.24%, dashboard 92.75%, endpoints 100%); build de desarrollo y build de producción con orígenes `.example.invalid` pasaron. El build de producción falló como se esperaba al faltar los orígenes.

### H-WEB-05 — Cobertura parcial de escenarios en login y dashboard
- Estado: CANDIDATO
- Evidencia: `web/src/app/login/login.component.spec.ts:34` cubre el login válido; `web/src/app/dashboard/dashboard.component.spec.ts:35,69,93` cubre carga, error y logout. No se cubren todos los bordes, como credenciales inválidas o falta de token.
- Impacto: algunos casos límite de autenticación y restauración de sesión todavía podrían cambiar sin que la suite los detecte.
- Prioridad propuesta: Baja.
- Contrato potencialmente afectado: flujos de login, dashboard y logout; endpoints `POST /auth/login` y `GET /api/tasks`.
- Cómo validarlo: agregar pruebas para los casos límite pendientes y ejecutar `npm test` y `npm run test:coverage` desde `web/`.

### H-WEB-06 — Alertas de vulnerabilidad en dependencias por clasificar
- Estado: CANDIDATO
- Evidencia: la instalación reproducible `npm ci` en `web/` reportó 43 vulnerabilidades: 27 moderadas, 10 altas y 6 críticas. No se identificaron en esta ejecución los paquetes, rutas de dependencia ni advisories concretos.
- Impacto: podrían existir dependencias vulnerables en el árbol usado para compilar o ejecutar el frontend; el alcance y la exposición no están confirmados.
- Prioridad propuesta: Alta, pendiente de verificar los paquetes y advisories.
- Contrato potencialmente afectado: no determinado; posible seguridad e integridad del frontend.
- Cómo validarlo: ejecutar `npm audit` en `web/`, revisar las dependencias directas y transitivas afectadas y confirmar versiones corregidas antes de proponer una remediación.
