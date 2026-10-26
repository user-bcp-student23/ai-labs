# Plan de correccion — API

## Seleccion y alcance

Se seleccionan hallazgos existentes y `Pendiente` en `HALLAZGOS.md`:

- **H-API-01** — prerrequisito solicitado para establecer una identidad verificable antes de autorizar por owner.
- **H-API-02** — severidad alta: riesgo de acceso y asignacion de tareas entre identidades.
- **H-API-04** — severidad media: alcance acotado a la validacion y persistencia de archivos.

H-API-03 no se incluyo en la implementacion inicial y permanecio pendiente en esa etapa. Tras la revision local, el usuario selecciono corregir todos los problemas reportados; el seguimiento y las pruebas de H-API-03 se registran en el addendum. H-API-01 debe resolverse antes de H-API-02; de lo contrario, un token falsificable invalida la proteccion por identidad.

`docs/ENDPOINTS.md` existe y describe el contrato observado y las decisiones humanas aprobadas: JWT HS256 con `iss=ISS`, `aud=CLAIM` y clave leida de `SECRET`; PyJWT; HTTP 403 para solicitudes cross-owner; extensiones `.txt` y `.pdf`, maximo inclusivo de 4 bytes, nombre unico ante colisiones, HTTP 415 por extension invalida y HTTP 413 por tamano excedido, ambos con `{"detail":"Invalid upload"}`. Se conservaron las rutas y las formas de respuesta exitosa, salvo que `fileName` refleja el nombre unico guardado ante colision. La integracion del emisor real del JWT sigue pendiente; las pruebas usan una clave ficticia aislada.

## H-API-01 — Verificar JWT real
**Hallazgo de HALLAZGOS.md:** H-API-01, “Token Base64 con secreto embebido y sin firma”, Vulnerabilidad, severidad alta, estado Pendiente. Se incluye porque H-API-02 depende de una identidad autenticada que no pueda falsificarse.

**Problema:** `legacy_identity` decodifica Base64, confia en los campos username/role y compara un secreto fijo; no verifica firma, issuer ni audience.

**Cambio propuesto:**

1. Reemplazar la confianza en el contenido decodificado por validacion criptografica de un JWT estandar, verificando firma, algoritmo permitido, `iss`, `aud` y expiracion.
2. Obtener la clave desde una variable de entorno, nunca desde codigo ni un valor real en pruebas. Mantener la interfaz interna de identidad (`username` y `role`) que consumen las rutas.
3. Propuesta de biblioteca: PyJWT, justificada para validar el formato y claims JWT sin implementar criptografia propia. Requiere confirmar dependencia y coordinar el contrato con el emisor externo antes de instalar o integrar.
4. No aceptar tokens legacy como fallback despues de la migracion: ese fallback mantendria la vulnerabilidad. El cambio del formato del token requiere coordinacion con su emisor. Mantener el status 401 y la forma JSON `detail` observados en `docs/ENDPOINTS.md`; el texto generico exacto queda pendiente de acuerdo porque el codigo actual devuelve detalles variables de excepcion.
5. Mantener los status y los campos de respuesta exitosa documentados en `docs/ENDPOINTS.md`. El token debe provenir del emisor acordado; no inventar ni publicar una muestra que contenga una clave.

**Archivos a tocar:**

- `api/app/main.py` — conservar dependencias de autenticacion en rutas y delegar la verificacion.
- `api/app/security.py` — validacion JWT y construccion de identidad.
- `api/requirements.txt` — agregar PyJWT solo despues de confirmar contrato y dependencia.
- `api/tests/test_api.py` — caracterizacion previa y casos de tokens firmados/invalidos.

**Prueba de caracterizacion antes de tocar implementacion:**

- Con el token ficticio legacy actualmente usado por `tests/test_api.py`, registrar status y forma de respuesta de rutas protegidas para token valido, invalido y expirado.
- Despues del cambio, usar una clave exclusiva de prueba para emitir JWT validos y verificar que las rutas conservan respuestas para identidad autentica; comprobar rechazo de firma, algoritmo, `iss`, `aud` o expiracion no validos y ausencia de token.

