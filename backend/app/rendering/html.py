"""Zentrale HTML-Erzeugung. Einzige Quelle der HTML-Repräsentation.

Vorschau, EPUB und PDF konsumieren dieselben Fragmente und dasselbe CSS.
Ein `MediaResolver` bildet eine MediaRef auf den im jeweiligen Zielformat
gültigen href ab (API-URL für die Vorschau, relativer Pfad im EPUB, file://
oder relativer Pfad fürs PDF).
"""

from __future__ import annotations

from html import escape
from typing import Callable, Iterator
from xml.sax.saxutils import quoteattr

from app.models import Book, Chapter, MediaKind, MediaRef, Page
from app.rendering.annotations import (
    AnnotationMode,
    new_counter,
    transform_annotations,
)
from app.rendering.css import ANNOTATION_JS, BASE_CSS, PRINT_CSS
from app.rendering.sanitize import normalize_fragment

__all__ = [
    "BASE_CSS",
    "PRINT_CSS",
    "MediaResolver",
    "normalize_fragment",
    "render_page_fragment",
    "render_chapter_fragment",
    "render_book_document",
]

# Ein Resolver liefert für eine MediaRef den href-String im Zielkontext.
MediaResolver = Callable[[MediaRef], str]


def _image_html(ref: MediaRef, resolver: MediaResolver) -> str:
    src = quoteattr(resolver(ref))
    alt = quoteattr(ref.filename)
    return f'<div class="page-image"><img src={src} alt={alt} /></div>'


def _audio_html(ref: MediaRef, resolver: MediaResolver) -> str:
    src = quoteattr(resolver(ref))
    typ = quoteattr(ref.mime)
    return (
        '<div class="page-audio">'
        f"<audio controls=\"controls\" src={src}>"
        f"<source src={src} type={typ} />"
        "</audio></div>"
    )


def _audio_placeholder_html(ref: MediaRef) -> str:
    return (
        '<div class="page-audio">'
        f'<p class="audio-placeholder">🔊 Audio: {escape(ref.filename)}</p>'
        "</div>"
    )


def render_page_fragment(
    page: Page,
    resolver: MediaResolver,
    *,
    audio_placeholder: bool = False,
    annotation_mode: AnnotationMode = AnnotationMode.interactive,
    note_counter: Iterator[int] | None = None,
) -> str:
    """Rendert eine Seite als XHTML-Fragment (Text + Medien + Annotationen)."""
    counter = note_counter if note_counter is not None else new_counter()
    parts: list[str] = ['<section class="page">']
    text = normalize_fragment(page.text)
    text, asides = transform_annotations(text, annotation_mode, counter)
    parts.append(f'<div class="page-text">{text}</div>')
    for ref in page.media:
        if ref.kind == MediaKind.image:
            parts.append(_image_html(ref, resolver))
        elif ref.kind == MediaKind.audio:
            if audio_placeholder:
                parts.append(_audio_placeholder_html(ref))
            else:
                parts.append(_audio_html(ref, resolver))
    # EPUB: Fußnoten-Asides in dasselbe Dokument wie die Referenz legen.
    parts.extend(asides)
    parts.append("</section>")
    return "".join(parts)


def render_chapter_fragment(
    chapter: Chapter,
    resolver: MediaResolver,
    *,
    audio_placeholder: bool = False,
    annotation_mode: AnnotationMode = AnnotationMode.interactive,
    note_counter: Iterator[int] | None = None,
) -> str:
    """Rendert ein Kapitel (Titel + alle Seiten) als XHTML-Fragment."""
    counter = note_counter if note_counter is not None else new_counter()
    parts: list[str] = ['<section class="chapter">']
    title = chapter.title.strip() or "Kapitel"
    parts.append(f'<h2 class="chapter-title">{escape(title)}</h2>')
    for page in chapter.pages:
        parts.append(
            render_page_fragment(
                page,
                resolver,
                audio_placeholder=audio_placeholder,
                annotation_mode=annotation_mode,
                note_counter=counter,
            )
        )
    parts.append("</section>")
    return "".join(parts)


def render_book_document(
    book: Book,
    resolver: MediaResolver,
    *,
    chapter_id: str | None = None,
    audio_placeholder: bool = False,
    include_print_css: bool = False,
    annotation_mode: AnnotationMode = AnnotationMode.interactive,
) -> str:
    """Rendert ein komplettes HTML-Dokument (Vorschau bzw. PDF-Quelle).

    Mit ``chapter_id`` wird nur das betreffende Kapitel gerendert.
    """
    chapters = book.chapters
    if chapter_id is not None:
        chapters = [c for c in book.chapters if c.id == chapter_id]

    counter = new_counter()
    body_parts: list[str] = []
    if chapter_id is None:
        body_parts.append(f'<h1 class="book-title">{escape(book.title)}</h1>')
        if book.description.strip():
            body_parts.append(
                f'<p class="book-description">{escape(book.description)}</p>'
            )
    for chapter in chapters:
        body_parts.append(
            render_chapter_fragment(
                chapter,
                resolver,
                audio_placeholder=audio_placeholder,
                annotation_mode=annotation_mode,
                note_counter=counter,
            )
        )

    css = BASE_CSS + ("\n" + PRINT_CSS if include_print_css else "")
    # Nur in der interaktiven Vorschau die Klick-Logik für Annotationen laden.
    script = (
        f"<script>\n{ANNOTATION_JS}\n</script>\n"
        if annotation_mode is AnnotationMode.interactive
        else ""
    )
    return (
        '<!DOCTYPE html>\n'
        '<html lang="de">\n<head>\n'
        '<meta charset="utf-8" />\n'
        f"<title>{escape(book.title)}</title>\n"
        f"<style>\n{css}\n</style>\n"
        "</head>\n<body>\n"
        + "".join(body_parts)
        + "\n"
        + script
        + "</body>\n</html>"
    )
