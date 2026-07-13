"""Anwendungslogik der KI-Integration (Google Gemini).

Trennt Prompt-Aufbau/Orchestrierung von den reinen API-Aufrufen (Gateway).
Generierung liefert Drafts (Vorschau); ein separater Commit-Schritt legt
Buch/Kapitel/Seiten tatsächlich an. Bild/Audio werden erzeugt und als Medien
gespeichert, aber erst nach Bestätigung im Frontend an eine Seite gehängt.
"""

from __future__ import annotations

import re
from typing import cast

from app.config import Settings
from app.errors import AIUnavailableError, ValidationError
from app.models import Book, Chapter, MediaKind, MediaRef, Page
from app.models.ai import (
    BookDraft,
    BookGenerateRequest,
    ChapterDraft,
    ChapterGenerateRequest,
    ExplainRequest,
    ExplanationDraft,
    ModelGroup,
    ModelOption,
    ModelsInfo,
    PageDraft,
    PageGenerateRequest,
)
from app.repositories import BookRepository
from app.services import ai_catalog
from app.services.gemini_gateway import GeminiGateway, pcm_to_wav
from app.services.media_service import MediaService
from app.services.tree import find_chapter, find_page

_ALLOWED_TAGS_HINT = (
    "<p>, <h2>, <h3>, <strong>, <em>, <ul>, <ol>, <li>, <blockquote>"
)


def _html_rules(language: str) -> str:
    return (
        "Du bist ein professioneller Autoren-Assistent für ein EPUB3-Buch. "
        "Antworte ausschließlich im vorgegebenen JSON-Schema. "
        f"Schreibe alle Inhalte auf {language}. "
        "Das Textfeld jeder Seite muss einfaches, valides HTML sein und darf "
        f"NUR diese Tags verwenden: {_ALLOWED_TAGS_HINT}. "
        "Keine <html>/<body>/<div>-Tags, keine Inline-Styles, keine <img>- oder "
        "<audio>-Tags. Das Bild-Prompt-Feld enthält einen kurzen, bildhaften "
        "englischen Prompt für eine passende Illustration oder bleibt leer."
    )


def _explain_rules(language: str) -> str:
    return (
        "Du bist ein Sprachlern-Assistent. Erkläre den vom Nutzer markierten "
        f"Textabschnitt kompakt und lernfreundlich auf {language}. "
        "Gib ausschließlich das Feld 'note' zurück: reiner Klartext (KEIN HTML, "
        "kein Markdown) mit Zeilenumbrüchen. Enthalte, wo sinnvoll: den "
        "Originalabschnitt, ggf. eine andere Schriftform/Umschrift, die "
        "Wort-für-Wort-Bedeutung, eine kurze Grammatik-Erläuterung und eine "
        "natürliche Übersetzung."
    )


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


