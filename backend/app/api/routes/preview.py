from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.api.deps import ExportServiceDep

router = APIRouter(prefix="/api/books/{book_id}/preview", tags=["preview"])


@router.get("", response_class=HTMLResponse)
def preview(
    book_id: str, service: ExportServiceDep, chapter_id: str | None = None
) -> HTMLResponse:
    html = service.preview_html(book_id, chapter_id)
    return HTMLResponse(content=html)
