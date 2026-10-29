# Tasks

## 1. Characterize the Existing API Contract

- [x] 1.1 From `api/`, run the JWT and task-ownership characterization command from `design.md`; verify the existing success, HTTP 401, and HTTP 403 responses remain unchanged.
- [x] 1.2 Add an API test using a test-only `SECRET` shorter than 32 bytes; verify the existing configuration failure is raised and no key value is included in test output.

## 2. Add External-Issuer Integration Coverage

- [ ] 2.1 Confirm the approved non-production TrackingProcessor v1.0 environment and designated test username; provision the short-lived issuer token and matching API `SECRET` only through protected runtime configuration, and verify neither value is written to source or evidence.
- [ ] 2.2 Add an API-scoped integration check that consumes the externally issued token and environment-provided `SECRET` against an isolated test database; verify `GET /api/tasks` returns HTTP 200 and tasks owned by the expected verified username without logging credentials.
- [ ] 2.3 Extend the integration check to request tasks for a different owner using the same verified identity; verify HTTP 403 and `{"detail":"Owner does not match authenticated identity"}`.

## 3. Verify Integration and Record Safe Evidence

- [x] 3.1 From `api/`, run `python -m pytest`; verify the deterministic suite passes, including rejection of expired, wrong-issuer, wrong-audience, and incomplete-claim tokens.
- [x] 3.2 Run the external-token integration check explicitly against the approved non-production environment; record issuer/version, environment identifier, result, and whether `SECRET` is configured, without recording token or secret values. If prerequisites are unavailable, record the check as blocked or not run, never as passed.
- [ ] 3.3 Review the integration output and evidence; verify no token, secret, or credential values are present.
- [x] 3.4 Run `openspec validate "validate-api-jwt-integration" --type change --json`; verify the change validates successfully.
