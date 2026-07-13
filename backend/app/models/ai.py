"""Draft- und Request-Modelle für die KI-Generierung.

Die Draft-Modelle spiegeln die Domäne (Buch → Kapitel → Seite) und dienen
zugleich als `response_schema` für Geminis strukturierte Ausgabe. Dadurch
liefert die KI direkt eine Struktur, die 1:1 in Kapitel/Seiten übernommen wird.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PageDraft(BaseModel):
    # HTML-Fragment (nur erlaubte Tags) — wird wie manueller Editor-Output behandelt.
    text: str = ""
    # Kurzer, bildhafter Prompt für eine passende Illustration (oder leer).
    image_prompt: str = ""


class ChapterDraft(BaseModel):
    title: str = ""
    pages: list[PageDraft] = Field(default_factory=list)


class BookDraft(BaseModel):
    title: str = ""
    description: str = ""
    chapters: list[ChapterDraft] = Field(default_factory=list)


# --- Requests -----------------------------------------------------------
class BookGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    language: str = "Deutsch"
    chapter_count: int | None = Field(default=None, ge=1, le=50)
    pages_per_chapter: int | None = Field(default=None, ge=1, le=50)


class ChapterGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    language: str = "Deutsch"
    page_count: int | None = Field(default=None, ge=1, le=50)


class PageGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    language: str = "Deutsch"


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)


class AudioGenerateRequest(BaseModel):
    voice: str | None = None


class AIStatus(BaseModel):
    available: bool
