# Proposal

## Why

GitHub Issue [#28 — HU-01](https://github.com/user-bcp-student23/ai-labs/issues/28) reports that API-side JWT validation and task ownership controls are implemented locally, but their integration with the external TrackingProcessor v1.0 issuer and the deployment configuration of `SECRET` remain unverified. Confirming this integration matters because protected API access must reflect the identity issued by the central authentication service without weakening the documented authorization boundary or exposing credentials.

## What Changes

- Validate the API's documented JWT contract with a token issued by TrackingProcessor v1.0 and verify that the protected API identifies the expected `username`.
- Verify that expired tokens, incorrect issuer or audience, and tokens missing required claims do not authorize API access.
- Verify that requesting tasks for an owner different from the authenticated identity continues to return HTTP 403.
- Confirm that the API integration environment receives `SECRET` from its environment and that test results and evidence do not disclose its value, tokens, or credentials.
- Preserve the existing API and authentication endpoint contracts; this change adds integration evidence and does not request a behavior change.

## Scope

- Component: `api/` only, covering H-API-01 and the dependent H-API-02 from Issue #28.
- Observable integration behavior for a compatible externally issued token, rejected tokens, and a cross-owner task request.
- Non-sensitive evidence identifying the issuer/version and validation environment, plus confirmation that `SECRET` is configured through the environment.

## Out of Scope

- Changes to `auth/`, the `POST /auth/login` implementation, or the external issuer.
- Changes to JWT claims, algorithms, endpoint formats, successful response payloads, or authorization behavior.
- Changes to `web/`, other API features, or general documentation sections for other components.
- Recording or attaching secret values, tokens, or credentials.
- Technical implementation design and implementation task breakdown at this proposal stage.

## Behavior to Preserve

- The API does not issue tokens. Protected routes require a Bearer token and validate the documented HS256 contract: `iss=ISS`, `aud=CLAIM`, `exp`, `username`, and `role`; `SECRET` is supplied through the environment and must be at least 32 bytes.
- An absent or invalid token continues to return HTTP 401 with `{"detail":"Invalid token"}`.
- `GET /api/tasks` with `owner` omitted or empty continues to use the verified JWT username and return HTTP 200 with that identity's tasks.
- A request for tasks belonging to a different owner continues to return HTTP 403 with `{"detail":"Owner does not match authenticated identity"}`.
- These are existing contracts in [docs/ENDPOINTS.md](../../../docs/ENDPOINTS.md); Issue #28 does not request changing them.

## Capabilities

### New Capabilities

- `api-jwt-integration`: Verification of externally issued JWT compatibility, authenticated identity, and owner-bound task access in the API integration environment.

### Modified Capabilities

- None. No existing OpenSpec capability specs are present, and the Issue validates existing documented behavior rather than changing the contract.

## Impact

- API behavior under integration with TrackingProcessor v1.0 and the API integration environment's `SECRET` configuration.
- Observable scenarios are limited to the API contract described in [docs/ENDPOINTS.md](../../../docs/ENDPOINTS.md); implementation details are intentionally deferred.
- No dependencies or behavior changes are proposed for `auth/` or `web/`.
