from __future__ import annotations

from app.models import Book, Chapter, ChapterCreate, ChapterUpdate
from app.repositories import BookRepository
from app.services.tree import clamp_position, find_chapter


class ChapterService:
    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    def list(self, book_id: str) -> list[Chapter]:
        return self._repo.get(book_id).chapters

    def get(self, book_id: str, chapter_id: str) -> Chapter:
        return find_chapter(self._repo.get(book_id), chapter_id)

    def create(self, book_id: str, data: ChapterCreate) -> Chapter:
        book = self._repo.get(book_id)
        chapter = Chapter(title=data.title)
        book.chapters.append(chapter)
        self._repo.save(book)
        return chapter

    def update(self, book_id: str, chapter_id: str, data: ChapterUpdate) -> Chapter:
        book = self._repo.get(book_id)
        chapter = find_chapter(book, chapter_id)
        chapter.title = data.title
        self._repo.save(book)
        return chapter

    def delete(self, book_id: str, chapter_id: str) -> None:
        book = self._repo.get(book_id)
        chapter = find_chapter(book, chapter_id)
        book.chapters.remove(chapter)
        self._repo.save(book)

    def move(self, book_id: str, chapter_id: str, position: int) -> Book:
        book = self._repo.get(book_id)
        chapter = find_chapter(book, chapter_id)
        book.chapters.remove(chapter)
        target = clamp_position(position, len(book.chapters))
        book.chapters.insert(target, chapter)
        return self._repo.save(book)
