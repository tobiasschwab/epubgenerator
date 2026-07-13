"""Hilfsfunktionen zum Navigieren im Buch-Baum."""

from __future__ import annotations

from app.errors import NotFoundError
from app.models import Book, Chapter, Page


def find_chapter(book: Book, chapter_id: str) -> Chapter:
    for chapter in book.chapters:
        if chapter.id == chapter_id:
            return chapter
    raise NotFoundError(f"Kapitel {chapter_id} nicht gefunden")


def find_page(chapter: Chapter, page_id: str) -> Page:
    for page in chapter.pages:
        if page.id == page_id:
            return page
    raise NotFoundError(f"Seite {page_id} nicht gefunden")


def clamp_position(position: int, length: int) -> int:
    """Zielposition auf gültigen Bereich [0, length] begrenzen."""
    if position < 0:
        return 0
    return min(position, length)
