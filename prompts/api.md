AMBITO
Workspace ai-labs abierto en su raiz. Lee codigo solo en api/.
Todas las rutas parten de la raiz. Lee README.md, RETO.md y docs/ generales.
Este pedido es de solo lectura; no escribas archivos.
Git se ejecuta desde la raiz; las pruebas propuestas usan cwd api/.
No leas ni modifiques codigo de auth/ ni web/. Usa IDs H-API-NN y componente api.

CONTEXTO
ai-labs expone una ruta de autenticacion o consulta en api/ implementada en Python.
Lee README.md, RETO.md y docs/ENDPOINTS.md si existe. Revisa api/app/__init__.py,
api/app/main.py, api/tests/test_api.py, api/requirements.txt y api/pyproject.toml.
Localiza la ruta desde el handler HTTP hasta la consulta SQL (sqlite3 o similar).
No des por cierta la lista de RETO.md.

OBJETIVO
Determinar si entradas del login llegan concatenadas (f-string, %, +, .format)
a una consulta SQL, o si se pasan como parametros (?, :name).

RESTRICCIONES
No edites codigo ni ejecutes ataques contra servicios remotos. Usa solo codigo y
datos ficticios locales. Si falta un archivo o no puedes ejecutar una comprobacion,
dilo. No cambies contratos ni leas otros componentes. No uses # noqa ni excluyas
reglas de scanners.

CRITERIOS DE ACEPTACION
Identifica el recorrido de la entrada hasta la consulta con archivo y linea.
Distingue concatenacion, parametrizacion y cualquier caso no comprobado.
Propone una prueba local con credenciales validas, invalidas y entrada con comilla
(por ejemplo ' OR '1'='1), con resultado esperado segun el contrato observado.
No afirmes que la prueba paso si solo la propusiste.

FORMATO DE RESPUESTA
Tabla: afirmacion | evidencia archivo:linea | comprobado o hipotesis | prueba propuesta.
Termina con preguntas abiertas y comandos no ejecutados (por ejemplo,
python tools/lab.py test api, o pytest desde api/ con cwd api/).