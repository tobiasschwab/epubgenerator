from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import BookServiceDep
from app.models import Book, BookCreate, BookSummary, BookUpdate

router = APIRouter(prefix="/api/books", tags=["books"])


@router.get("", response_model=list[BookSummary])
def list_books(service: BookServiceDep) -> list[BookSummary]:
    return service.list()


@router.post("", response_model=Book, status_code=status.HTTP_201_CREATED)
def create_book(data: BookCreate, service: BookServiceDep) -> Book:
    return service.create(data)


@router.get("/{book_id}", response_model=Book)
def get_book(book_id: str, service: BookServiceDep) -> Book:
    return service.get(book_id)


@router.put("/{book_id}", response_model=Book)
def update_book(book_id: str, data: BookUpdate, service: BookServiceDep) -> Book:
    return service.update(book_id, data)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: str, service: BookServiceDep) -> None:
    service.delete(book_id)
