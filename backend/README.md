# ePUB3 Book Builder — Backend

FastAPI-Backend mit dateibasierter Persistenz. Erzeugt HTML (Vorschau), EPUB3
und PDF aus einer zentralen Rendering-Schicht (`app/rendering`).

## Lokal starten

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Tests / Lint / Typen

```bash
pytest
ruff check .
mypy app
```

Der PDF-Export benötigt WeasyPrint-Systemlibs (Pango, Cairo, GDK-PixBuf,
libffi) — im Docker-Image bereits enthalten.
