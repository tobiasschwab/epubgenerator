"""Zentrale HTML-Erzeugung. Einzige Quelle der HTML-Repräsentation.

Vorschau, EPUB und PDF konsumieren dieselben Fragmente und dasselbe CSS.
Ein `MediaResolver` bildet eine MediaRef auf den im jeweiligen Zielformat
gültigen href ab (API-URL für die Vorschau, relativer Pfad im EPUB, file://
oder relativer Pfad fürs PDF).
"""

from __future__ import annotations

from html import escape
from typing import Callable
from xml.sax.saxutils import quoteattr

from lxml import etree, html as lxml_html

from app.models import Book, Chapter, MediaKind, MediaRef, Page
from app.rendering.css import BASE_CSS, PRINT_CSS

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

# Tags, die aus dem Editor-Output erlaubt sind. Alles andere wird entpackt.
_ALLOWED_TAGS = {
    "p", "br", "strong", "b", "em", "i", "u", "s", "sub", "sup",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "blockquote", "pre", "code",
    "a", "span",
}
_ALLOWED_ATTRS = {
    "a": {"href", "title"},
    "span": set(),
}


def normalize_fragment(fragment: str) -> str:
    """Editor-HTML → sauberes, XHTML-nahes Fragment.

    Entfernt Inline-Styles, unbekannte Tags/Attribute und stellt gültiges
    XHTML sicher (selbstschließende Tags, geschlossene Elemente).
    """
    if not fragment or not fragment.strip():
        return ""
    # In einen Wurzelknoten kapseln, damit mehrere Top-Level-Knoten gehen.
    root = lxml_html.fragment_fromstring(fragment, create_parent="div")
    _clean_element(root)
    parts: list[str] = []
    if root.text:
        parts.append(escape(root.text))
    for child in root:
        parts.append(
            etree.tostring(child, encoding="unicode", method="xml")
        )
    return "".join(parts).strip()


def _clean_element(element: etree._Element) -> None:
    for child in list(element):
        _clean_element(child)
        tag = child.tag if isinstance(child.tag, str) else ""
        if tag.lower() not in _ALLOWED_TAGS:
            _unwrap(child)
            continue
        allowed = _ALLOWED_ATTRS.get(tag.lower(), set())
        for attr in list(child.attrib):
            if attr.lower() not in allowed:
                del child.attrib[attr]


def _unwrap(element: etree._Element) -> None:
    """Ersetzt ein Element durch seine Kinder/Text (Tag entfernen, Inhalt behalten)."""
    parent = element.getparent()
    if parent is None:
        return
    index = parent.index(element)
    previous = element.getprevious()
    tail = element.tail or ""
    text = element.text or ""
    # Text des entfernten Elements an vorheriges Element/Parent anhängen.
    if index == 0:
        parent.text = (parent.text or "") + text
    elif previous is not None:
        previous.tail = (previous.tail or "") + text
    children = list(element)
    for i, sub in enumerate(children):
        parent.insert(index + i, sub)
    if children:
        last = children[-1]
        last.tail = (last.tail or "") + tail
    else:
        if index == 0:
            parent.text = (parent.text or "") + tail
        elif previous is not None:
            previous.tail = (previous.tail or "") + tail
    parent.remove(element)


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
) -> str:
    """Rendert eine Seite als XHTML-Fragment (Text + geordnete, gemischte Medien)."""
    parts: list[str] = ['<section class="page">']
    text = normalize_fragment(page.text)
    parts.append(f'<div class="page-text">{text}</div>')
    for ref in page.media:
        if ref.kind == MediaKind.image:
            parts.append(_image_html(ref, resolver))
        elif ref.kind == MediaKind.audio:
            if audio_placeholder:
                parts.append(_audio_placeholder_html(ref))
            else:
                parts.append(_audio_html(ref, resolver))
    parts.append("</section>")
    return "".join(parts)


def render_chapter_fragment(
    chapter: Chapter,
    resolver: MediaResolver,
    *,
    audio_placeholder: bool = False,
) -> str:
    """Rendert ein Kapitel (Titel + alle Seiten) als XHTML-Fragment."""
    parts: list[str] = ['<section class="chapter">']
    title = chapter.title.strip() or "Kapitel"
    parts.append(f'<h2 class="chapter-title">{escape(title)}</h2>')
    for page in chapter.pages:
        parts.append(
            render_page_fragment(page, resolver, audio_placeholder=audio_placeholder)
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
) -> str:
    """Rendert ein komplettes HTML-Dokument (Vorschau bzw. PDF-Quelle).

    Mit ``chapter_id`` wird nur das betreffende Kapitel gerendert.
    """
    chapters = book.chapters
    if chapter_id is not None:
        chapters = [c for c in book.chapters if c.id == chapter_id]

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
                chapter, resolver, audio_placeholder=audio_placeholder
            )
        )

    css = BASE_CSS + ("\n" + PRINT_CSS if include_print_css else "")
    return (
        '<!DOCTYPE html>\n'
        '<html lang="de">\n<head>\n'
        '<meta charset="utf-8" />\n'
        f"<title>{escape(book.title)}</title>\n"
        f"<style>\n{css}\n</style>\n"
        "</head>\n<body>\n"
        + "".join(body_parts)
        + "\n</body>\n</html>"
    )
