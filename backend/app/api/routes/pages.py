from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import PageServiceDep
from app.models import MovePage, Page, PageCreate, PageUpdate

router = APIRouter(
    prefix="/api/books/{book_id}/chapters/{chapter_id}/pages", tags=["pages"]
)


@router.get("", response_model=list[Page])
def list_pages(book_id: str, chapter_id: str, service: PageServiceDep) -> list[Page]:
    return service.list(book_id, chapter_id)


@router.post("", response_model=Page, status_code=status.HTTP_201_CREATED)
def create_page(
    book_id: str, chapter_id: str, data: PageCreate, service: PageServiceDep
) -> Page:
    return service.create(book_id, chapter_id, data)


@router.get("/{page_id}", response_model=Page)
def get_page(book_id: str, chapter_id: str, page_id: str, service: PageServiceDep) -> Page:
    return service.get(book_id, chapter_id, page_id)


@router.put("/{page_id}", response_model=Page)
def update_page(
    book_id: str,
    chapter_id: str,
    page_id: str,
    data: PageUpdate,
    service: PageServiceDep,
) -> Page:
    return service.update(book_id, chapter_id, page_id, data)


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_page(
    book_id: str, chapter_id: str, page_id: str, service: PageServiceDep
) -> None:
    service.delete(book_id, chapter_id, page_id)


@router.post("/{page_id}/move", response_model=Page)
def move_page(
    book_id: str,
    chapter_id: str,
    page_id: str,
    data: MovePage,
    service: PageServiceDep,
) -> Page:
    return service.move(
        book_id, chapter_id, page_id, data.position, data.target_chapter_id
    )
