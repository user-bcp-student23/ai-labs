# Spec Delta

## Purpose

This capability verifies that the API accepts identities from the documented external JWT issuer while preserving authenticated task ownership and protecting secret material during integration validation.

## ADDED Requirements

### Requirement: Accept compatible tokens from the external issuer

The API SHALL accept a non-expired Bearer token issued by TrackingProcessor v1.0 when it satisfies the documented HS256 contract and the API integration environment is configured with `SECRET`.

#### Scenario: External identity accesses its tasks

- **WHEN** a request to `GET /api/tasks` omits `owner` and carries a compatible token issued by TrackingProcessor v1.0 for a username with at least one task
- **THEN** the API responds with HTTP 200 and the returned tasks identify that verified username as their owner

### Requirement: Reject tokens that do not satisfy the documented contract

The API SHALL deny access to a protected route when a token is expired, has an incorrect issuer or audience, or is missing any required claim: `exp`, `iss`, `aud`, `username`, or `role`.

#### Scenario: Expired external token is rejected

- **WHEN** a request to `GET /api/tasks` carries an expired token
- **THEN** the API responds with HTTP 401 and `{"detail":"Invalid token"}`

#### Scenario: Token with incorrect issuer or audience is rejected

- **WHEN** a request to `GET /api/tasks` carries a token whose issuer or audience differs from the documented contract
- **THEN** the API responds with HTTP 401 and `{"detail":"Invalid token"}`

#### Scenario: Token missing a required claim is rejected

- **WHEN** a request to `GET /api/tasks` carries a token missing `exp`, `iss`, `aud`, `username`, or `role`
- **THEN** the API responds with HTTP 401 and `{"detail":"Invalid token"}`

### Requirement: Enforce task ownership for the verified identity

The API SHALL restrict task requests to the username established by the verified token and preserve the documented response for a different requested owner.

#### Scenario: Different task owner is forbidden

- **WHEN** a request to `GET /api/tasks` specifies an `owner` different from the verified token's username
- **THEN** the API responds with HTTP 403 and `{"detail":"Owner does not match authenticated identity"}`

### Requirement: Keep verification secrets out of integration evidence

The API integration environment SHALL provide `SECRET` through its environment with at least 32 bytes, and validation evidence SHALL confirm its configuration without recording or disclosing its value, tokens, or credentials.

#### Scenario: Secret configuration is evidenced without disclosure

- **WHEN** integration validation results are recorded
- **THEN** the evidence identifies that `SECRET` is configured in the environment and contains no secret value, token, or credential