**Decisiones confirmadas:** HS256, `iss=ISS`, `aud=CLAIM`, variable de entorno `SECRET` y aprobacion de PyJWT. Se agrego PyJWT 2.15.1, version indicada por PyPI como release vigente en la consulta; el escaneo de advisories configurado no acepta el ecosistema Python, por lo que la verificacion de dependencia fue best-effort y no sustituye SCA reproducible. **Pendiente externo:** coordinar al emisor real para que entregue tokens conformes; no usar un secreto real en pruebas.

## H-API-02 — Vincular el owner con la identidad

**Hallazgo de HALLAZGOS.md:** H-API-02, “El cliente puede elegir el owner de consultas y tareas”, Vulnerabilidad, severidad alta, estado Pendiente.

**Problema:** `GET /api/tasks` y `GET /api/summary` permiten que el parametro `owner` sustituya el username de la identidad. `POST /api/tasks` permite que el cuerpo elija el owner de la tarea. Las consultas o escrituras pueden afectar datos de otra identidad.

**Cambio propuesto:**

1. Usar una identidad autenticada y verificada como fuente de autoridad. La verificacion criptografica completa corresponde a H-API-01 y es prerrequisito; no se considerara resuelto H-API-02 mientras la identidad pueda falsificarse.
2. Mantener las rutas, nombres de campos y formas de respuesta existentes. Cuando `owner` se omita, usar la identidad autenticada. Si se proporciona en query o cuerpo, permitirlo solo si coincide con esa identidad; para una discrepancia, devolver un error generico 403. Esto es una denegacion deliberada de acceso cruzado, no un cambio al formato de las operaciones autorizadas.
3. Definir un modelo Pydantic para el request de creacion con los campos y valores predeterminados observados. Caracterizar primero coerciones, campos omitidos y campos adicionales; si el modelo requerido altera el comportamiento observado, registrar la diferencia para aprobacion antes de implementarla.
4. En la implementacion inicial, mantener este cambio limitado a la autorizacion y dejar SQL concatenado de H-API-03 fuera de esa entrega. El seguimiento posterior de H-API-03 se documenta en el addendum.
5. Separar la regla de resolucion/autorizacion de owner en una funcion de servicio pequena, dejando a la ruta la coordinacion HTTP y evitando duplicar la regla entre tareas y resumen.

**Archivos a tocar:**

- `api/app/main.py` — conservar endpoints y formatos, delegar la regla de owner y responder ante discrepancias.
- `api/app/schemas.py` — modelo Pydantic de creacion compatible con los campos y defaults observados.
- `api/app/services/task_service.py` — resolver y validar el owner a partir de la identidad verificada.
- `api/tests/test_api.py` — caracterizacion previa y pruebas de autorizacion.

**Prueba de caracterizacion antes de tocar implementacion:**

- Con el token ficticio de `student`, registrar el resultado y formato actual de listar tareas sin `owner`, listar con `owner=student`, consultar resumen y crear una tarea omitiendo `owner`; conservar status, claves JSON y defaults.
- Registrar en pruebas locales aisladas el comportamiento actual de una consulta con `owner` distinto y de una creacion con owner distinto. Estas pruebas describen el comportamiento previo y se actualizaran para exigir 403 una vez aprobada la correccion.
- Caracterizar campos omitidos, adicionales y valores de tipos no string en el body para definir el modelo Pydantic sin asumir cambios de contrato.
- Despues del cambio, probar acceso propio exitoso, rechazo de owner distinto en las tres operaciones, y conservar respuestas de las operaciones propias.

**Aprobacion y dependencia:** el usuario aprobo HTTP 403 con `{"detail":"Owner does not match authenticated identity"}`. La regla se implemento y probo con JWT firmados localmente; H-API-02 permanece Pendiente hasta confirmar que el emisor externo cumple H-API-01.

## H-API-04 — Validar y guardar archivos de forma segura

