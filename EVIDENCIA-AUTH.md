# Evidencia de implementación — auth / H-AUTH-01

## Cambio verificado

- El emisor ahora produce JWT HS256 con los claims y la expiración de 300 segundos definidos en `auth/contracts/tracking-processor-v1.yaml`.
- `POST /auth/login` conserva la ruta, los campos observables de la respuesta y los status de éxito y credenciales inválidas.
- La clave se obtiene de `SECRET`; no se incluye ningún valor de clave, token ni credencial en esta evidencia.

## Ejecuciones

Resultados obtenidos el 2026-10-27 desde la raíz de `ai-labs/`:

| Componente e IDs | Comando | Código de salida | Resultado |
|---|---|---:|---|
| auth — H-AUTH-01 | `python tools/lab.py test auth` | 0 | 12 pruebas pasaron. JaCoCo: `AuthResource` 100% y `TokenIssuer` 91,3% de líneas. |
| api — H-API-01, regresión de consumidor | `python tools/lab.py test api` | 0 | 42 pruebas pasaron; cobertura total 98,11%; 83 warnings de deprecación reportados, no silenciados. |
| auth — H-AUTH-01, YAML | `python -c "import yaml,pathlib; [yaml.safe_load(pathlib.Path(p).read_text(encoding='utf-8')) for p in [r'auth\\contracts\\tracking-processor-v1.yaml',r'compose.yaml']]"` | 0 | Los dos archivos YAML se parsearon correctamente. |
| auth — H-AUTH-01, diff | `git diff --check` | 0 | Sin errores de whitespace. |

## Pendiente

- No se pudo ejecutar `docker compose config --quiet`: el CLI `docker` no está disponible en este entorno.
- No se ejecutó una integración real con TrackingProcessor v1.0. El contrato YAML permanece marcado para revisión de Gobierno de APIs.
- La provisión real de `SECRET` y la revisión humana del cambio siguen pendientes. No se usaron secretos reales.
