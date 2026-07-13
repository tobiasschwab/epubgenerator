# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Systemlibs für WeasyPrint (PDF-Export). Ohne diese schlägt der PDF-Export
# zur Laufzeit fehl (siehe CLAUDE.md §8, Gotcha WeasyPrint).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Abhängigkeiten zuerst installieren (Layer-Cache).
COPY pyproject.toml ./
RUN uv pip install --system --no-cache \
    fastapi "uvicorn[standard]" "pydantic>=2.7" pydantic-settings \
    python-multipart ebooklib weasyprint lxml google-genai

COPY app ./app

ENV EPUB_DATA_DIR=/app/data
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
