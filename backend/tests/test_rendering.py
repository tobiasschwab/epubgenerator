from __future__ import annotations

from app.models import Book, Chapter, MediaKind, MediaRef, Page
from app.rendering.annotations import AnnotationMode, new_counter
from app.rendering.epub import build_epub
from app.rendering.html import normalize_fragment, render_book_document, render_page_fragment

_ANNOTATED = (
    '<p><span class="annotation" data-note="Zeile eins&#10;Zeile zwei">'
    "一ばんこわいひがはじまりました</span> Rest.</p>"
)


def test_normalize_strips_disallowed_tags_and_attrs() -> None:
    html = '<p style="color:red" onclick="x()">Hallo <script>bad()</script><b>Welt</b></p>'
    out = normalize_fragment(html)
    assert "style" not in out
    assert "onclick" not in out
    assert "script" not in out
    assert "<b>Welt</b>" in out
    assert "Hallo" in out


def test_normalize_keeps_allowed_structure() -> None:
    html = "<h2>Titel</h2><ul><li>Eins</li><li>Zwei</li></ul>"
    out = normalize_fragment(html)
    assert "<h2>Titel</h2>" in out
    assert "<li>Eins</li>" in out


def test_normalize_empty() -> None:
    assert normalize_fragment("") == ""
    assert normalize_fragment("   ") == ""


def test_render_page_with_multiple_mixed_media() -> None:
    page = Page(
        text="<p>Text</p>",
        media=[
            MediaRef(id="img1", filename="a.png", mime="image/png", kind=MediaKind.image),
            MediaRef(id="aud1", filename="a.mp3", mime="audio/mpeg", kind=MediaKind.audio),
            MediaRef(id="img2", filename="b.png", mime="image/png", kind=MediaKind.image),
        ],
    )
    out = render_page_fragment(page, lambda ref: f"/media/{ref.id}")
    assert 'src="/media/img1"' in out
    assert 'src="/media/img2"' in out
    assert "<audio" in out
    assert 'src="/media/aud1"' in out
    # Reihenfolge bleibt erhalten (img1 vor aud1 vor img2).
    assert out.index("/media/img1") < out.index("/media/aud1") < out.index("/media/img2")


def test_render_page_audio_placeholder() -> None:
    page = Page(
        text="<p>x</p>",
        media=[
            MediaRef(id="a", filename="klang.mp3", mime="audio/mpeg", kind=MediaKind.audio)
        ],
    )
    out = render_page_fragment(page, lambda ref: "", audio_placeholder=True)
    assert "audio-placeholder" in out
    assert "klang.mp3" in out
    assert "<audio" not in out


def _sample_book() -> Book:
    return Book(
        title="Mein Buch",
        description="Beschreibung",
        chapters=[
            Chapter(title="Kapitel 1", pages=[Page(text="<p>Seite A</p>")]),
            Chapter(title="Kapitel 2", pages=[Page(text="<p>Seite B</p>")]),
        ],
    )


def test_render_book_document_full_and_single_chapter() -> None:
    book = _sample_book()
    full = render_book_document(book, lambda ref: "")
    assert "Mein Buch" in full
    assert "Kapitel 1" in full and "Kapitel 2" in full

    single = render_book_document(book, lambda ref: "", chapter_id=book.chapters[0].id)
    assert "Kapitel 1" in single
    assert "Kapitel 2" not in single


def test_normalize_keeps_annotation_span() -> None:
    out = normalize_fragment(_ANNOTATED)
    assert 'class="annotation"' in out
    assert "data-note" in out
    assert "一ばんこわいひがはじまりました" in out


def test_annotation_interactive_mode_toggle() -> None:
    page = Page(text=_ANNOTATED)
    out = render_page_fragment(
        page, lambda r: "", annotation_mode=AnnotationMode.interactive
    )
    assert 'class="annotation-ref"' in out
    assert 'aria-controls="note-1"' in out
    assert 'class="annotation-note"' in out and 'hidden="hidden"' in out
    # Erklärungszeilen als Absätze
    assert "<p>Zeile eins</p>" in out
    assert "<p>Zeile zwei</p>" in out
    # kein rohes data-note mehr
    assert "data-note" not in out


