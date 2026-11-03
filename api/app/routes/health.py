from __future__ import annotations

import logging
import os

import urllib3
from fastapi import APIRouter

from app.constants import (
    BACKEND_UNAVAILABLE_BODY,
    DEFAULT_HEALTH_URL,
    HEALTH_TIMEOUT_SECONDS,
    HEALTH_URL_ENV,
)
from app.dependencies import IdentityDep
from app.schemas import HealthOut, Identity

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.get("/backend-health", response_model=HealthOut)
def backend_health(identity: Identity = IdentityDep) -> HealthOut:
    url = os.getenv(HEALTH_URL_ENV, DEFAULT_HEALTH_URL)
    try:
        response = urllib3.PoolManager().request("GET", url, timeout=HEALTH_TIMEOUT_SECONDS)
        return HealthOut(requestedBy=identity.username, status=response.status, body=response.data.decode("utf-8"))
    except (urllib3.exceptions.HTTPError, OSError, ValueError):
        logger.exception("Backend health check failed for %s", url)
        return HealthOut(requestedBy=identity.username, status=0, body=BACKEND_UNAVAILABLE_BODY)
