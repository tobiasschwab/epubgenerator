from __future__ import annotations

from app.models import Book, BookCreate, BookSummary, BookUpdate
from app.repositories import BookRepository


class BookService:
    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    def list(self) -> list[BookSummary]:
        return self._repo.list_summaries()

    def get(self, book_id: str) -> Book:
        return self._repo.get(book_id)

    def create(self, data: BookCreate) -> Book:
        book = Book(title=data.title, description=data.description)
        return self._repo.save(book)

    def update(self, book_id: str, data: BookUpdate) -> Book:
        book = self._repo.get(book_id)
        book.title = data.title
        book.description = data.description
        return self._repo.save(book)

    def delete(self, book_id: str) -> None:
        self._repo.delete(book_id)
