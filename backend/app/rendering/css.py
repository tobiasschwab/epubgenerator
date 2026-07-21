"""Gemeinsames CSS für Vorschau, EPUB und PDF (single source of truth)."""

BASE_CSS = """
html { font-size: 100%; }
body {
  font-family: "Georgia", "Times New Roman", serif;
  line-height: 1.6;
  color: #1a1a1a;
  margin: 0;
  padding: 0;
}
.book-title { font-size: 2rem; margin: 0 0 0.25em; }
.book-description { color: #555; font-style: italic; margin: 0 0 2rem; }
.chapter { margin-bottom: 2rem; }
.chapter-title {
  font-size: 1.5rem;
  border-bottom: 2px solid #ddd;
  padding-bottom: 0.25em;
  margin: 0 0 1rem;
}
.page { margin: 0 0 1.5rem; }
.page-text h1, .page-text h2, .page-text h3 { line-height: 1.3; }
.page-text p { margin: 0 0 0.75em; }
.page-text ul, .page-text ol { margin: 0 0 0.75em 1.5em; }
.page-image { text-align: center; margin: 1rem 0; }
.page-image img { max-width: 100%; height: auto; }
.page-audio { margin: 1rem 0; }
.page-audio audio { width: 100%; }
.audio-placeholder {
  border: 1px solid #ccc;
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  background: #f5f5f5;
  color: #444;
  font-family: sans-serif;
  font-size: 0.9rem;
}

/* Annotationen / Erklärungen */
.annotation { position: relative; }
.annotation-ref {
  cursor: pointer;
  background: none;
  border: none;
  padding: 0;
  margin: 0;
  font: inherit;
  color: #1a4ba3;
  text-decoration: none;
  border-bottom: 1px dotted #1a4ba3;
}
.annotation-mark {
  font-size: 0.7em;
  vertical-align: super;
  line-height: 0;
  color: #1a4ba3;
}
.annotation-note {
  display: block;
  margin: 0.6rem 0;
  padding: 0.5rem 0.75rem 0.5rem 2rem;
  border-left: 3px solid #1a4ba3;
  background: #eef3fb;
  border-radius: 6px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
  font-family: sans-serif;
  font-size: 0.9rem;
  position: relative;
}
.annotation-note[hidden] { display: none; }
.annotation-note > .annotation-mark {
  position: absolute;
  left: 0.6rem;
  top: 0.5rem;
  font-weight: 700;
  vertical-align: baseline;
}
.annotation-note p { margin: 0 0 0.35em; }
.annotation-note p:last-child { margin-bottom: 0; }
.annotation-note ul, .annotation-note ol { margin: 0.2em 0 0.4em 1.2em; }
aside.annotation-note { border-left-color: #999; box-shadow: none; }
""".strip()

# Klick-Logik nur für die interaktive Vorschau: Erklärung als schwebendes
# Popover nahe dem angeklickten Wort ein-/ausblenden.
ANNOTATION_JS = """
(function () {
  function hideAll() {
    document.querySelectorAll('.annotation-note:not([hidden])').forEach(function (n) {
      n.setAttribute('hidden', 'hidden');
      n.style.position = '';
    });
    document.querySelectorAll('.annotation-ref[aria-expanded="true"]').forEach(function (b) {
      b.setAttribute('aria-expanded', 'false');
    });
  }
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.annotation-ref');
    if (!btn) {
      if (!e.target.closest('.annotation-note')) hideAll();
      return;
    }
    var id = btn.getAttribute('aria-controls');
    var note = id && document.getElementById(id);
    if (!note) return;
    var wasOpen = !note.hasAttribute('hidden');
    hideAll();
    if (!wasOpen) {
      note.removeAttribute('hidden');
      btn.setAttribute('aria-expanded', 'true');
      var r = btn.getBoundingClientRect();
      note.style.position = 'fixed';
      note.style.left = Math.max(8, Math.min(r.left, window.innerWidth - 340)) + 'px';
      note.style.top = (r.bottom + 6) + 'px';
      note.style.maxWidth = '320px';
      note.style.margin = '0';
      note.style.zIndex = '50';
    }
  });
})();
""".strip()

PRINT_CSS = """
@page {
  size: A4;
  margin: 20mm 18mm;
}
.chapter { page-break-before: always; }
.chapter:first-of-type { page-break-before: avoid; }
.page { page-break-inside: avoid; }
img { page-break-inside: avoid; }

/* Annotationen im PDF als echte Fußnoten am Seitenende (WeasyPrint). */
.footnote {
  float: footnote;
  font-size: 0.85rem;
  font-family: sans-serif;
}
.footnote p { display: inline; margin: 0; }
@page { @footnote { border-top: 0.5pt solid #999; padding-top: 2pt; } }
.footnote::footnote-call { font-size: 0.7em; vertical-align: super; }
""".strip()
