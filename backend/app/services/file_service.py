from pathlib import Path

from fastapi import HTTPException, UploadFile

from backend.app.config import settings


ROOT = Path(settings.allowed_file_root).resolve()
ROOT.mkdir(parents=True, exist_ok=True)


def resolve_managed_path(relative_path: str = "") -> Path:
    requested = (ROOT / relative_path).resolve()

    if requested != ROOT and ROOT not in requested.parents:
        raise HTTPException(status_code=403, detail="Path is outside managed storage")

    current = ROOT
    for part in Path(relative_path).parts:
        if part in ("..", "."):
            raise HTTPException(status_code=400, detail="Invalid path")
        current = current / part
        if current.is_symlink():
            raise HTTPException(status_code=403, detail="Symbolic links are not allowed")

    return requested


def list_files(relative_path: str = "") -> list[dict]:
    directory = resolve_managed_path(relative_path)

    if not directory.exists() or not directory.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    results = []

    for item in directory.iterdir():
        if item.is_symlink():
            continue

        results.append({
            "name": item.name,
            "is_directory": item.is_dir(),
            "size": item.stat().st_size if item.is_file() else None,
        })

    return results


async def save_upload(relative_path: str, upload: UploadFile) -> dict:
    destination = resolve_managed_path(relative_path)

    if destination.exists():
        raise HTTPException(status_code=409, detail="File already exists")

    destination.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    temporary = destination.with_name(destination.name + ".uploading")

    try:
        with temporary.open("xb") as output:
            while chunk := await upload.read(1024 * 1024):
                total += len(chunk)

                if total > settings.max_upload_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail="Upload exceeds configured size limit",
                    )

                output.write(chunk)

        temporary.rename(destination)

    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    finally:
        await upload.close()

    return {"filename": destination.name, "size": total}


def get_file(relative_path: str) -> Path:
    file_path = resolve_managed_path(relative_path)

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return file_path
