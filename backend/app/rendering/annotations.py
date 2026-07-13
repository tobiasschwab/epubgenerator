"""Inline-Annotationen (Erklärungen) — eine Quelle, drei Darstellungen.

Im Editor wird eine Erklärung als Inline-Markierung gespeichert:
``<span class="annotation" data-note="…">markierter Text</span>``.

Die Rendering-Schicht wandelt das je nach Ziel um:
- ``interactive`` (Vorschau): anklickbarer Marker + eingeklapptes Popover (JS).
- ``epub`` (EPUB3): ``epub:type="noteref"`` + ``<aside epub:type="footnote">``
  → native Popup-Fußnote in E-Readern.
- ``pdf`` (WeasyPrint): ``float: footnote`` → Fußnote am Seitenende.
"""

from __future__ import annotations

from enum import Enum
from html import escape
from itertools import count
from typing import Iterator
from xml.sax.saxutils import quoteattr

from lxml import etree, html as lxml_html

# Sentinels aus dem Unicode-Private-Use-Bereich: markieren die Einfügestellen,
# ohne mit Nutzertext oder XML-Escaping zu kollidieren.
_TOKEN_OPEN = ""
_TOKEN_CLOSE = ""


class AnnotationMode(str, Enum):
    interactive = "interactive"  # Vorschau (JS-Popover)
    epub = "epub"  # EPUB3-Popup-Fußnote
    pdf = "pdf"  # PDF-Fußnote am Seitenende


def new_counter() -> Iterator[int]:
    return count(1)


def _note_to_html(note: str) -> str:
    """Klartext-Erklärung (mit Zeilenumbrüchen) → einfache Absätze."""
    lines = [line.strip() for line in note.splitlines()]
    paras = [f"<p>{escape(line)}</p>" for line in lines if line]
    return "".join(paras) or f"<p>{escape(note.strip())}</p>"


def _build_ref(mode: AnnotationMode, n: int, anchor: str, note: str) -> tuple[str, str]:
    """Liefert (Inline-Ersatz, optionales Aside) für eine Annotation."""
    esc = escape(anchor)
    mark = f'<sup class="annotation-mark">{n}</sup>'
    if mode is AnnotationMode.interactive:
        note_id = f"note-{n}"
        ref = (
            '<span class="annotation">'
            f'<button type="button" class="annotation-ref" aria-expanded="false" '
            f'aria-controls={quoteattr(note_id)}>{esc}{mark}</button>'
            f'<span class="annotation-note" id={quoteattr(note_id)} role="note" hidden="hidden">'
            f"{_note_to_html(note)}</span></span>"
        )
        return ref, ""
    if mode is AnnotationMode.epub:
        ref = (
            f'<a class="annotation-ref" epub:type="noteref" role="doc-noteref" '
            f'href="#fn-{n}" id="fnref-{n}">{esc}{mark}</a>'
        )
        aside = (
            f'<aside class="annotation-note" epub:type="footnote" role="doc-footnote" '
            f'id="fn-{n}"><p><sup class="annotation-mark">{n}</sup> </p>{_note_to_html(note)}'
            "</aside>"
        )
        return ref, aside
    # pdf: WeasyPrint verschiebt den Inhalt per float:footnote ans Seitenende.
    ref = f'{esc}<span class="footnote">{_note_to_html(note)}</span>'
    return ref, ""


def _replace_with_text(el: etree._Element, text: str) -> None:
    parent = el.getparent()
    if parent is None:
        return
    prev = el.getprevious()
    tail = el.tail or ""
    if prev is not None:
        prev.tail = (prev.tail or "") + text + tail
    else:
        parent.text = (parent.text or "") + text + tail
    parent.remove(el)


def _serialize_children(root: etree._Element) -> str:
    parts: list[str] = []
    if root.text:
        parts.append(escape(root.text))
    for child in root:
        parts.append(etree.tostring(child, encoding="unicode", method="xml"))
    return "".join(parts)


def transform_annotations(
    fragment: str, mode: AnnotationMode, counter: Iterator[int]
) -> tuple[str, list[str]]:
    """Annotationen im Fragment umwandeln.

    Rückgabe: (transformiertes Fragment, Liste der Aside-Elemente für EPUB).
    """
    if not fragment or "annotation" not in fragment:
        return fragment, []

    root = lxml_html.fragment_fromstring(fragment, create_parent="div")
    replacements: dict[str, str] = {}
    asides: list[str] = []
    idx = 0

    for span in list(root.iter("span")):
        classes = (span.get("class") or "").split()
        note = span.get("data-note")
        if "annotation" not in classes or note is None:
            continue
        n = next(counter)
        anchor = span.text_content()
        ref_html, aside_html = _build_ref(mode, n, anchor, note)
        token = f"{_TOKEN_OPEN}{idx}{_TOKEN_CLOSE}"
        idx += 1
        replacements[token] = ref_html
        if aside_html:
            asides.append(aside_html)
        _replace_with_text(span, token)

    out = _serialize_children(root)
    for token, rep in replacements.items():
        out = out.replace(token, rep)
    return out, asides
