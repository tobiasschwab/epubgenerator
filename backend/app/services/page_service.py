from __future__ import annotations

from app.models import Page, PageCreate, PageUpdate
from app.repositories import BookRepository
from app.services.tree import clamp_position, find_chapter, find_page


class PageService:
    def __init__(self, repo: BookRepository) -> None:
        self._repo = repo

    def list(self, book_id: str, chapter_id: str) -> list[Page]:
        chapter = find_chapter(self._repo.get(book_id), chapter_id)
        return chapter.pages

    def get(self, book_id: str, chapter_id: str, page_id: str) -> Page:
        chapter = find_chapter(self._repo.get(book_id), chapter_id)
        return find_page(chapter, page_id)

    def create(self, book_id: str, chapter_id: str, data: PageCreate) -> Page:
        book = self._repo.get(book_id)
        chapter = find_chapter(book, chapter_id)
        page = Page(text=data.text)
        chapter.pages.append(page)
        self._repo.save(book)
        return page

    def update(self, book_id: str, chapter_id: str, page_id: str, data: PageUpdate) -> Page:
        book = self._repo.get(book_id)
        chapter = find_chapter(book, chapter_id)
        page = find_page(chapter, page_id)

        # Entfernte Medien physisch aufräumen (Orphans vermeiden).
        new_ids = {ref.id for ref in data.media}
        for ref in page.media:
            if ref.id not in new_ids:
                self._repo.delete_media_file(book_id, ref.id)

        page.text = data.text
        page.media = data.media
        self._repo.save(book)
        return page

    def delete(self, book_id: str, chapter_id: str, page_id: str) -> None:
        book = self._repo.get(book_id)
        chapter = find_chapter(book, chapter_id)
        page = find_page(chapter, page_id)
        chapter.pages.remove(page)
        self._repo.save(book)

    def move(
        self,
        book_id: str,
        chapter_id: str,
        page_id: str,
        position: int,
        target_chapter_id: str | None,
    ) -> Page:
        """Seite verschieben — innerhalb oder kapitelübergreifend."""
        book = self._repo.get(book_id)
        source = find_chapter(book, chapter_id)
        page = find_page(source, page_id)
        target = find_chapter(book, target_chapter_id) if target_chapter_id else source

        source.pages.remove(page)
        pos = clamp_position(position, len(target.pages))
        target.pages.insert(pos, page)
        self._repo.save(book)
        return page
