# CLAUDE.md — ePUB3 Book Builder

> Instruktionsdatei für KI-gestützte Entwicklung (Claude Code / Codex CLI).
> Enthält Projektumfang, Stack, Konventionen, Architektur und Workflow.
> Abschnitt **„Offene Entscheidungen"** am Ende bitte zuerst klären bzw. bestätigen.

---

## 1. Projektüberblick

Einfaches Autoren-Tool zum Erstellen von **EPUB3-Büchern** mit Text, Bildern und
Audio. **Single-User**, keine Authentifizierung, kein Mandanten-/Rollenkonzept.

**Kernfunktionen**
- Bücher-CRUD (`id`, `titel`, `beschreibung`)
- Kapitel-CRUD (`id`, `titel`) — geordnet innerhalb eines Buchs
- Seiten-CRUD (`id`, `text`, `bild?`, `audio?`) — geordnet innerhalb eines Kapitels, inkl. **Verschieben**
- **Vorschau** im Browser (gleiche Rendering-Pipeline wie der Export)
- **Export** als **EPUB3** und **PDF**
- Backend mit REST-API (Persistenz **als Dateien**, keine Datenbank)
- Web-Frontend, State of the Art
- **Docker Compose** ist Teil der Entwicklung; Nutzdaten liegen in einem gemappten Volume

**Explizite Nicht-Ziele (Non-Goals)**
- Kein Login / User-Management / Sharing / Kollaboration
- Keine Datenbank (bewusste Entscheidung: Dateipersistenz genügt)
- Kein Online-Shop, kein DRM
- Keine SMIL-Read-Along-Media-Overlays in v1 (siehe offene Entscheidungen)

---

## 2. Tech-Stack

**Backend**
- Python 3.12+, **FastAPI**, Pydantic v2, Uvicorn
- **ebooklib** für EPUB3-Erzeugung
- **WeasyPrint** für PDF (HTML/CSS → PDF) — benötigt Systemlibs (Pango, Cairo, GDK-PixBuf, libffi) im Image
- `uv` für Dependency-/Env-Management
- Tests: `pytest`; Lint/Format: `ruff`; Typen: `mypy`

**Frontend**
- **Vite + React 18 + TypeScript**
- **TanStack Query** (Server-State) + **TanStack Router** (oder React Router)
- **Tailwind CSS + shadcn/ui** (Komponenten)
- **dnd-kit** für Drag-&-Drop-Reihenfolge (Verschieben von Seiten/Kapiteln)
- **TipTap** (ProseMirror) als Rich-Text-Editor → erzeugt sauberes XHTML-kompatibles HTML
- **Zod** für Schema-Validierung (spiegelt die API-Modelle)
- Tests: **Vitest** + React Testing Library; Lint: ESLint + Prettier

**Infra**
- **Docker Compose** (Dev + Prod-Profile)
- Volume-Mapping `./data:/app/data` für alle Nutzdaten (Bücher + Medien + Exporte)

---

## 3. Projektstruktur

```
epub-builder/
├── CLAUDE.md
├── docker-compose.yml
├── docker-compose.override.yml      # Dev-Overrides (HMR, Bind-Mounts)
├── .env.example
├── data/                            # gemapptes Volume — NICHT versionieren
│   └── books/
│       └── {book_id}/
│           ├── book.json            # komplette Baumstruktur (Buch→Kapitel→Seiten)
│           ├── media/{media_id}.*   # Bilder/Audio
│           └── export/              # generierte book.epub / book.pdf
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py                  # FastAPI-App, Router-Registrierung, CORS
│   │   ├── config.py                # Settings (DATA_DIR etc.)
│   │   ├── models/                  # Pydantic-Domänenmodelle (Book, Chapter, Page, Media)
│   │   ├── api/routes/              # books, chapters, pages, media, preview, export
│   │   ├── repositories/            # dateibasierte Persistenz (book.json lesen/schreiben)
│   │   ├── services/                # Anwendungslogik (Reorder, Move, Export-Orchestrierung)
│   │   ├── rendering/               # ZENTRALE HTML-Erzeugung (single source of truth)
│   │   │   ├── html.py              # Buch/Kapitel/Seite → HTML-Fragmente
│   │   │   ├── epub.py              # HTML-Fragmente → EPUB3 (ebooklib)
│   │   │   └── pdf.py               # HTML → PDF (WeasyPrint)
│   │   └── static/                  # gebautes Frontend (Prod)
│   └── tests/
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── api/                     # typisierter API-Client (aus OpenAPI generiert)
        ├── features/
        │   ├── books/
        │   ├── chapters/
        │   ├── pages/               # Editor, Medien-Upload, Reorder
        │   ├── preview/
        │   └── export/
        ├── components/              # geteilte UI (shadcn)
        └── lib/                     # Query-Client, Zod-Schemas, Utils
```

