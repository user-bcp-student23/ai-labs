import os

import jwt
from fastapi import Header, HTTPException
from jwt import InvalidTokenError
from pydantic import ValidationError

from app.schemas import Identity

JWT_SECRET_ENV_VAR = "SECRET"
JWT_ISSUER = "ISS"
JWT_AUDIENCE = "CLAIM"
JWT_ALGORITHM = "HS256"
MINIMUM_HMAC_KEY_BYTES = 32
REQUIRED_JWT_CLAIMS = ("exp", "iss", "aud", "username", "role")
INVALID_TOKEN_DETAIL = "Invalid token"
JWT_CONFIGURATION_ERROR = "JWT verification key is not configured correctly"


def verified_identity(authorization: str = Header(default="")) -> Identity:
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail=INVALID_TOKEN_DETAIL)

    secret = os.getenv(JWT_SECRET_ENV_VAR)
    if secret is None or len(secret.encode("utf-8")) < MINIMUM_HMAC_KEY_BYTES:
        raise RuntimeError(JWT_CONFIGURATION_ERROR)

    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"require": list(REQUIRED_JWT_CLAIMS)},
        )
        return Identity.model_validate(claims)
    except (InvalidTokenError, ValidationError) as error:
        raise HTTPException(status_code=401, detail=INVALID_TOKEN_DETAIL) from error
