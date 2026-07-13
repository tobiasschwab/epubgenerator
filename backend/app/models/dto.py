from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.domain import MediaRef


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = ""


class BookUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = ""


class ChapterCreate(BaseModel):
    title: str = ""


class ChapterUpdate(BaseModel):
    title: str = ""


class PageCreate(BaseModel):
    text: str = ""


class PageUpdate(BaseModel):
    """PUT ersetzt den Seitenzustand vollständig (Text + geordnete Medienliste)."""

    text: str = ""
    media: list[MediaRef] = Field(default_factory=list)


class MovePosition(BaseModel):
    """Zielposition (0-basiert) innerhalb der Zielliste."""

    position: int = Field(ge=0)


class MovePage(BaseModel):
    """Seite verschieben — kapitelübergreifend erlaubt."""

    target_chapter_id: str | None = None
    position: int = Field(ge=0)
