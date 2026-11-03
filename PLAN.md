# Plan

Plan de correccion del componente `api`. Referencias: `HALLAZGOS.md` (matriz), `docs/GOOD_PRACTICES.md` (seccion `api`) y las reglas de Clean Code de `AGENTS.md`. No existe `docs/ENDPOINTS.md`; no se crea en este paso. El contrato a preservar es el comportamiento observado en `api/app/main.py`, listado abajo.

Nota: este archivo se ha recreado varias veces porque no persistia en disco. Su contenido se reconstruye a partir de los registros de ejecucion, las aprobaciones recibidas y las decisiones de la persona usuaria.

## Contrato observado (a preservar)

| Metodo y ruta | Entrada | Respuesta exitosa | Errores hoy |
|---|---|---|---|
| `GET /api/tasks` | `Authorization`, `owner` (query, opcional) | 200, lista de tareas | 401 |
| `POST /api/tasks` | `Authorization`, body JSON `title`, `description`, `status`, `priority`, `owner` | 201, tarea creada | 401 |
| `GET /api/summary` | `Authorization`, `owner` (query, opcional) | 200, resumen | 401 |
| `POST /api/requirements` | `Authorization`, multipart `file` | 201, `owner`, `fileName`, `storedAt`, `size` | 401 |
| `GET /api/backend-health` | `Authorization` | 200, `requestedBy`, `status`, `body` | 401 |

Datos semilla: 3 tareas; `student` posee 2 y `trainer` posee 1.

---

## Aprobaciones registradas

Texto tal como lo indico la persona usuaria. No son aprobaciones inventadas.

- H-API-01, H-API-02, H-API-04: "Todo esta aprobado por Nataly Aylas".
- H-API-03: "H-API-03 desbloquear y aprobar".
- H-API-06: "H-API-06 ya esta verificado y aprobado". Sin evidencia en el repositorio (no hay advisory consultado ni plan de version). Se registra como afirmacion de la persona usuaria, no como verificacion ejecutada por el agente.
- H-API-01 a H-API-12: "Aprobar todos los hallazgos".
- H-API-05 a H-API-12: "si los apruebo" (respuesta a la revision de los planes). Cubre los planes tal como estan escritos. Las decisiones que cambian valores o contratos siguen pendientes hasta recibir respuesta.
- H-API-01 a H-API-12, todos los planes: "aprobar todo" (nueva respuesta de la persona usuaria). Aprueba los planes tal como estan escritos. No fija los valores PENDIENTE (tamano maximo, limite de salud, emisor de `auth/`, accion de H-API-06), que siguen abiertos.

---

## Decisiones recibidas (pendientes de implementar)

- H-API-05: extensiones permitidas `.pdf`, `.docx`, `.txt`. Tamano maximo: 5 MB (respuesta de la persona usuaria).
- H-API-07: origen permitido para CORS `http://localhost:4200`.
- H-API-12: limite de caracteres del cuerpo de salud: PENDIENTE (la persona usuaria no respondio el valor; propuesta inicial 200).
- Emisor de `auth/` con el formato de H-API-03: `ai-labs-auth` (respuesta de la persona usuaria).
- H-API-06: accion `solo registrar` (respuesta de la persona usuaria). No se consultaron advisories.

---

## Registro de ejecuciones

### Linea base

Antes de los cambios de H-API-01 a 04: 9 pasaron y 4 fallaron como `xfail`. Cobertura no medida en esa linea base.

### H-API-01 y H-API-02 (SQL concatenado)

- Caracterizacion antes: contrato de listado y creacion en `api/tests/test_api.py`.
- Correccion: `api/app/repository.py` (consultas con `?`), `api/app/schemas.py` (`TaskCreate`, `TaskOut`, `SummaryOut`).
- Resultado tras el cambio: incluido en la corrida de 13 pasados con cobertura 95%.
- Estado: `Resuelto`.

### H-API-04 (autorizacion por `owner` del cliente)

- Correccion: `resolve_owner` en `api/app/services.py`, 403 si `owner` no coincide con `identity["username"]`.
- Resultado: incluido en la corrida de 13 pasados con cobertura 95%.
- Estado: `Resuelto`.

### H-API-03 (token Base64 con secreto embebido)

