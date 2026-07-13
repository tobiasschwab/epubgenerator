from __future__ import annotations

from app.models import Book
from app.repositories import BookRepository
from app.rendering import epub as epub_render
from app.rendering import pdf as pdf_render
from app.rendering.html import render_book_document
from app.services.media_service import MediaService


class ExportService:
    def __init__(self, repo: BookRepository, media: MediaService) -> None:
        self._repo = repo
        self._media = media

    def preview_html(self, book_id: str, chapter_id: str | None = None) -> str:
        book = self._repo.get(book_id)

        def resolver(ref) -> str:
            return f"/api/books/{book_id}/media/{ref.id}"

        return render_book_document(book, resolver, chapter_id=chapter_id)

    def export_epub(self, book_id: str) -> tuple[bytes, str]:
        book = self._repo.get(book_id)
        data = epub_render.build_epub(book, self._media.loader(book_id))
        filename = self._safe_filename(book, "epub")
        self._repo.write_export(book_id, "book.epub", data)
        return data, filename

    def export_pdf(self, book_id: str) -> tuple[bytes, str]:
        book = self._repo.get(book_id)
        base_url = str(self._repo.book_dir(book_id).resolve())
        data = pdf_render.build_pdf(book, self._media.path_resolver(book_id), base_url)
        filename = self._safe_filename(book, "pdf")
        self._repo.write_export(book_id, "book.pdf", data)
        return data, filename

    @staticmethod
    def _safe_filename(book: Book, ext: str) -> str:
        base = "".join(
            c if c.isalnum() or c in " -_" else "_" for c in (book.title or "book")
        ).strip()
        base = base.replace(" ", "_") or "book"
        return f"{base}.{ext}"
