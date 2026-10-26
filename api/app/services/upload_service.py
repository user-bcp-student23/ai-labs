from itertools import count
from pathlib import Path
from typing import Iterator

from fastapi import HTTPException, UploadFile

ALLOWED_UPLOAD_EXTENSIONS = frozenset({".txt", ".pdf"})
MAX_UPLOAD_BYTES = 4
UPLOAD_OVERFLOW_PROBE_BYTES = 1
INVALID_UPLOAD_DETAIL = "Invalid upload"
INVALID_UPLOAD_STATUS = 415
OVERSIZED_UPLOAD_STATUS = 413


async def store_upload(upload: UploadFile, upload_directory: Path) -> tuple[Path, int]:
    filename = _normalized_filename(upload.filename)
    if Path(filename).suffix.lower() not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=INVALID_UPLOAD_STATUS, detail=INVALID_UPLOAD_DETAIL)

    content = await upload.read(MAX_UPLOAD_BYTES + UPLOAD_OVERFLOW_PROBE_BYTES)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=OVERSIZED_UPLOAD_STATUS, detail=INVALID_UPLOAD_DETAIL)

    directory = upload_directory.resolve()
    for candidate in _filename_candidates(directory, filename):
        try:
            with candidate.open("xb") as destination:
                destination.write(content)
            return candidate, len(content)
        except FileExistsError:
            continue

def _normalized_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status_code=INVALID_UPLOAD_STATUS, detail=INVALID_UPLOAD_DETAIL)
    return filename.replace("\\", "/").rsplit("/", maxsplit=1)[-1]


def _filename_candidates(directory: Path, filename: str) -> Iterator[Path]:
    original = Path(filename)
    for suffix_number in count():
        candidate_name = (
            filename
            if suffix_number == 0
            else f"{original.stem}_{suffix_number}{original.suffix}"
        )
        candidate = directory / candidate_name
        if candidate.parent.resolve() != directory:
            raise HTTPException(
                status_code=INVALID_UPLOAD_STATUS,
                detail=INVALID_UPLOAD_DETAIL,
            )
        yield candidate