class AIService:
    def __init__(
        self,
        settings: Settings,
        repo: BookRepository,
        media: MediaService,
        gateway: GeminiGateway | None,
    ) -> None:
        self._settings = settings
        self._repo = repo
        self._media = media
        self._gateway = gateway

    @property
    def available(self) -> bool:
        return self._gateway is not None

    def _require(self) -> GeminiGateway:
        if self._gateway is None:
            raise AIUnavailableError(
                "KI ist nicht konfiguriert (kein GEMINI_API_KEY gesetzt)."
            )
        return self._gateway

    # --- Modell-Katalog für die Oberfläche ------------------------------
    def models_info(self) -> ModelsInfo:
        return ModelsInfo(
            text=self._group(ai_catalog.TEXT_MODELS, self._settings.gemini_text_model),
            image=self._group(ai_catalog.IMAGE_MODELS, self._settings.gemini_image_model),
            tts=self._group(ai_catalog.TTS_MODELS, self._settings.gemini_tts_model),
            voices=ai_catalog.TTS_VOICES,
        )

    @staticmethod
    def _group(options: list[ModelOption], default: str) -> ModelGroup:
        # Ein per Env gesetztes, nicht katalogisiertes Modell dennoch anbieten.
        if all(opt.id != default for opt in options):
            options = [
                ModelOption(id=default, label=f"{default} (konfiguriert)", tier="standard"),
                *options,
            ]
        return ModelGroup(default=default, options=options)

    # --- Generierung (Vorschau) -----------------------------------------
    def generate_book(self, req: BookGenerateRequest) -> BookDraft:
        gateway = self._require()
        scope = ""
        if req.chapter_count:
            scope += f" Erzeuge etwa {req.chapter_count} Kapitel."
        if req.pages_per_chapter:
            scope += f" Etwa {req.pages_per_chapter} Seiten pro Kapitel."
        prompt = (
            "Erzeuge ein vollständiges Buch mit Titel, kurzer Beschreibung, "
            f"Kapiteln und Seiten zum folgenden Thema:\n\n{req.prompt}{scope}"
        )
        return cast(
            BookDraft, self._structured(prompt, req.language, BookDraft, req.model)
        )

    def generate_chapter(self, req: ChapterGenerateRequest) -> ChapterDraft:
        self._require()
        scope = f" Etwa {req.page_count} Seiten." if req.page_count else ""
        prompt = (
            "Erzeuge ein einzelnes Kapitel mit Titel und Seiten zum folgenden "
            f"Thema:\n\n{req.prompt}{scope}"
        )
        return cast(
            ChapterDraft, self._structured(prompt, req.language, ChapterDraft, req.model)
        )

    def generate_page(self, req: PageGenerateRequest) -> PageDraft:
        self._require()
        prompt = (
            "Erzeuge den Inhalt einer einzelnen Buchseite zum folgenden "
            f"Thema:\n\n{req.prompt}"
        )
        return cast(
            PageDraft, self._structured(prompt, req.language, PageDraft, req.model)
        )

    def explain(self, req: ExplainRequest) -> ExplanationDraft:
        prompt = f"Erkläre diesen Textabschnitt:\n\n{req.text}"
        return cast(
            ExplanationDraft,
            self._structured(
                prompt,
                req.language,
                ExplanationDraft,
                req.model,
                system_instruction=_explain_rules(req.language),
            ),
        )

    def _structured(
        self,
        prompt: str,
        language: str,
        schema: type,
        model: str | None = None,
        system_instruction: str | None = None,
    ) -> object:
        gateway = self._require()
        try:
            result = gateway.generate_structured(
                model=model or self._settings.gemini_text_model,
                system_instruction=system_instruction or _html_rules(language),
                prompt=prompt,
                schema=schema,
            )
        except Exception as exc:  # noqa: BLE001 — API-/Netzfehler einheitlich melden
            raise AIUnavailableError(f"KI-Generierung fehlgeschlagen: {exc}") from exc
        if not isinstance(result, schema):
            result = schema.model_validate(result)  # type: ignore[attr-defined]
        return result

    # --- Commit (Persistieren) ------------------------------------------
    def create_book(self, draft: BookDraft) -> Book:
        book = Book(
            title=draft.title,
            description=draft.description,
            chapters=[self._chapter_from_draft(c) for c in draft.chapters],
        )
        return self._repo.save(book)

    def append_chapter(self, book_id: str, draft: ChapterDraft) -> Chapter:
        book = self._repo.get(book_id)
        chapter = self._chapter_from_draft(draft)
        book.chapters.append(chapter)
        self._repo.save(book)
        return chapter

    def append_page(self, book_id: str, chapter_id: str, draft: PageDraft) -> Page:
        book = self._repo.get(book_id)
        chapter = find_chapter(book, chapter_id)
        page = Page(text=draft.text)
        chapter.pages.append(page)
        self._repo.save(book)
        return page

    @staticmethod
    def _chapter_from_draft(draft: ChapterDraft) -> Chapter:
        return Chapter(
            title=draft.title,
            pages=[Page(text=p.text) for p in draft.pages],
        )

    # --- Bild / Audio ----------------------------------------------------
    def generate_image(
        self,
        book_id: str,
        chapter_id: str,
        page_id: str,
        prompt: str,
        model: str | None = None,
    ) -> MediaRef:
        gateway = self._require()
        # Seite validieren (existiert sie?), Ergebnis wird noch nicht angehängt.
        find_page(find_chapter(self._repo.get(book_id), chapter_id), page_id)
        try:
            data, mime = gateway.generate_image(
                model=model or self._settings.gemini_image_model, prompt=prompt
            )
        except Exception as exc:  # noqa: BLE001
            raise AIUnavailableError(f"Bildgenerierung fehlgeschlagen: {exc}") from exc
        return self._media.store_generated(
            book_id, "ki-bild.png", mime, data, MediaKind.image
        )

    def generate_audio(
        self,
        book_id: str,
        chapter_id: str,
        page_id: str,
        voice: str | None,
        model: str | None = None,
    ) -> MediaRef:
        gateway = self._require()
        page = find_page(find_chapter(self._repo.get(book_id), chapter_id), page_id)
        text = _strip_html(page.text)
        if not text:
            raise ValidationError("Die Seite enthält keinen Text für die Sprachausgabe.")
        try:
            pcm, sample_rate = gateway.generate_pcm_audio(
                model=model or self._settings.gemini_tts_model,
                text=text,
                voice=voice or self._settings.gemini_tts_voice,
            )
        except Exception as exc:  # noqa: BLE001
            raise AIUnavailableError(f"Audiogenerierung fehlgeschlagen: {exc}") from exc
        wav = pcm_to_wav(pcm, sample_rate)
        return self._media.store_generated(
            book_id, "ki-audio.wav", "audio/wav", wav, MediaKind.audio
        )