- Antes del cambio: 14 pasados y 1 `xfail` (token legado). Las pruebas de correccion fallaban con `--runxfail`.
- Despues del cambio: 26 pasados, cobertura total 96%. `app/security.py` 97%, `app/main.py` 92%.
- Cambios: `api/app/security.py` (HMAC-SHA256 con biblioteca estandar, `iss`, `aud`, `sub`, `role`, `exp`), `api/app/constants.py`, `api/tests/conftest.py`, `api/tests/test_security.py`, `README.md` (variable `WORKSHOP_TOKEN_SECRET`).
- Decisiones: sin `PyJWT`; `WORKSHOP_TOKEN_SECRET` sin valor por defecto; `iss="ai-labs-auth"` y `aud="ai-labs-api"` elegidos por el agente, no confirmados.
- Riesgo abierto: el emisor de `auth/` debe firmar con el mismo formato. No verificado.
- Estado: `Resuelto`.

Corrida de referencia (cwd `api/`): `.venv\Scripts\python.exe -m pytest -p no:warnings --cov=app --cov-branch`. Ultima verificacion: 26 pasados, cobertura 96%.

---

### H-API-07, 08, 09, 10 y 11 (ejecucion)

- Caracterizacion y correccion: `api/tests/test_hardening.py` (7 pruebas). Antes del cambio, 3 fallaban (CORS con `*` y error de salud con detalle). Despues del cambio, pasan.
- Suite completa en `api/` con `.venv\Scripts\python.exe -m pytest -p no:warnings --cov=app --cov-branch`: salida 0 (todas pasan), cobertura de `app/` 99%.
- H-API-11 ya no existia en el codigo; se verifico con las pruebas de resumen y se marca como resuelto sin cambio nuevo.
- Pendientes sin ejecutar: H-API-05 (falta tamano maximo), H-API-06 (falta verificar advisories), H-API-12 (falta limite de caracteres).

## Planes por hallazgo pendiente

Ningun codigo de estos hallazgos se ha editado.

### H-API-05: nombre de archivo subido sin normalizar (alta)

- Hallazgo: `file.filename` se une a la ruta de subida (`api/app/main.py:79`). Un nombre con `../` o absoluto escribe fuera de `uploads/`. No hay limite de extension ni de tamano.
- Problema: escritura de archivos fuera del directorio previsto.
- Cambio propuesto:
  - Normalizar el nombre con `Path(filename).name` y rechazar nombres vacios, `.` o `..`.
  - Lista blanca de extensiones `.pdf`, `.docx`, `.txt` y tamano maximo, ambos como constantes en `api/app/constants.py`. El tamano maximo queda PENDIENTE.
  - Validacion en `api/app/services.py`; escritura en un metodo de almacenamiento. La ruta solo orquesta.
- Archivos: `api/app/main.py`, `api/app/services.py`, `api/app/constants.py`, `api/tests/test_api.py`.
- Caracterizacion antes: subida de un `.txt` valido devuelve 201 con `fileName`, `storedAt`, `size`.
- Prueba de correccion: `../x.txt` y ruta absoluta no escriben fuera de `uploads/`; extension no permitida y tamano excedido responden 4xx sin escribir.
- Pregunta abierta: rechazar archivos cambia la respuesta de `POST /api/requirements` (nuevo codigo 4xx). Requiere confirmacion del codigo y del tamano.

### H-API-06: dependencias con posibles CVE (media)

- Hallazgo: `api/requirements.txt:4` (`urllib3==2.5.0`) y `api/requirements.txt:5` (`python-multipart==0.0.21`).
- Problema: no hay evidencia de advisory consultado en este entorno.
- Cambio propuesto: consultar advisories con una herramienta de SCA antes de decidir. Si hay CVE, subir a la version corregida y ejecutar la suite completa.
- Archivos: `api/requirements.txt`.
- Caracterizacion: suite completa en verde antes de cambiar versiones.
- Estado: aprobado por la persona usuaria, sin evidencia en el repositorio. No se afirma que se haya ejecutado una comprobacion de CVE.
- Pregunta abierta: accion PENDIENTE (solo registrar, o consultar advisories).

### H-API-07: secreto y CORS en el codigo (media)

- Hallazgo: `api/app/main.py:51` (`allow_origins=["*"]`) y `api/app/main.py:52` (`allow_credentials=True`). El secreto ya no vive en el codigo (H-API-03).
- Problema: CORS permite cualquier origen con credenciales.
- Cambio propuesto: leer el origen permitido de una variable de entorno con valor por defecto restrictivo y mantener `allow_credentials` solo con origenes explicitos. Origen decidido: `http://localhost:4200`.
- Archivos: `api/app/main.py`, `api/app/constants.py`, `README.md`.
- Caracterizacion antes: respuesta CORS actual para un origen cualquiera.
- Prueba de correccion: `http://localhost:4200` recibe `Access-Control-Allow-Origin`; un origen no listado no lo recibe.
- Nota: `web/` no se leyo (fuera de alcance); no se verifico que el frontend use ese origen.

### H-API-08: detalle de error expuesto (media)