def test_annotation_epub_mode_footnote() -> None:
    page = Page(text=_ANNOTATED)
    out = render_page_fragment(page, lambda r: "", annotation_mode=AnnotationMode.epub)
    assert 'epub:type="noteref"' in out
    assert 'epub:type="footnote"' in out
    assert 'href="#fn-1"' in out and 'id="fn-1"' in out


def test_annotation_pdf_mode_float_footnote() -> None:
    page = Page(text=_ANNOTATED)
    out = render_page_fragment(page, lambda r: "", annotation_mode=AnnotationMode.pdf)
    assert 'class="footnote"' in out
    assert "noteref" not in out  # keine EPUB-Referenz im PDF-Modus


_RICH = (
    '<p>Wort <span class="annotation" data-note="'
    "&lt;p&gt;&lt;strong&gt;一番&lt;/strong&gt; = am meisten&lt;/p&gt;"
    "&lt;ul&gt;&lt;li&gt;怖い = gruselig&lt;/li&gt;&lt;/ul&gt;"
    '">一番怖い</span>.</p>'
)


def test_annotation_rich_html_note_block_preserved() -> None:
    # Interaktiv/EPUB: fett + Liste bleiben als Block-HTML erhalten.
    page = Page(text=_RICH)
    out = render_page_fragment(page, lambda r: "", annotation_mode=AnnotationMode.epub)
    assert "<strong>一番</strong>" in out
    assert "<li>怖い = gruselig</li>" in out


def test_annotation_rich_html_note_flattened_for_pdf() -> None:
    # PDF: Struktur flach (Liste → Aufzählungszeile), fett bleibt erhalten.
    page = Page(text=_RICH)
    out = render_page_fragment(page, lambda r: "", annotation_mode=AnnotationMode.pdf)
    assert "<strong>一番</strong>" in out
    assert "• 怖い = gruselig" in out
    assert "<li>" not in out  # keine Block-Liste im PDF-Inline-Footnote


def test_annotation_rich_html_note_sanitized() -> None:
    # Script im Notiz-HTML wird entfernt.
    evil = "&lt;script&gt;alert(1)&lt;/script&gt;&lt;strong&gt;ok&lt;/strong&gt;"
    page = Page(
        text=f'<p><span class="annotation" data-note="{evil}">x</span></p>'
    )
    out = render_page_fragment(page, lambda r: "", annotation_mode=AnnotationMode.epub)
    assert "<script" not in out  # Tag entfernt (Inhalt bleibt als harmloser Text)
    assert "<strong>ok</strong>" in out


def test_annotation_numbering_continuous_across_pages() -> None:
    counter = new_counter()
    chapter = Chapter(
        title="K",
        pages=[Page(text=_ANNOTATED), Page(text=_ANNOTATED)],
    )
    outs = [
        render_page_fragment(
            p, lambda r: "", annotation_mode=AnnotationMode.epub, note_counter=counter
        )
        for p in chapter.pages
    ]
    assert 'id="fn-1"' in outs[0]
    assert 'id="fn-2"' in outs[1]


def test_preview_document_includes_annotation_script() -> None:
    book = Book(title="B", chapters=[Chapter(title="K", pages=[Page(text=_ANNOTATED)])])
    doc = render_book_document(book, lambda r: "")
    assert "annotation-ref" in doc
    assert "<script>" in doc  # interaktive Klick-Logik


def test_build_epub_produces_zip() -> None:
    book = _sample_book()
    data = build_epub(book, lambda ref: b"")
    # EPUB ist ein ZIP-Container.
    assert data[:2] == b"PK"
    assert len(data) > 100
