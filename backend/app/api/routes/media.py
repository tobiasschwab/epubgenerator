from __future__ import annotations

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import MediaServiceDep
from app.models import MediaRef

router = APIRouter(prefix="/api/books/{book_id}/media", tags=["media"])


@router.post("", response_model=MediaRef)
async def upload_media(
    book_id: str, service: MediaServiceDep, file: UploadFile = File(...)
) -> MediaRef:
    data = await file.read()
    return service.upload(
        book_id, file.filename or "upload", file.content_type or "", data
    )


@router.get("/{media_id}")
def get_media(book_id: str, media_id: str, service: MediaServiceDep) -> FileResponse:
    path = service.resolve_path(book_id, media_id)
    return FileResponse(path, media_type=service.guess_media_type(path))


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(book_id: str, media_id: str, service: MediaServiceDep) -> None:
    # Datei löschen (z. B. verworfene KI-Generierung). Idempotent.
    service.delete(book_id, media_id)