**Hallazgo de HALLAZGOS.md:** H-API-04, “Carga de archivos usa el nombre del cliente sin limites visibles”, Vulnerabilidad, severidad media, estado Pendiente.

**Problema:** `POST /api/requirements` usa el nombre recibido para construir la ruta de destino y lee el archivo completo antes de guardarlo. No se observan validaciones de nombre, extension ni tamano.

**Cambio propuesto:**

1. Conservar la ruta multipart y, para archivos permitidos, el status 201 y las claves de respuesta observadas (`owner`, `fileName`, `storedAt`, `size`) descritas en `docs/ENDPOINTS.md`.
2. Extraer la validacion y persistencia a una funcion/servicio de una sola responsabilidad. Normalizar el nombre, verificar que el destino permanezca dentro de `upload_dir`, y manejar colisiones sin sobrescribir silenciosamente.
3. Definir una allowlist de extensiones y un maximo de bytes con constantes nombradas. Comprobar tamano durante lectura acotada, antes de persistir, para evitar cargar contenido ilimitado en memoria.
4. Para archivos invalidos o demasiado grandes, responder con un error HTTP controlado y no escribir archivo. Mantener los nombres de campo de respuesta para las cargas validas. Los status y el cuerpo de error deben acordarse antes de implementar; no forman parte de una respuesta observada actualmente.
5. Usar biblioteca estandar existente; no agregar dependencias.

**Archivos a tocar:**

- `api/app/main.py` — delegar almacenamiento/validacion y mantener la ruta y respuesta de exito.
- `api/app/services/upload_service.py` — normalizar, validar limites y persistir dentro del directorio permitido.
- `api/app/schemas.py` — tipo de respuesta de carga si hace falta para preservar su forma.
- `api/tests/test_api.py` — pruebas de caracterizacion y regresion con directorios temporales.

**Prueba de caracterizacion antes de tocar implementacion:**

- Subir un archivo ficticio permitido por el comportamiento actual a un `upload_dir` temporal; registrar status 201, claves y valores de respuesta, bytes escritos y ruta.
- Despues de aprobar la politica, probar filename con separadores, extension no permitida, tamano sobre el limite y colision: esperar error controlado y ningun archivo fuera del directorio ni sobrescritura.
- Probar un archivo normal permitido: esperar status 201, mismo formato de respuesta y contenido intacto.

**Decisiones confirmadas:** extensiones `.txt` y `.pdf`, maximo inclusivo de 4 bytes, nombre unico ante colisiones, HTTP 415 para extension no permitida y HTTP 413 para exceso de tamano; ambos responden `{"detail":"Invalid upload"}`. El limite de 4 bytes y los codigos/cuerpo fueron confirmados por el usuario.

**Resultado:** implementado y probado; H-API-04 se marco Resuelto en `HALLAZGOS.md`.

## Validacion prevista

Registrar cada ejecucion con fecha, comando, resultado e IDs afectados en esta seccion. La caracterizacion debe correr contra la implementacion anterior a cualquier cambio de comportamiento; despues, ejecutar `python -m pytest` desde `api/` y medir la cobertura de lineas del codigo modificado, con objetivo minimo de 85%. H-API-01, H-API-02 y H-API-04 solo se marcaran resueltos tras pruebas exitosas, cobertura suficiente y coordinacion del emisor JWT cuando corresponda.

### Ejecuciones

