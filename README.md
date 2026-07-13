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
