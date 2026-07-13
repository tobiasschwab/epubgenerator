from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import AIServiceDep
from app.models import Book, Chapter, MediaRef, Page
from app.models.ai import (
    AIStatus,
    AudioGenerateRequest,
    BookDraft,
    BookGenerateRequest,
    ChapterDraft,
    ChapterGenerateRequest,
    ExplainRequest,
    ExplanationDraft,
    ImageGenerateRequest,
    ModelsInfo,
    PageDraft,
    PageGenerateRequest,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/status", response_model=AIStatus)
def ai_status(service: AIServiceDep) -> AIStatus:
    return AIStatus(available=service.available)


@router.get("/models", response_model=ModelsInfo)
def ai_models(service: AIServiceDep) -> ModelsInfo:
    return service.models_info()


# --- Generierung (Vorschau, nicht persistiert) --------------------------
@router.post("/generate/book", response_model=BookDraft)
def generate_book(req: BookGenerateRequest, service: AIServiceDep) -> BookDraft:
    return service.generate_book(req)


@router.post("/generate/chapter", response_model=ChapterDraft)
def generate_chapter(req: ChapterGenerateRequest, service: AIServiceDep) -> ChapterDraft:
    return service.generate_chapter(req)


@router.post("/generate/page", response_model=PageDraft)
def generate_page(req: PageGenerateRequest, service: AIServiceDep) -> PageDraft:
    return service.generate_page(req)


@router.post("/explain", response_model=ExplanationDraft)
def explain(req: ExplainRequest, service: AIServiceDep) -> ExplanationDraft:
    return service.explain(req)


# --- Commit (Persistieren des bestätigten Drafts) -----------------------
@router.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
def commit_book(draft: BookDraft, service: AIServiceDep) -> Book:
    return service.create_book(draft)


@router.post(
    "/books/{book_id}/chapters",
    response_model=Chapter,
    status_code=status.HTTP_201_CREATED,
)
def commit_chapter(book_id: str, draft: ChapterDraft, service: AIServiceDep) -> Chapter:
    return service.append_chapter(book_id, draft)


@router.post(
    "/books/{book_id}/chapters/{chapter_id}/pages",
    response_model=Page,
    status_code=status.HTTP_201_CREATED,
)
def commit_page(
    book_id: str, chapter_id: str, draft: PageDraft, service: AIServiceDep
) -> Page:
    return service.append_page(book_id, chapter_id, draft)


# --- Bild / Audio zu einer Seite (erzeugt MediaRef, noch nicht angehängt) ---
@router.post(
    "/books/{book_id}/chapters/{chapter_id}/pages/{page_id}/image",
    response_model=MediaRef,
)
def generate_page_image(
    book_id: str,
    chapter_id: str,
    page_id: str,
    req: ImageGenerateRequest,
    service: AIServiceDep,
) -> MediaRef:
    return service.generate_image(book_id, chapter_id, page_id, req.prompt, req.model)


@router.post(
    "/books/{book_id}/chapters/{chapter_id}/pages/{page_id}/audio",
    response_model=MediaRef,
)
def generate_page_audio(
    book_id: str,
    chapter_id: str,
    page_id: str,
    req: AudioGenerateRequest,
    service: AIServiceDep,
) -> MediaRef:
    return service.generate_audio(book_id, chapter_id, page_id, req.voice, req.model)
