---
name: find-pull-request
description: "Find a GitHub pull request by number, title, branch, status, or description. Use the GitHub MCP list_pull_requests tool and inspect paginated results."
argument-hint: "Repository and PR criteria, for example: owner/repo, title contains 'login'"
---

# Find Pull Request

Encuentra y reporta el PR que coincide con los criterios del usuario. No crees, edites ni cierres PRs.

## Procedimiento

1. Obtén `owner` y `repo` del contexto o pídelos si no están claros. No los inventes.
2. Identifica los criterios: número, texto del título o cuerpo, estado, rama base o rama de origen. Si el usuario especifica un autor, usa `mcp_github_mcp_se_search_pull_requests`; la herramienta de listado no admite ese filtro.
3. Para los demás casos, llama a `mcp_github_mcp_se_list_pull_requests` con el repositorio y los filtros disponibles (`state`, `base`, `head`). Solicita los campos necesarios: `number`, `title`, `body`, `state`, `draft`, `html_url`, `user`, `head`, `base`, `created_at`, `updated_at` y `merged_at`.
4. Revisa las páginas consecutivas, hasta que una devuelva menos resultados que `perPage` o se agoten las páginas. No concluyas que no existe una coincidencia después de revisar solo la primera página.
5. Compara los criterios restantes con los resultados. Para texto libre, busca en título, cuerpo y nombres de ramas; distingue coincidencias exactas de parciales.
6. Si no hay coincidencias, informa qué repo, filtros y páginas revisaste. Si hay varias, preséntalas para que el usuario elija; no selecciones una arbitrariamente.

## Respuesta

Para cada coincidencia, muestra número, título, estado, rama origen → base, autor y enlace. Indica si es borrador o está fusionado cuando esos datos estén disponibles. Si GitHub no permite acceder al repositorio, informa el error sin afirmar que el PR no existe.