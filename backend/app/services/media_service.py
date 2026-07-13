from __future__ import annotations

import mimetypes
import os
import time
from pathlib import Path

from app.config import Settings
from app.errors import NotFoundError, ValidationError
from app.models import MediaKind, MediaRef
from app.repositories import BookRepository

_IMAGE_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}
_AUDIO_MIME = {
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/webm": ".webm",
}


class MediaService:
    def __init__(self, repo: BookRepository, settings: Settings) -> None:
        self._repo = repo
        self._settings = settings

    def upload(self, book_id: str, filename: str, mime: str, data: bytes) -> MediaRef:
        if not self._repo.exists(book_id):
            raise NotFoundError(f"Buch {book_id} nicht gefunden")
        if len(data) > self._settings.max_upload_bytes:
            raise ValidationError("Datei überschreitet die maximale Uploadgröße")

        mime = (mime or "").lower()
        if mime in _IMAGE_MIME:
            kind = MediaKind.image
            ext = _IMAGE_MIME[mime]
        elif mime in _AUDIO_MIME:
            kind = MediaKind.audio
            ext = _AUDIO_MIME[mime]
        else:
            raise ValidationError(f"Nicht unterstützter MIME-Typ: {mime}")

        ref = MediaRef(filename=filename or f"media{ext}", mime=mime, kind=kind)
        self._repo.write_media(book_id, ref.id, ext, data)
        return ref

    def store_generated(
        self, book_id: str, filename: str, mime: str, data: bytes, kind: MediaKind
    ) -> MediaRef:
        """Serverseitig erzeugte Medien (KI) ablegen und als MediaRef zurückgeben."""
        ext = {**_IMAGE_MIME, **_AUDIO_MIME}.get(mime.lower())
        if ext is None:
            ext = mimetypes.guess_extension(mime) or ""
        ref = MediaRef(filename=filename, mime=mime, kind=kind)
        self._repo.write_media(book_id, ref.id, ext, data)
        return ref

    def delete(self, book_id: str, media_id: str) -> None:
        """Mediendatei löschen (z. B. verworfene KI-Generierung)."""
        self._repo.delete_media_file(book_id, media_id)

    def cleanup_orphans(self, book_id: str, grace_seconds: int | None = None) -> list[str]:
        """Nicht referenzierte Mediendateien eines Buchs entfernen.

        Dateien innerhalb der Karenzzeit (mtime) werden verschont, damit frisch
        generierte, noch nicht bestätigte KI-Medien nicht gelöscht werden.
        """
        if not self._repo.exists(book_id):
            return []
        grace = (
            grace_seconds
            if grace_seconds is not None
            else self._settings.media_cleanup_grace_seconds
        )
        book = self._repo.get(book_id)
        referenced = {
            ref.id
            for chapter in book.chapters
            for page in chapter.pages
            for ref in page.media
        }
        now = time.time()
        removed: list[str] = []
        for path in self._repo.iter_media_files(book_id):
            if path.stem in referenced:
                continue
            if grace > 0 and (now - path.stat().st_mtime) < grace:
                continue
            path.unlink(missing_ok=True)
            removed.append(path.stem)
        return removed

    def cleanup_all(self, grace_seconds: int | None = None) -> int:
        """Cleanup über alle Bücher (für den periodischen Hintergrund-Task)."""
        total = 0
        for book_id in self._repo.list_book_ids():
            total += len(self.cleanup_orphans(book_id, grace_seconds))
        return total

    def resolve_path(self, book_id: str, media_id: str) -> Path:
        path = self._repo.find_media_file(book_id, media_id)
        if path is None:
            raise NotFoundError(f"Medium {media_id} nicht gefunden")
        return path

    def guess_media_type(self, path: Path) -> str:
        ext = path.suffix.lower()
        for mime, e in {**_IMAGE_MIME, **_AUDIO_MIME}.items():
            if e == ext:
                return mime
        return "application/octet-stream"

    def loader(self, book_id: str):
        """Callable, das MediaRef → Bytes lädt (für den EPUB-Export)."""

        def load(ref: MediaRef) -> bytes:
            path = self._repo.find_media_file(book_id, ref.id)
            if path is None:
                raise FileNotFoundError(ref.id)
            return path.read_bytes()

        return load

    def path_resolver(self, book_id: str):
        """Callable, das MediaRef → Dateipfad auflöst (für den PDF-Export)."""

        def resolve(ref: MediaRef) -> Path | None:
            return self._repo.find_media_file(book_id, ref.id)

        return resolve

    @staticmethod
    def extension_for(mime: str) -> str:
        return {**_IMAGE_MIME, **_AUDIO_MIME}.get(mime.lower(), os.extsep)
