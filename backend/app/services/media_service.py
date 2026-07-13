from __future__ import annotations

import os
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
