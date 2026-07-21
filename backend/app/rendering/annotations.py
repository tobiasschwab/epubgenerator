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

from app.rendering.sanitize import normalize_fragment

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


def _note_block(note: str) -> str:
    """Erklärung als Block-HTML (Rich-Text sanitisiert, oder Klartext→Absätze)."""
    if "<" in note:
        cleaned = normalize_fragment(note)
        if cleaned:
            return cleaned
    lines = [line.strip() for line in note.splitlines()]
    paras = [f"<p>{escape(line)}</p>" for line in lines if line]
    return "".join(paras) or f"<p>{escape(note.strip())}</p>"


def _note_inline(note: str) -> str:
    """Erklärung inline-tauglich flach (für PDF-Fußnoten; behält fett/kursiv)."""
    root = lxml_html.fragment_fromstring(_note_block(note), create_parent="div")

    def inline(el: etree._Element) -> str:
        s = escape(el.text) if el.text else ""
        for child in el:
            tag = child.tag if isinstance(child.tag, str) else ""
            inner = inline(child)
            if tag in ("strong", "b"):
                s += f"<strong>{inner}</strong>"
            elif tag in ("em", "i"):
                s += f"<em>{inner}</em>"
            elif tag == "code":
                s += f"<code>{inner}</code>"
            elif tag == "br":
                s += "<br/>"
            else:
                s += inner
            if child.tail:
                s += escape(child.tail)
        return s

    lines: list[str] = []
    if root.text and root.text.strip():
        lines.append(escape(root.text.strip()))
    for child in root:
        tag = child.tag if isinstance(child.tag, str) else ""
        if tag in ("ul", "ol"):
            lines.extend("• " + inline(li) for li in child.findall("li"))
        else:
            lines.append(inline(child))
    return "<br/>".join(x for x in lines if x)


def _build_ref(mode: AnnotationMode, n: int, anchor: str, note: str) -> tuple[str, str]:
    """Liefert (Inline-Referenz, optionaler Block auf Section-Ebene)."""
    esc = escape(anchor)
    mark = f'<sup class="annotation-mark">{n}</sup>'
    if mode is AnnotationMode.interactive:
        note_id = f"note-{n}"
        ref = (
            f'<button type="button" class="annotation-ref" aria-expanded="false" '
            f'aria-controls={quoteattr(note_id)}>{esc}{mark}</button>'
        )
        # Block auf Section-Ebene (kein Block-in-Inline) → per JS als Popover.
        block = (
            f'<div class="annotation-note" id={quoteattr(note_id)} role="note" '
            f'hidden="hidden"><span class="annotation-mark">{n}</span>'
            f"{_note_block(note)}</div>"
        )
        return ref, block
    if mode is AnnotationMode.epub:
        ref = (
            f'<a class="annotation-ref" epub:type="noteref" role="doc-noteref" '
            f'href="#fn-{n}" id="fnref-{n}">{esc}{mark}</a>'
        )
        aside = (
            f'<aside class="annotation-note" epub:type="footnote" role="doc-footnote" '
            f'id="fn-{n}"><span class="annotation-mark">{n}</span>{_note_block(note)}'
            "</aside>"
        )
        return ref, aside
    # pdf: WeasyPrint verschiebt den Inhalt per float:footnote ans Seitenende.
    ref = f'{esc}<span class="footnote">{_note_inline(note)}</span>'
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
