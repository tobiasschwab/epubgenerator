from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from app.config import Settings
from app.errors import NotFoundError
from app.models import Book, BookSummary


class BookRepository:
    """Dateibasierte Persistenz: ein book.json pro Buch, Medien als eigene Dateien.

    Kapselt sämtliches Datei-I/O. Services rufen niemals direkt open()/os.*.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._books_dir = settings.books_dir

    # --- Pfade -----------------------------------------------------------
    def book_dir(self, book_id: str) -> Path:
        return self._books_dir / book_id

    def _book_json(self, book_id: str) -> Path:
        return self.book_dir(book_id) / "book.json"

    def media_dir(self, book_id: str) -> Path:
        return self.book_dir(book_id) / "media"

    def export_dir(self, book_id: str) -> Path:
        return self.book_dir(book_id) / "export"

    def media_path(self, book_id: str, media_id: str, ext: str) -> Path:
        return self.media_dir(book_id) / f"{media_id}{ext}"

    def find_media_file(self, book_id: str, media_id: str) -> Path | None:
        media_dir = self.media_dir(book_id)
        if not media_dir.exists():
            return None
        for entry in media_dir.iterdir():
            if entry.stem == media_id and entry.is_file():
                return entry
        return None

    def iter_media_files(self, book_id: str) -> list[Path]:
        media_dir = self.media_dir(book_id)
        if not media_dir.exists():
            return []
        return [entry for entry in media_dir.iterdir() if entry.is_file()]

    def list_book_ids(self) -> list[str]:
        if not self._books_dir.exists():
            return []
        return [
            entry.name
            for entry in self._books_dir.iterdir()
            if (entry / "book.json").is_file()
        ]

    # --- CRUD ------------------------------------------------------------
    def exists(self, book_id: str) -> bool:
        return self._book_json(book_id).exists()

    def list_summaries(self) -> list[BookSummary]:
        summaries: list[BookSummary] = []
        if not self._books_dir.exists():
            return summaries
        for entry in sorted(self._books_dir.iterdir()):
            book_json = entry / "book.json"
            if not book_json.is_file():
                continue
            try:
                book = Book.model_validate_json(book_json.read_text(encoding="utf-8"))
            except Exception:
                # Korruptes oder unlesbares Buch überspringen statt Liste zu brechen.
                continue
            summaries.append(
                BookSummary(
                    id=book.id,
                    title=book.title,
                    description=book.description,
                    chapter_count=len(book.chapters),
                )
            )
        return summaries

    def get(self, book_id: str) -> Book:
        path = self._book_json(book_id)
        if not path.exists():
            raise NotFoundError(f"Buch {book_id} nicht gefunden")
        return Book.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, book: Book) -> Book:
        book_dir = self.book_dir(book.id)
        book_dir.mkdir(parents=True, exist_ok=True)
        self.media_dir(book.id).mkdir(exist_ok=True)
        self._atomic_write(self._book_json(book.id), book.model_dump_json(indent=2))
        return book

    def delete(self, book_id: str) -> None:
        book_dir = self.book_dir(book_id)
        if not book_dir.exists():
            raise NotFoundError(f"Buch {book_id} nicht gefunden")
        shutil.rmtree(book_dir)

    # --- Medien ----------------------------------------------------------
    def write_media(self, book_id: str, media_id: str, ext: str, data: bytes) -> Path:
        self.media_dir(book_id).mkdir(parents=True, exist_ok=True)
        path = self.media_path(book_id, media_id, ext)
        self._atomic_write_bytes(path, data)
        return path

    def delete_media_file(self, book_id: str, media_id: str) -> None:
        path = self.find_media_file(book_id, media_id)
        if path is not None:
            path.unlink(missing_ok=True)

    def write_export(self, book_id: str, filename: str, data: bytes) -> Path:
        export_dir = self.export_dir(book_id)
        export_dir.mkdir(parents=True, exist_ok=True)
        path = export_dir / filename
        self._atomic_write_bytes(path, data)
        return path

    # --- Atomare Schreibvorgänge ----------------------------------------
    @staticmethod
    def _atomic_write(path: Path, text: str) -> None:
        BookRepository._atomic_write_bytes(path, text.encode("utf-8"))

    @staticmethod
    def _atomic_write_bytes(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