- Hallazgo: el error del token ya quedo generico con H-API-03 (`api/app/main.py:26`, `Invalid token`). Queda `api/app/main.py:91`: `backend_health` devuelve `str(error)` en el cuerpo.
- Problema: texto de la excepcion visible para el cliente.
- Cambio propuesto: en salud, `status: 0` con un `body` generico. El detalle completo va solo al log del servidor.
- Archivos: `api/app/main.py`, `api/tests/test_api.py`.
- Caracterizacion antes: cuerpo de error de salud cuando la URL no responde.
- Prueba de correccion: el cuerpo no contiene el texto de la excepcion; el detalle queda en el log.
- Pregunta abierta: confirmar que el frontend no depende del texto exacto.

### H-API-09: servicio en un solo `create_app` (media, refactor)

- Hallazgo: `api/app/main.py:28` concentra conexion SQLite, siembra, middleware, rutas y cierre.
- Problema: dificulta probar y cambiar cada capa por separado.
- Cambio propuesto: separar `api/app/database.py` (conexion y siembra), dejar en `main.py` la creacion de la app y el registro de rutas, y mover cada ruta a `api/app/routes/`. Sin cambiar URLs ni respuestas.
- Archivos: `api/app/main.py`, `api/app/database.py` (nuevo), `api/app/routes/` (nuevo).
- Caracterizacion antes: todas las pruebas de `api/tests/test_api.py` en verde.
- Prueba de correccion: las mismas pruebas, sin cambios de expectativa.
- Riesgo: cambian las rutas de importacion; `app = create_app()` debe seguir funcionando al importar.

### H-API-10: tipos amplios y excepciones genericas (baja, refactor)

- Hallazgo: `api/app/main.py:25` (`dict[str, str]` de identidad), `:60`, `:72`, `:78` (`dict[str, Any]` en respuestas) y `:90` (`except Exception`).
- Problema: validacion debil y errores ocultos.
- Cambio propuesto: modelos Pydantic para respuestas (falta uno para subida y para salud); en la consulta de salud capturar excepciones concretas de `urllib3` (`urllib3.exceptions.HTTPError`, `OSError`) en lugar de `Exception`.
- Archivos: `api/app/schemas.py`, `api/app/main.py`.
- Caracterizacion antes: forma exacta de cada respuesta actual.
- Prueba de correccion: la forma sigue igual; un error de red sigue devolviendo `status: 0`.

### H-API-11: condicionales anidados y SELECT duplicado (baja, refactor)

- Hallazgo: conteo de prioridad alta con `if` anidados; lista de columnas repetida en consultas.
- Cambio propuesto: retorno anticipado en `api/app/services.py` y constante para la lista de columnas en `api/app/repository.py`.
- Archivos: `api/app/services.py`, `api/app/repository.py`.
- Caracterizacion antes: resumen actual para `student` y `trainer`.
- Prueba de correccion: el mismo resumen.

### H-API-12: URL de salud devuelve el cuerpo remoto (baja, sugerencia)

- Hallazgo: `api/app/main.py:86` lee `AUTH_HEALTH_URL`; `api/app/main.py:89` devuelve el cuerpo completo del servicio remoto.
- Problema: se expone contenido remoto sin acotar.
- Cambio propuesto: devolver solo el estado y un cuerpo acotado. El limite se define como constante con nombre en `api/app/constants.py` (PENDIENTE; propuesta inicial 200). Validar que la URL sea `http` o `https`.
- Archivos: `api/app/main.py`, `api/app/constants.py`, `README.md`.
- Caracterizacion antes: cuerpo devuelto con un servidor local de prueba (no remoto).
- Prueba de correccion: el cuerpo se trunca al limite; un esquema no permitido se rechaza.
- Pregunta abierta: limite de caracteres PENDIENTE y si la truncacion es aceptable para el frontend.

---

## Preguntas abiertas

1. H-API-05: tamano maximo de archivo, y aceptar el nuevo 4xx en `POST /api/requirements`.
2. H-API-06: solo registrar la aprobacion, o consultar advisories antes de subir versiones.
3. H-API-12: limite de caracteres del cuerpo de salud.
4. H-API-08 y H-API-12: confirmar que el frontend no depende del texto exacto de error de salud.
5. Emisor de `auth/`: confirmar que firma el token con el formato de H-API-03. Sin esto el login no funciona de extremo a extremo.
6. `prompts/` (sin rastrear): decidir si entra en el commit.

## Comandos no ejecutados en esta recreacion

- No se editaron archivos de `api/`.
- No se consultaron advisories de CVE (H-API-06).
- Los resultados de pruebas de H-API-01 a 04 provienen de ejecuciones previas registradas arriba.
