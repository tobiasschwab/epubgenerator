from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field


def new_id() -> str:
    """Server-seitig generierte UUIDv4 als String."""
    return str(uuid.uuid4())


class MediaKind(str, Enum):
    image = "image"
    audio = "audio"


class MediaRef(BaseModel):
    """Referenz auf eine Mediendatei, die physisch unter media/{id}.{ext} liegt."""

    id: str = Field(default_factory=new_id)
    filename: str
    mime: str
    kind: MediaKind


class Page(BaseModel):
    id: str = Field(default_factory=new_id)
    text: str = ""  # HTML-Fragment aus dem Rich-Text-Editor
    # Geordnete, gemischte Medienliste (Bilder und Audio, mehrere pro Seite).
    media: list[MediaRef] = Field(default_factory=list)


class Chapter(BaseModel):
    id: str = Field(default_factory=new_id)
    title: str = ""
    pages: list[Page] = Field(default_factory=list)


class Book(BaseModel):
    id: str = Field(default_factory=new_id)
    title: str = ""
    description: str = ""
    chapters: list[Chapter] = Field(default_factory=list)


class BookSummary(BaseModel):
    """Kompakte Buchdarstellung für die Bücherliste (ohne Kapitelbaum)."""

    id: str
    title: str
    description: str
    chapter_count: int = 0
