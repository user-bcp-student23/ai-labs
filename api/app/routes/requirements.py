from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.dependencies import IdentityDep, UploadDirDep
from app.schemas import Identity, UploadOut

router = APIRouter(prefix="/api")


@router.post("/requirements", status_code=201, response_model=UploadOut)
async def upload_requirement(
    file: UploadFile = File(...),
    identity: Identity = IdentityDep,
    upload_dir: str = UploadDirDep,
) -> UploadOut:
    target = Path(upload_dir) / str(file.filename)
    content = await file.read()
    target.write_bytes(content)
    return UploadOut(owner=identity.username, fileName=file.filename, storedAt=str(target), size=len(content))
