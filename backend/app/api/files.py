from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User
from backend.app.security import require_admin
from backend.app.services.audit_service import record_event
from backend.app.services.file_service import (
    get_file,
    list_files,
    save_upload,
)

router = APIRouter(prefix="/files", tags=["Managed Files"])


@router.get("")
def browse(
    path: str = "",
    user: User = Depends(require_admin),
):
    return {"path": path, "items": list_files(path)}


@router.post("/upload")
async def upload(
    path: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    if not file.filename or Path(file.filename).name != file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    relative_path = str(Path(path) / file.filename) if path else file.filename

    result = await save_upload(relative_path, file)

    record_event(
        db,
        actor=user.email,
        action="file_uploaded",
        resource=relative_path,
    )

    return result


@router.get("/download")
def download(
    path: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    file_path = get_file(path)

    record_event(
        db,
        actor=user.email,
        action="file_downloaded",
        resource=path,
    )

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream",
    )
