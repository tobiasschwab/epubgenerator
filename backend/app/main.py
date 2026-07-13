from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import ai, books, chapters, export, media, pages, preview
from app.config import Settings, get_settings
from app.errors import DomainError
from app.repositories import BookRepository
from app.services import MediaService

logger = logging.getLogger("epub.cleanup")


async def _media_cleanup_loop(settings: Settings) -> None:
    """Periodisch verwaiste Mediendateien über alle Bücher entfernen."""
    media = MediaService(BookRepository(settings), settings)
    interval = settings.media_cleanup_interval_seconds
    while True:
        try:
            removed = await asyncio.to_thread(media.cleanup_all)
            if removed:
                logger.info("Media-Cleanup: %d verwaiste Datei(en) entfernt", removed)
        except Exception:  # noqa: BLE001 — Loop darf nie sterben
            logger.exception("Media-Cleanup fehlgeschlagen")
        await asyncio.sleep(interval)


def create_app() -> FastAPI:
    settings = get_settings()

    @contextlib.asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        task: asyncio.Task[None] | None = None
        if settings.media_cleanup_interval_seconds > 0:
            task = asyncio.create_task(_media_cleanup_loop(settings))
        try:
            yield
        finally:
            if task is not None:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    app = FastAPI(title="ePUB3 Book Builder", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )

    app.include_router(books.router)
    app.include_router(chapters.router)
    app.include_router(pages.router)
    app.include_router(media.router)
    app.include_router(preview.router)
    app.include_router(export.router)
    app.include_router(ai.router)

    @app.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Prod: gebautes Frontend statisch ausliefern, wenn vorhanden.
    static_dir = Path(__file__).parent / "static"
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_app()
