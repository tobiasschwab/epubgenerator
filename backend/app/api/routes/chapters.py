from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import ChapterServiceDep
from app.models import Book, Chapter, ChapterCreate, ChapterUpdate, MovePosition

router = APIRouter(prefix="/api/books/{book_id}/chapters", tags=["chapters"])


@router.get("", response_model=list[Chapter])
def list_chapters(book_id: str, service: ChapterServiceDep) -> list[Chapter]:
    return service.list(book_id)


@router.post("", response_model=Chapter, status_code=status.HTTP_201_CREATED)
def create_chapter(book_id: str, data: ChapterCreate, service: ChapterServiceDep) -> Chapter:
    return service.create(book_id, data)


@router.get("/{chapter_id}", response_model=Chapter)
def get_chapter(book_id: str, chapter_id: str, service: ChapterServiceDep) -> Chapter:
    return service.get(book_id, chapter_id)


@router.put("/{chapter_id}", response_model=Chapter)
def update_chapter(
    book_id: str, chapter_id: str, data: ChapterUpdate, service: ChapterServiceDep
) -> Chapter:
    return service.update(book_id, chapter_id, data)


@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(book_id: str, chapter_id: str, service: ChapterServiceDep) -> None:
    service.delete(book_id, chapter_id)


@router.post("/{chapter_id}/move", response_model=Book)
def move_chapter(
    book_id: str, chapter_id: str, data: MovePosition, service: ChapterServiceDep
) -> Book:
    return service.move(book_id, chapter_id, data.position)
