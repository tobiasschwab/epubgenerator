# ePUB3 Book Builder

Autoren-Tool zum Erstellen von **EPUB3-Büchern** mit Text, Bildern und Audio —
mit Live-Vorschau und Export als EPUB3 und PDF. Single-User, keine Datenbank
(Dateipersistenz), kein Auth. Details siehe [CLAUDE.md](./CLAUDE.md).

## Architektur

- **Backend** (`backend/`): Python 3.12 · FastAPI · Pydantic v2 · ebooklib ·
  WeasyPrint. Dateibasierte Persistenz (ein `book.json` pro Buch). Eine
  zentrale Rendering-Schicht (`app/rendering`) speist Vorschau **und** beide
  Exporte — kein doppeltes Layout.
- **Frontend** (`frontend/`): Vite · React 18 · TypeScript · TanStack Query ·
  Tailwind · **shadcn/ui** (Radix + CVA) · TipTap (Editor) · dnd-kit (Reorder) ·
  **epub.js** (E-Reader-Vorschau) · Zod.

## Vorschau-Modi

- **HTML**: Server-Vorschau über dieselbe Pipeline wie der Export (iframe-isoliert).
- **E-Reader**: das exportierte EPUB, mit **epub.js** paginiert wie in einem
  E-Reader gerendert.

## Screenshots

Desktop-Ansichten unter [`docs/screenshots/`](./docs/screenshots):
Bücherliste, Editor (3-Spalten mit gemischten Medien), KI-Bild-Dialog
(mit vorbelegtem Seitentext), E-Reader-Vorschau (epub.js) und KI-Buch-Dialog.

## Orphan-Cleanup (verwaiste Medien)

Nicht referenzierte Mediendateien (z. B. verworfene KI-Generierungen) werden
periodisch entfernt — im Hintergrund über einen Lifespan-Task
(`EPUB_MEDIA_CLEANUP_INTERVAL_SECONDS`, Default 1800 s; 0 deaktiviert) und
manuell via `POST /api/books/{bookId}/media/cleanup`. Eine Karenzzeit
(`EPUB_MEDIA_CLEANUP_GRACE_SECONDS`, Default 3600 s) schützt frisch erzeugte,
noch nicht bestätigte Medien.

## KI-Integration (Google Gemini)

Optional, aktiviert sobald ein `EPUB_GEMINI_API_KEY` gesetzt ist (sonst sind die
KI-Buttons ausgeblendet, die App läuft normal weiter). Alle Gemini-Aufrufe
liegen hinter einem Gateway (`app/services/gemini_gateway.py`) und sind ohne
Netzzugriff testbar.

- **Buch/Kapitel/Seite per Prompt**: Gemini liefert über *structured output*
  (`response_schema`) ein JSON, das 1:1 dem Domänenmodell entspricht
  (Buch → Kapitel → Seiten mit HTML-Text). Ablauf: **Vorschau → bestätigen →
  speichern**. Bei einem Buch werden Kapitel und Seiten gleich mit angelegt.
- **Bildgenerierung** pro Seite (Button): Beschreibung im Popup, mit dem
  Seitentext vorbelegt; Ergebnis wird als Vorschau gezeigt und auf Wunsch als
  Bild an die (gemischte) Medienliste der Seite gehängt.
- **Audiogenerierung** pro Seite (Button): TTS aus dem Seitentext, als WAV in
  die Medienliste.

Modelle (überschreibbar via Env): Text `gemini-2.5-flash`, Bild
`gemini-2.5-flash-image`, TTS `gemini-2.5-flash-preview-tts`.

## Medien pro Seite

Jede Seite trägt eine **geordnete, gemischte Medienliste** — beliebig viele
Bilder *und* Audiodateien, per Drag-&-Drop sortierbar. Reihenfolge und Mischung
werden in Vorschau, EPUB und PDF identisch übernommen (Audio im PDF als
Hinweisblock).

## Schnellstart (Docker Compose)

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend/API + OpenAPI-Docs: http://localhost:8000/docs

Nutzdaten liegen im gemappten Volume `./data` und überleben Rebuilds
(`data/` ist bewusst nicht versioniert).

## Entwicklung ohne Docker

```bash
# Backend
cd backend && uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e ".[dev]" && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Tests

```bash
cd backend && pytest
cd frontend && npm run test
```

## Entscheidungen (CLAUDE.md §11) & Erweiterungen

Umgesetzt sind die dort vorgeschlagenen Defaults: Stack ohne DB, WeasyPrint für
PDF, Audio im PDF als Hinweisblock, Rich-Text (TipTap) für Seitentext,
kapitelübergreifendes Verschieben, EPUB-Audio als eingebettetes `<audio>`
(ohne SMIL).

Auf Wunsch erweitert:

- **echtes shadcn/ui** (Radix-Primitives + class-variance-authority, CSS-Variablen-
  Theme mit Light/Dark) statt einer eigenen UI-Schicht.
- **epub.js** als zusätzlicher E-Reader-Vorschaumodus neben der Live-HTML-Vorschau.
- **mehrere und gemischte Medien pro Seite** (geordnete Liste, Bilder + Audio),
  statt je einem Bild/Audio.
