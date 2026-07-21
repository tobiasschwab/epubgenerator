"""HTML-Sanitisierung (Whitelist) für Editor-Output und Annotationen.

Eigenes Modul, damit sowohl die Seiten-Rendering-Schicht (`html.py`) als auch
die Annotationen (`annotations.py`) es ohne Import-Zyklus nutzen können.
"""

from __future__ import annotations

from html import escape

from lxml import etree, html as lxml_html

# Tags, die aus dem Editor-Output erlaubt sind. Alles andere wird entpackt.
ALLOWED_TAGS = {
    "p", "br", "strong", "b", "em", "i", "u", "s", "sub", "sup",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "blockquote", "pre", "code",
    "a", "span",
}
ALLOWED_ATTRS = {
    "a": {"href", "title"},
    "span": {"class", "data-note"},
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
        parts.append(etree.tostring(child, encoding="unicode", method="xml"))
    return "".join(parts).strip()


def _clean_element(element: etree._Element) -> None:
    for child in list(element):
        _clean_element(child)
        tag = child.tag if isinstance(child.tag, str) else ""
        if tag.lower() not in ALLOWED_TAGS:
            _unwrap(child)
            continue
        allowed = ALLOWED_ATTRS.get(tag.lower(), set())
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
