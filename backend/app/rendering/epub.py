"""HTML-Fragmente → EPUB3 (ebooklib).

Jede Seite wird zu einem XHTML-Content-Dokument, Kapitel bilden die Nav-Ebene.
Bilder/Audio werden als Manifest-Items eingebettet und relativ referenziert.
"""

from __future__ import annotations

import mimetypes
import os
from typing import Callable

from ebooklib import epub

from app.models import Book, MediaKind, MediaRef
from app.rendering.annotations import AnnotationMode, new_counter
from app.rendering.css import BASE_CSS
from app.rendering.html import render_page_fragment

MediaLoader = Callable[[MediaRef], bytes]


def _media_href(ref: MediaRef) -> str:
    ext = os.path.splitext(ref.filename)[1].lower()
    return f"media/{ref.id}{ext}"


def build_epub(book: Book, media_loader: MediaLoader) -> bytes:
    ebook = epub.EpubBook()
    ebook.set_identifier(f"urn:uuid:{book.id}")
    ebook.set_title(book.title or "Ohne Titel")
    ebook.set_language("de")
    if book.description:
        ebook.add_metadata("DC", "description", book.description)

    style = epub.EpubItem(
        uid="style",
        file_name="styles/base.css",
        media_type="text/css",
        content=BASE_CSS.encode("utf-8"),
    )
    ebook.add_item(style)

    # Medien nur einmal einbetten (mehrfach referenzierte Refs deduplizieren).
    embedded: set[str] = set()

    def resolver(ref: MediaRef) -> str:
        # href relativ vom Content-Dokument (liegt im Wurzelordner) zur Mediendatei.
        return _media_href(ref)

    def embed_media(ref: MediaRef) -> None:
        if ref.id in embedded:
            return
        try:
            data = media_loader(ref)
        except FileNotFoundError:
            return
        href = _media_href(ref)
        media_type = ref.mime or mimetypes.guess_type(href)[0] or "application/octet-stream"
        item = epub.EpubItem(
            uid=f"media-{ref.id}",
            file_name=href,
            media_type=media_type,
            content=data,
        )
        ebook.add_item(item)
        embedded.add(ref.id)

    spine: list = ["nav"]
    toc: list = []
    note_counter = new_counter()

    for c_index, chapter in enumerate(book.chapters):
        page_links: list[epub.Link] = []
        for p_index, page in enumerate(chapter.pages):
            for ref in page.media:
                if ref.kind in (MediaKind.image, MediaKind.audio):
                    embed_media(ref)

            file_name = f"chap_{c_index}_page_{p_index}.xhtml"
            fragment = render_page_fragment(
                page,
                resolver,
                annotation_mode=AnnotationMode.epub,
                note_counter=note_counter,
            )
            heading = ""
            if p_index == 0:
                title = chapter.title.strip() or f"Kapitel {c_index + 1}"
                heading = f'<h2 class="chapter-title">{_escape(title)}</h2>'
            item = epub.EpubHtml(
                title=chapter.title or f"Kapitel {c_index + 1}",
                file_name=file_name,
                lang="de",
            )
            # ebooklib umschließt den Body-Inhalt selbst via Template; daher nur
            # das Body-Fragment setzen (kein <?xml>/<html>-Wrapper).
            item.content = heading + fragment
            item.add_item(style)
            ebook.add_item(item)
            spine.append(item)
            if p_index == 0:
                page_links.append(item)

        chapter_title = chapter.title.strip() or f"Kapitel {c_index + 1}"
        if page_links:
            toc.append((epub.Section(chapter_title), tuple(page_links)))

    ebook.toc = tuple(toc)
    ebook.add_item(epub.EpubNcx())
    nav = epub.EpubNav()
    # Platzhalter-Inhalt: ebooklib 0.20 parst beim Schreiben alle Dokument-Items
    # (u. a. für die Page-List) und scheitert an leerem Nav-Inhalt.
    nav.content = b"<html><body></body></html>"
    ebook.add_item(nav)
    ebook.spine = spine

    # ebooklib schreibt nur auf Pfad; über temporäre Datei in Bytes wandeln.
    import tempfile

    fd, tmp = tempfile.mkstemp(suffix=".epub")
    os.close(fd)
    try:
        epub.write_epub(tmp, ebook)
        with open(tmp, "rb") as fh:
            return fh.read()
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _escape(text: str) -> str:
    from html import escape

    return escape(text)
