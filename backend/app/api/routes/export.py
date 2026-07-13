from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from app.api.deps import ExportServiceDep

router = APIRouter(prefix="/api/books/{book_id}/export", tags=["export"])


@router.post("/epub")
def export_epub(book_id: str, service: ExportServiceDep) -> Response:
    data, filename = service.export_epub(book_id)
    return Response(
        content=data,
        media_type="application/epub+zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/pdf")
def export_pdf(book_id: str, service: ExportServiceDep) -> Response:
    data, filename = service.export_pdf(book_id)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
