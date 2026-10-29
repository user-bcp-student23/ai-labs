# Design

## Context

See [proposal.md](./proposal.md) for the motivation and [api-jwt-integration spec](./specs/api-jwt-integration/spec.md) for the observable requirements.

The API already validates a Bearer JWT in `api/app/security.py`: HS256 signature, `iss=ISS`, `aud=CLAIM`, expiry, and required `username` and `role` claims. It reads `SECRET` from the process environment and rejects keys shorter than 32 bytes. Protected task routes in `api/app/main.py` use the verified identity, and `api/app/services/task_service.py` rejects a different requested owner with HTTP 403. `api/tests/test_api.py` already characterizes these behaviors with locally signed test tokens and a temporary SQLite database.

The remaining gap is proof with a token actually issued by TrackingProcessor v1.0 and evidence that the integration runtime supplies the matching `SECRET`. This is a validation change in `api/`; it does not require changing the issuer, application behavior, endpoint contracts, or the `auth/` and `web/` components.

## Goals / Non-Goals

**Goals:**

- Verify the existing API contract using a short-lived token issued by the designated TrackingProcessor v1.0 integration issuer.
- Exercise the protected task route with an isolated API test database and a test identity whose username is known to the test.
- Verify that the integration runtime obtains `SECRET` from protected environment configuration and that evidence reports configuration status without its value.
- Keep integration validation distinguishable from the deterministic API test suite so an unavailable issuer or environment cannot be reported as a successful integration run.

**Non-Goals:**

- Change JWT algorithms, claims, validation rules, `SECRET` requirements, response bodies/statuses, or task ownership policy.
- Implement token issuance, change `POST /auth/login`, or modify the external issuer.
- Add code or tests under `auth/` or `web/`, introduce another JWT library, or redesign API authentication.
- Store tokens, credentials, or secret values in source, test fixtures, logs, or committed evidence.

## Contracts Protected

- Protected API requests continue to require a Bearer token satisfying the documented HS256 contract and `SECRET` remains an environment-provided key of at least 32 bytes.
- An absent or invalid token continues to return HTTP 401 with `{"detail":"Invalid token"}`.
- `GET /api/tasks` with `owner` absent or empty continues to use the verified token username and return that identity's tasks.
- A different requested owner continues to return HTTP 403 with `{"detail":"Owner does not match authenticated identity"}`.
- Missing or undersized `SECRET` remains a configuration failure, not an authentication success. No outward error behavior is changed by this validation work.

These contracts are documented in [docs/ENDPOINTS.md](../../../docs/ENDPOINTS.md) and covered by existing API tests.

## Components Affected

- `api/app/security.py`: existing JWT and environment-key boundary; no behavior change is planned.
- `api/app/main.py` and `api/app/services/task_service.py`: existing identity-to-owner enforcement; no behavior change is planned.
- `api/tests/test_api.py` and API-scoped integration-test configuration/evidence: characterize the existing contract and validate the externally issued token.
- No production code, tests, or configuration in `auth/` or `web/`; no changes to general documentation sections for those components.

## Decisions

### Keep production authentication behavior unchanged

**Decision:** Treat this as an integration-validation change. Preserve `verified_identity` and the current owner authorization boundary; add no fallback keys, alternate algorithms, relaxed claims, or issuer-specific exceptions.

**Alternatives considered:** Changing API validation to accommodate a token before confirming the issuer contract could silently broaden acceptance and violate the documented baseline. Rejected; if the real issuer is incompatible, record the mismatch and obtain an explicit contract decision before changing behavior.

### Use an externally issued token for integration evidence

**Decision:** Run the integration check with a short-lived token obtained for a designated non-production test identity from TrackingProcessor v1.0. Supply the token and the API verification key only through protected runtime environment configuration; configure the matching test identity in an isolated API test database. Do not generate or commit a substitute token for this integration check.

**Alternatives considered:** Locally signing a token with the test key is appropriate for deterministic characterization, and existing tests already do so, but cannot establish compatibility with the external issuer. Calling or modifying issuer implementation from `api/` would exceed the approved component boundary. Keep local-token tests as the fast baseline and use the issuer-produced token only for the integration check.

