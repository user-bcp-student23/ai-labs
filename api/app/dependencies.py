from __future__ import annotations

from fastapi import Depends, HTTPException, Header, Request

from app.constants import TOKEN_PREFIX
from app.repository import TaskRepository
from app.schemas import Identity
from app.security import InvalidTokenError, verify_token


def legacy_identity(request: Request, authorization: str = Header(default="")) -> Identity:
    token = authorization.removeprefix(TOKEN_PREFIX)
    try:
        claims = verify_token(token, request.app.state.token_secret)
    except InvalidTokenError as error:
        raise HTTPException(status_code=401, detail="Invalid token") from error
    return Identity(username=claims["sub"], role=claims["role"])


def get_repository(request: Request) -> TaskRepository:
    return request.app.state.repository


def get_upload_dir(request: Request) -> str:
    return request.app.state.upload_dir


IdentityDep = Depends(legacy_identity)
RepositoryDep = Depends(get_repository)
UploadDirDep = Depends(get_upload_dir)
