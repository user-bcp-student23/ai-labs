from fastapi import HTTPException

from app.schemas import Identity

OWNER_MISMATCH_DETAIL = "Owner does not match authenticated identity"


def resolve_authorized_owner(identity: Identity, requested_owner: str | None) -> str:
    if requested_owner is not None and requested_owner != identity.username:
        raise HTTPException(status_code=403, detail=OWNER_MISMATCH_DETAIL)
    return identity.username