- **2026-10-26; componente api; IDs H-API-01, H-API-02, H-API-04; antes del cambio:** `python -m pytest` ejecutado desde la raiz fallo en coleccion con `ModuleNotFoundError: No module named 'app'` (directorio incorrecto). No se conto como prueba.
- **2026-10-26; componente api; IDs H-API-01, H-API-02, H-API-04; caracterizacion previa:** `Set-Location api; python -m pytest` — 9 passed. La caracterizacion verifico token legacy valido/invalido/expirado, lectura y creacion para owner distinto, y aceptacion previa de extensiones no permitidas y archivos mayores al limite acordado.
- **2026-10-26; componente api; IDs H-API-01, H-API-02, H-API-04; despues del cambio:** `Set-Location api; python -m pytest` — 22 passed.
- **2026-10-26; componente api; IDs H-API-01, H-API-02, H-API-04; cobertura posterior:** `Set-Location api; python -m pytest --cov=app --cov-report=term-missing` — 22 passed; cobertura total 95%, `app/main.py` 93%, `app/services/upload_service.py` 92%; los archivos nuevos `security.py` y `task_service.py` tuvieron cobertura completa segun el reporte. Validacion ejecutada con Python 3.14.7.
- **2026-10-26; componente api; H-API-01; dependencias:** `python -m pip check` — No broken requirements found. El escaneo CVE compartido no acepta ecosistema Python; la consulta best-effort verifico version PyJWT y advisories publicos, no se considera un escaneo completo de dependencias.
- **2026-10-26; componente api; IDs H-API-01, H-API-02, H-API-04; analisis estatico:** comprobacion de problemas de los archivos modificados — sin errores; `git diff --check -- api` — sin errores.

## Addendum — correcciones posteriores a la revision local

El usuario eligio **“Fix all issues”** para las observaciones concretas de la revision. Este seguimiento amplio la implementacion inicial solo dentro de `api/`:

- **H-API-03:** se parametrizaron los filtros de listado y resumen, los campos de insercion y la lectura de la tarea por ID. No se concatenan valores de usuario o identidad en sentencias SQL.
- **H-API-06 (parcial):** `/api/backend-health` ahora usa `Identity.username`, devuelve un modelo Pydantic tipado y captura solo errores HTTP de urllib3. Ante esos fallos conserva HTTP 200 y `status: 0`, devuelve `Health check unavailable` en vez del detalle interno y registra el tipo de error en el log. La separacion de persistencia/capas y otras mejoras agrupadas en H-API-06 permanecen pendientes.
- **H-API-04:** la revision confirmo que la normalizacion, limite, extension y escritura exclusiva estaban implementados; no hizo falta cambiar su estado.

### Ejecuciones del addendum

- **2026-10-26; componente api; IDs H-API-03, H-API-06; caracterizacion antes del cambio:** desde `api/`, `python -m pytest tests/test_api.py -k "task_filter_treats_sql_syntax_in_username_as_literal or summary_filter_treats_sql_syntax_in_username_as_literal or task_fields_containing_quotes_are_persisted_literally or backend_health_uses_verified_identity_attribute or backend_health_hides_transport_exception_details" -q` — **5 fallaron como se esperaba**, reproduciendo las consultas vulnerables y el fallo del endpoint health.
- **2026-10-26; componente api; IDs H-API-03, H-API-06; despues del cambio:** el mismo comando focalizado — **5 pasaron**.
- **2026-10-26; componente api; IDs H-API-03, H-API-06; suite y cobertura:** desde `api/`, `python -m pytest --cov=app --cov-report=term-missing` — **27 pasaron**, cobertura total **98%** (188 statements, 1 missed); seis archivos tuvieron cobertura completa. La unica linea no cubierta que reporto el comando pertenece a `app/services/upload_service.py`, no a los cambios de este addendum. Python ejecutado: **3.14.7**.
- **2026-10-26; componente api; IDs H-API-03, H-API-06; sintaxis:** Pylance no encontro errores de sintaxis en `main.py`, `schemas.py` ni `tests/test_api.py`.
- **2026-10-26; componente api; IDs H-API-03, H-API-06; diff:** `git diff --check -- api` — sin errores.

**Pendientes que no se declararon resueltos:** H-API-01/02 requieren confirmacion real del emisor JWT y del despliegue de `SECRET`; H-API-06 conserva la deuda de capas; H-API-07 requiere un escaneo reproducible de dependencias. La cobertura global no certifica por si sola el porcentaje del diff, pero las lineas funcionales añadidas por este addendum fueron ejecutadas por sus pruebas de regresion.
