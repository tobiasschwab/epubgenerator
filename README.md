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
  Tailwind · TipTap (Editor) · dnd-kit (Reorder) · Zod.

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

## Bestätigte Defaults (CLAUDE.md §11)

Umgesetzt sind die dort vorgeschlagenen Defaults: Stack ohne DB, WeasyPrint für
PDF, Audio im PDF als Hinweisblock, Rich-Text (TipTap) für Seitentext,
Live-HTML-Vorschau, je ein Bild/Audio pro Seite, kapitelübergreifendes
Verschieben, EPUB-Audio als eingebettetes `<audio>` (ohne SMIL). shadcn/ui ist
als schlanke, selbst gepflegte UI-Primitives-Schicht (`components/ui`) umgesetzt.