**Struktur-Prinzipien**
- Backend nach **Schichten** (routes → services → repositories → rendering), keine Fachlogik in den Routen.
- Frontend nach **Features**, geteilte Bausteine unter `components/` und `lib/`.
- Die **Rendering-Schicht ist die einzige Quelle** für die HTML-Repräsentation — Export **und** Vorschau nutzen sie (siehe §6).

---

## 4. Domänenmodell & Persistenz

### Modell
```
Book   { id, title, description, chapters: Chapter[] (geordnet) }
Chapter{ id, title, pages: Page[] (geordnet) }
Page   { id, text (HTML), image?: MediaRef, audio?: MediaRef }
MediaRef { id, filename, mime, kind: "image" | "audio" }
```
- Reihenfolge ist **implizit über die Array-Position** (kein separates `order`-Feld) → „Verschieben" = Array-Umsortierung.
- IDs: server-seitig generierte **UUIDv4** (Strings).
- `Page.text` ist HTML-Fragment (aus dem Rich-Text-Editor), das beim Export in valides XHTML normalisiert wird.

### Persistenz (dateibasiert)
- **Ein `book.json` pro Buch** hält den kompletten Baum. Einfach, atomar handhabbar, kein Konsistenzproblem über mehrere Dateien.
- Medien liegen als eigene Dateien unter `media/{media_id}.{ext}`; im JSON nur per `MediaRef` referenziert.
- **Atomare Schreibvorgänge**: in temporäre Datei schreiben, dann `os.replace()` → nie korruptes JSON bei Absturz.
- **Kein globaler Index nötig**: Bücherliste = Verzeichnis-Scan über `data/books/*/book.json`.
- Der `DATA_DIR` kommt aus der Config und ist im Container das gemappte Volume.

---

## 5. API-Konventionen (REST)

Basis: `/api`. Ressourcen genestet, damit Zugehörigkeit klar ist.

| Zweck | Methode | Pfad |
|---|---|---|
| Bücher | GET/POST | `/api/books`, `/api/books/{bookId}` (GET/PUT/DELETE) |
| Kapitel | CRUD | `/api/books/{bookId}/chapters[/{chapterId}]` |
| Kapitel verschieben | POST | `/api/books/{bookId}/chapters/{chapterId}/move` → `{ position }` |
| Seiten | CRUD | `/api/books/{bookId}/chapters/{chapterId}/pages[/{pageId}]` |
| **Seite verschieben** | POST | `/api/books/{bookId}/chapters/{chapterId}/pages/{pageId}/move` → `{ targetChapterId, position }` |
| Medien-Upload | POST | `/api/books/{bookId}/media` (multipart) → `MediaRef` |
| Medien ausliefern | GET | `/api/books/{bookId}/media/{mediaId}` |
| Vorschau (HTML) | GET | `/api/books/{bookId}/preview` (optional `?chapterId=…`) |
| Export EPUB | POST | `/api/books/{bookId}/export/epub` → Datei-Download |
| Export PDF | POST | `/api/books/{bookId}/export/pdf` → Datei-Download |

