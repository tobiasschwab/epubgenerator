"""HTML → PDF (WeasyPrint).

Nutzt dasselbe Print-CSS wie die Vorschau. Audio kann im PDF nicht abspielen
und wird daher als Hinweisblock dargestellt (audio_placeholder=True).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from app.models import Book, MediaRef
from app.rendering.annotations import AnnotationMode
from app.rendering.html import render_book_document

# Resolver liefert einen file://-Pfad, den WeasyPrint laden kann.
MediaPathResolver = Callable[[MediaRef], Path | None]


def build_pdf(book: Book, media_path_resolver: MediaPathResolver, base_url: str) -> bytes:
    # Import lokal, damit Tests ohne WeasyPrint-Systemlibs importieren können.
    from weasyprint import HTML

    def resolver(ref: MediaRef) -> str:
        path = media_path_resolver(ref)
        if path is None:
            return ""
        return path.resolve().as_uri()

    html_doc = render_book_document(
        book,
        resolver,
        audio_placeholder=True,
        include_print_css=True,
        annotation_mode=AnnotationMode.pdf,
    )
    return HTML(string=html_doc, base_url=base_url).write_pdf()
