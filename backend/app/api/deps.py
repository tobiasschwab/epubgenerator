from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.config import Settings, get_settings
from app.repositories import BookRepository
from app.services import (
    BookService,
    ChapterService,
    ExportService,
    MediaService,
    PageService,
)

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_repository(settings: SettingsDep) -> BookRepository:
    # Repository ist zustandslos (nur Pfad-Logik) → pro Request billig konstruierbar.
    return BookRepository(settings)


RepoDep = Annotated[BookRepository, Depends(get_repository)]


def get_book_service(repo: RepoDep) -> BookService:
    return BookService(repo)


def get_chapter_service(repo: RepoDep) -> ChapterService:
    return ChapterService(repo)


def get_page_service(repo: RepoDep) -> PageService:
    return PageService(repo)


def get_media_service(repo: RepoDep, settings: SettingsDep) -> MediaService:
    return MediaService(repo, settings)


def get_export_service(repo: RepoDep, settings: SettingsDep) -> ExportService:
    return ExportService(repo, MediaService(repo, settings))


BookServiceDep = Annotated[BookService, Depends(get_book_service)]
ChapterServiceDep = Annotated[ChapterService, Depends(get_chapter_service)]
PageServiceDep = Annotated[PageService, Depends(get_page_service)]
MediaServiceDep = Annotated[MediaService, Depends(get_media_service)]
ExportServiceDep = Annotated[ExportService, Depends(get_export_service)]