**Konventionen**
- Fehlerformat einheitlich (`{ detail, code }`), passende HTTP-Codes.
- Validierung ausschließlich über Pydantic-Modelle; keine Roh-Dicts durchreichen.
- OpenAPI-Schema wird für den **typisierten Frontend-Client** genutzt (Quelle der Wahrheit für Typen).
- Seiten-Verschieben unterstützt **kapitelübergreifend** (siehe offene Entscheidung — falls nur innerhalb: `targetChapterId` entfällt).

---

## 6. Rendering-Architektur (zentral!)

**Grundregel: Eine HTML-Repräsentation, drei Konsumenten.**

```
book.json ──► rendering/html.py ──► HTML-Fragmente (pro Seite/Kapitel)
                                     │
                 ┌───────────────────┼───────────────────┐
                 ▼                   ▼                   ▼
          rendering/epub.py    rendering/pdf.py     Vorschau (API liefert HTML)
          (ebooklib → EPUB3)   (WeasyPrint → PDF)   (Frontend rendert dasselbe)
```

- **Vorschau == Export-Fidelity**, weil beide dieselben Fragmente + dasselbe CSS nutzen. Keine doppelte Layoutlogik.
- **EPUB3**: jede Seite → ein XHTML-Content-Dokument; Kapitel → Nav (`nav.xhtml` + `toc.ncx`); Bilder/Audio als eingebettete Manifest-Items; Audio via `<audio controls>`.
- **PDF (WeasyPrint)**: gemeinsames Print-CSS mit `@page`-Regeln (Seitenränder, Umbrüche pro Kapitel). Kapitel beginnen auf neuer Seite.
- **Audio im PDF**: PDF kann Audio nicht sinnvoll abspielen → Audio wird im PDF als **Platzhalter/Hinweis** dargestellt (siehe offene Entscheidung; Default: kleiner Hinweisblock „🔊 Audio: <Dateiname>").

---

## 7. Frontend-Konventionen

- **Server-State ausschließlich über TanStack Query** (kein manuelles Fetch-State-Handling); Mutationen invalidieren gezielt.
- **Typen aus dem OpenAPI-Schema generieren** (`openapi-typescript` o. Ä.), nicht händisch pflegen.
- **Reorder** (Seiten/Kapitel) via dnd-kit → optimistisches Update, danach `move`-Endpoint; bei Fehler Rollback.
- **Editor**: TipTap mit reduziertem Toolset (Überschriften, fett/kursiv, Listen, Bild-/Audio-Einbettung). Output muss sauberes, XHTML-nahes HTML sein (keine `<div>`-Suppe, keine Inline-Styles).
- Medien-Upload mit Fortschritt + clientseitiger Größen-/MIME-Prüfung.
- Vorschau in `<iframe srcdoc>` oder isoliertem Container rendern (Style-Isolation).
- Zustand minimal halten; kein globaler Store nötig, solange Query + lokaler Component-State reichen.

---

## 8. Docker & Entwicklungs-Workflow

**Dev** (`docker compose up`)
- `backend`: FastAPI mit `--reload`, Bind-Mount `./backend:/app`, Volume `./data:/app/data`, Port `8000`.
- `frontend`: Vite Dev-Server mit HMR, Port `5173`, Proxy `/api → backend:8000`.
- Nutzdaten liegen dauerhaft in `./data` (gemapptes Volume) und überleben Rebuilds.

**Prod-Profil**
- Frontend wird gebaut und statisch vom Backend (oder nginx) ausgeliefert; ein Origin, kein CORS nötig.

**Wichtige Befehle**
```bash
# starten (dev)
docker compose up

# Backend-Tests / Lint / Typen
docker compose exec backend pytest
docker compose exec backend ruff check .
docker compose exec backend mypy app

# Frontend
docker compose exec frontend npm run test
docker compose exec frontend npm run lint
docker compose exec frontend npm run build
```

**Gotcha WeasyPrint:** Das Backend-Image muss Systempakete `libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev libcairo2` enthalten — sonst schlägt der PDF-Export zur Laufzeit fehl. Beim Erstellen des Dockerfiles zwingend berücksichtigen.

---

## 9. Coding-Standards & Konventionen

**Allgemein**
- Deutsch in fachlichen Bezeichnern nur, wo sinnvoll; Code-Identifier auf Englisch (`Book`, `Chapter`, `Page`), UI-Texte auf Deutsch.
- Kleine, fokussierte Funktionen; Fachlogik in `services/`, I/O in `repositories/`.
- Keine Geschäftslogik in Routen oder React-Komponenten.

**Backend**
- Pydantic-Modelle als einzige Ein-/Ausgabeschicht.
- Repository kapselt das gesamte Datei-I/O; Services rufen nie direkt `open()`.
- Alle Schreibzugriffe atomar (temp + `os.replace`).
- Pfade immer aus `config.DATA_DIR` ableiten, keine Hardcodes.

**Frontend**
- Feature-Ordner in sich geschlossen; geteiltes nach `components/`/`lib/`.
- Serverdaten nie im Component-State duplizieren.
- Zod-Schemas spiegeln API-Typen; an Systemgrenzen validieren.

---

## 10. Do's & Don'ts für den Agenten

**Do**
- Zuerst die Rendering-Schicht (`html.py`) bauen — sie ist Fundament für Vorschau **und** beide Exporte.
- Domänenmodell + Repository + Tests vor den Routen implementieren.
- EPUB3-Ausgabe gegen einen Validator (z. B. `epubcheck`) prüfen.
- Bei Unklarheit im Datenmodell: an dieser CLAUDE.md ausrichten, nicht raten.

**Don't**
- Keine Datenbank / kein ORM einführen (bewusste Entscheidung).
- Kein Auth-/User-Konzept hinzufügen.
- Layoutlogik nicht zwischen Vorschau und Export duplizieren.
- Keine Inline-Styles/`<div>`-Suppe im Editor-Output erzeugen (bricht EPUB-Validierung).
- `data/` nicht versionieren.

---

## 11. Offene Entscheidungen (bitte bestätigen/korrigieren)

Diese Punkte sind mit Defaults belegt; eine andere Wahl ändert Teile der Architektur:

1. **Stack** — Python/FastAPI + React/TS/Vite + Docker Compose, **ohne DB**. Passt das? *(Default: ja)*
2. **PDF & Audio** — Audio ist im PDF nicht abspielbar. Default: **Hinweis-/Platzhalterblock** im PDF. Alternativen: weglassen, oder QR-Code/Link auf die Audiodatei.
3. **PDF-Renderer** — **WeasyPrint** (HTML/CSS → PDF, volle Layout-Kontrolle, gleiche Quelle wie EPUB). Alternative wäre EPUB→PDF-Konvertierung (weniger Kontrolle). *(Default: WeasyPrint)*
4. **Seiten-Text** — **Rich Text (TipTap → HTML)**. Alternativen: Markdown oder reiner Plaintext. *(Default: Rich Text, weil EPUB-Inhalt ohnehin XHTML ist)*
5. **Vorschau-Umfang** — **Live-HTML-Vorschau** über dieselbe Pipeline. Optional zusätzlich echter EPUB-Reader (epub.js) für „Lesen wie im E-Reader"? *(Default: Live-HTML, epub.js optional später)*
6. **Medien pro Seite** — je **optional ein Bild und ein Audio** pro Seite (laut Spec Singular). Oder mehrere Medien pro Seite? *(Default: je eins)*
7. **Verschieben** — **kapitelübergreifend** (Seite in anderes Kapitel). Oder nur innerhalb desselben Kapitels? *(Default: kapitelübergreifend)*
8. **EPUB-Audio** — einfach eingebettetes `<audio>`. **SMIL-Media-Overlays** (synchrones Read-Along) sind bewusst außen vor. Für v1 ok? *(Default: ja)*
