from __future__ import annotations

import wave
from io import BytesIO

import pytest

from app.api.deps import get_ai_service
from app.config import get_settings
from app.models.ai import BookDraft, ChapterDraft, PageDraft
from app.repositories import BookRepository
from app.services import AIService
from app.services.media_service import MediaService


class FakeGateway:
    """Deterministischer Ersatz für die Gemini-API (kein Netzzugriff)."""

    def generate_structured(self, *, model, system_instruction, prompt, schema):
        page = PageDraft(text="<p>KI-Text</p>", image_prompt="a red fox")
        if schema is BookDraft:
            return BookDraft(
                title="KI-Buch",
                description="Von der KI erzeugt",
                chapters=[ChapterDraft(title="Kapitel 1", pages=[page])],
            )
        if schema is ChapterDraft:
            return ChapterDraft(title="KI-Kapitel", pages=[page])
        return page

    def generate_image(self, *, model, prompt):
        return (b"\x89PNG\r\n\x1a\n" + b"0" * 20, "image/png")

    def generate_pcm_audio(self, *, model, text, voice):
        return (b"\x00\x01" * 100, 24000)


@pytest.fixture
def ai_client(client):
    settings = get_settings()

    def override() -> AIService:
        repo = BookRepository(settings)
        return AIService(settings, repo, MediaService(repo, settings), FakeGateway())

    client.app.dependency_overrides[get_ai_service] = override
    yield client
    client.app.dependency_overrides.pop(get_ai_service, None)


def test_status_unavailable_without_key(client) -> None:
    assert client.get("/api/ai/status").json() == {"available": False}


def test_models_catalog(client) -> None:
    info = client.get("/api/ai/models").json()
    assert info["text"]["default"] == "gemini-3.5-flash"
    assert info["image"]["default"] == "gemini-3.1-flash-image"
    text_ids = [o["id"] for o in info["text"]["options"]]
    assert "gemini-3.5-flash" in text_ids
    assert "gemini-3.1-flash-lite" in text_ids
    assert info["voices"]  # nicht leer


def test_generate_book_honours_model_override(ai_client) -> None:
    # Modell-Override wird an das Gateway durchgereicht.
    draft = ai_client.post(
        "/api/ai/generate/book",
        json={"prompt": "Füchse", "model": "gemini-3.1-pro"},
    ).json()
    assert draft["title"] == "KI-Buch"


def test_generate_returns_503_without_key(client) -> None:
    resp = client.post("/api/ai/generate/book", json={"prompt": "Ein Buch über Füchse"})
    assert resp.status_code == 503
    assert resp.json()["code"] == "ai_unavailable"


def test_generate_and_commit_book(ai_client) -> None:
    draft = ai_client.post(
        "/api/ai/generate/book",
        json={"prompt": "Füchse", "language": "Deutsch", "chapter_count": 1},
    ).json()
    assert draft["title"] == "KI-Buch"
    assert draft["chapters"][0]["pages"][0]["image_prompt"] == "a red fox"

    book = ai_client.post("/api/ai/books", json=draft).json()
    assert book["chapters"][0]["pages"][0]["text"] == "<p>KI-Text</p>"
    # Wirklich persistiert?
    assert ai_client.get(f"/api/books/{book['id']}").status_code == 200


def test_generate_chapter_and_page_commit(ai_client) -> None:
    book_id = ai_client.post("/api/books", json={"title": "B"}).json()["id"]

    cdraft = ai_client.post(
        "/api/ai/generate/chapter", json={"prompt": "Ein Kapitel"}
    ).json()
    chapter = ai_client.post(
        f"/api/ai/books/{book_id}/chapters", json=cdraft
    ).json()
    assert chapter["title"] == "KI-Kapitel"

    pdraft = ai_client.post("/api/ai/generate/page", json={"prompt": "Eine Seite"}).json()
    page = ai_client.post(
        f"/api/ai/books/{book_id}/chapters/{chapter['id']}/pages", json=pdraft
    ).json()
    assert page["text"] == "<p>KI-Text</p>"


def test_generate_image_stores_media(ai_client) -> None:
    book_id = ai_client.post("/api/books", json={"title": "B"}).json()["id"]
    chap_id = ai_client.post(
        f"/api/books/{book_id}/chapters", json={"title": "K"}
    ).json()["id"]
    page_id = ai_client.post(
        f"/api/books/{book_id}/chapters/{chap_id}/pages", json={"text": "<p>x</p>"}
    ).json()["id"]

    ref = ai_client.post(
        f"/api/ai/books/{book_id}/chapters/{chap_id}/pages/{page_id}/image",
        json={"prompt": "ein Fuchs"},
    ).json()
    assert ref["kind"] == "image"
    # Datei ist abrufbar …
    assert ai_client.get(f"/api/books/{book_id}/media/{ref['id']}").status_code == 200
    # … und wieder verwerfbar.
    assert ai_client.delete(f"/api/books/{book_id}/media/{ref['id']}").status_code == 204
    assert ai_client.get(f"/api/books/{book_id}/media/{ref['id']}").status_code == 404


def test_generate_audio_produces_wav(ai_client) -> None:
    book_id = ai_client.post("/api/books", json={"title": "B"}).json()["id"]
    chap_id = ai_client.post(
        f"/api/books/{book_id}/chapters", json={"title": "K"}
    ).json()["id"]
    page_id = ai_client.post(
        f"/api/books/{book_id}/chapters/{chap_id}/pages",
        json={"text": "<p>Hallo Welt</p>"},
    ).json()["id"]

    ref = ai_client.post(
        f"/api/ai/books/{book_id}/chapters/{chap_id}/pages/{page_id}/audio",
        json={},
    ).json()
    assert ref["kind"] == "audio"
    assert ref["mime"] == "audio/wav"

    media = ai_client.get(f"/api/books/{book_id}/media/{ref['id']}")
    with wave.open(BytesIO(media.content), "rb") as wav:
        assert wav.getframerate() == 24000
        assert wav.getnchannels() == 1


def test_generate_audio_without_text_is_422(ai_client) -> None:
    book_id = ai_client.post("/api/books", json={"title": "B"}).json()["id"]
    chap_id = ai_client.post(
        f"/api/books/{book_id}/chapters", json={"title": "K"}
    ).json()["id"]
    page_id = ai_client.post(
        f"/api/books/{book_id}/chapters/{chap_id}/pages", json={"text": ""}
    ).json()["id"]

    resp = ai_client.post(
        f"/api/ai/books/{book_id}/chapters/{chap_id}/pages/{page_id}/audio", json={}
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "validation_error"