### Separate deterministic characterization from environment-dependent validation

**Decision:** First run the existing API tests for accepted identity, invalid/expired/malformed claims, missing `SECRET`, and owner mismatch. Keep those deterministic tests independent of issuer availability. Run the external-token integration check as a separately identifiable validation using the approved non-production environment.

**Alternatives considered:** Making all API tests require a live issuer would make local validation unreliable and conceal whether a failure is in existing API behavior or external integration. A fully mocked issuer would not meet the integration requirement.

### Record evidence without sensitive values

**Decision:** Record the issuer/version, non-production environment identifier, validation result, and whether `SECRET` was configured; never print, serialize, or attach its value or the bearer token. A missing issuer/environment prerequisite is recorded as blocked or not run, not as a passing integration check.

**Alternatives considered:** Capturing request headers or environment dumps might simplify troubleshooting but creates an avoidable credential exposure risk; rejected.

## Incremental Strategy

1. Before adding any integration-specific test or changing critical behavior, run the existing characterization tests from `api/`:
   `python -m pytest tests/test_api.py -k "lists_seeded_tasks or empty_owner_query_uses_authenticated_identity or rejects_tasks_for_different_owner or rejects_malformed_bearer_header or rejects_invalid_token or rejects_token_with_invalid_issuer_or_audience or rejects_token_with_invalid_signature or rejects_token_missing_required_claim or rejects_expired_token or requires_configured_jwt_secret"`.
   Preserve the current expected statuses, response details, and task ownership behavior.
2. Add the API-scoped integration validation using a temporary database, a designated test identity, an externally issued short-lived token, and environment-provided `SECRET`. Keep issuer access and secret provisioning outside application code.
3. Run the deterministic API tests, then run the integration validation explicitly against the approved non-production issuer/environment. If prerequisites are absent, report the integration evidence as not run or blocked rather than treating a skip as success.
4. Review the resulting evidence for accidental token or secret disclosure before sharing it. Only report integration acceptance when the external-token route and owner-mismatch checks have actually completed.

## Tests Before Critical Behavior Changes

No behavior change is proposed. If later evidence demonstrates that a behavior change is necessary, first preserve the current expectations in API characterization tests: successful access with a compatible token; HTTP 401 and the existing detail for missing, malformed, expired, wrong-issuer, wrong-audience, or incomplete-claim tokens; the current configuration failure when `SECRET` is absent/undersized; defaulting an omitted/empty task owner to the verified username; and HTTP 403 with the existing detail for a different owner. Any proposed deviation must be reconciled with `docs/ENDPOINTS.md` and the approved spec before implementation.

## Risks / Trade-offs

- [The external issuer or non-production integration environment may be unavailable] → Keep deterministic API tests runnable independently; report the external check as blocked/not run and do not claim H-API-01/H-API-02 integration evidence.
- [A real token or shared HMAC key could leak through test output or artifacts] → Inject values only through protected environment configuration, suppress request/environment dumps, use a short-lived test token, and review evidence before sharing.
- [The integration identity may not match the test database fixture] → Use a dedicated test identity and isolated database data configured for its username; never weaken owner checks to make the scenario pass.
- [Issuer behavior may differ from the documented token contract] → Capture only non-sensitive failure metadata and stop for an explicit contract decision; do not broaden API token acceptance as an integration workaround.
- [Running an integration test can depend on external state and network availability] → Keep it separately invoked from the fast deterministic suite and identify its target environment in the results.

## Rollback

This validation plan changes no production data, schema, or API behavior, so no application or database rollback is required. If the integration-test or environment wiring is unsafe or unstable, disable/revert only that API-scoped test/configuration and retain the existing deterministic tests and production behavior. If a token or key is exposed, stop validation and rotate/revoke it through the authorized secret-management process; do not preserve the leaked value in logs or evidence.

## Open Questions

- Which approved non-production TrackingProcessor v1.0 environment and designated test identity will supply the short-lived integration token? This must be established before executing the integration check; the test must not substitute a locally generated token.
