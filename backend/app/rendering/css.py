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
""".strip()
