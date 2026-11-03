from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from app.constants import (
    TOKEN_AUDIENCE,
    TOKEN_CLOCK_SKEW_SECONDS,
    TOKEN_ISSUER,
    TOKEN_SECRET_ENV,
    TOKEN_SEPARATOR,
)


class InvalidTokenError(ValueError):
    """El token no pudo verificarse."""


def load_token_secret() -> str:
    secret = os.getenv(TOKEN_SECRET_ENV, "")
    if not secret:
        raise RuntimeError(f"{TOKEN_SECRET_ENV} debe estar definido")
    return secret


def sign_claims(claims: Any, secret: str) -> str:
    payload_part = _b64url_encode(json.dumps(claims, separators=(",", ":")).encode("utf-8"))
    return payload_part + TOKEN_SEPARATOR + _signature(payload_part, secret)


def verify_token(token: str, secret: str, now: float | None = None) -> dict[str, Any]:
    payload_part, separator, given_signature = token.partition(TOKEN_SEPARATOR)
    if not separator or not _signature_matches(payload_part, given_signature, secret):
        raise InvalidTokenError("firma invalida")
    claims = _decode_claims(payload_part)
    _check_identity(claims)
    _check_expiry(claims, time.time() if now is None else now)
    return claims


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def _signature(payload_part: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload_part.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(digest)


def _signature_matches(payload_part: str, given_signature: str, secret: str) -> bool:
    expected = _signature(payload_part, secret)
    return hmac.compare_digest(expected.encode("utf-8"), given_signature.encode("utf-8"))


def _decode_claims(payload_part: str) -> dict[str, Any]:
    try:
        claims = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    except ValueError as error:
        raise InvalidTokenError("payload malformado") from error
    if not isinstance(claims, dict):
        raise InvalidTokenError("payload malformado")
    return claims


def _check_identity(claims: dict[str, Any]) -> None:
    if claims.get("iss") != TOKEN_ISSUER or claims.get("aud") != TOKEN_AUDIENCE:
        raise InvalidTokenError("emisor o audiencia no valido")
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise InvalidTokenError("sujeto ausente")
    if not isinstance(claims.get("role"), str):
        raise InvalidTokenError("rol ausente")


def _check_expiry(claims: dict[str, Any], now: float) -> None:
    expires_at = claims.get("exp")
    if not isinstance(expires_at, int) or expires_at < now - TOKEN_CLOCK_SKEW_SECONDS:
        raise InvalidTokenError("token expirado o sin exp")
