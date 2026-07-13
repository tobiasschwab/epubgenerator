from __future__ import annotations

import io


def test_book_lifecycle_via_api(client) -> None:
    resp = client.post("/api/books", json={"title": "API Buch", "description": "d"})
    assert resp.status_code == 201
    book = resp.json()
    book_id = book["id"]

    assert client.get("/api/books").json()[0]["id"] == book_id

    resp = client.put(
        f"/api/books/{book_id}", json={"title": "Neu", "description": "x"}
    )
    assert resp.json()["title"] == "Neu"

    assert client.delete(f"/api/books/{book_id}").status_code == 204
    assert client.get(f"/api/books/{book_id}").status_code == 404


def test_not_found_error_shape(client) -> None:
    resp = client.get("/api/books/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "not_found"
    assert "detail" in body


def test_chapters_pages_and_preview(client) -> None:
    book_id = client.post("/api/books", json={"title": "B"}).json()["id"]
    chap = client.post(
        f"/api/books/{book_id}/chapters", json={"title": "Kap"}
    ).json()
    chap_id = chap["id"]
    page = client.post(
        f"/api/books/{book_id}/chapters/{chap_id}/pages",
        json={"text": "<p>Inhalt</p>"},
    ).json()
    assert page["id"]

    prev = client.get(f"/api/books/{book_id}/preview")
    assert prev.status_code == 200
    assert "Inhalt" in prev.text
    assert "Kap" in prev.text


def test_media_upload_and_page_attach(client) -> None:
    book_id = client.post("/api/books", json={"title": "B"}).json()["id"]
    chap_id = client.post(
        f"/api/books/{book_id}/chapters", json={"title": "K"}
    ).json()["id"]
    page = client.post(
        f"/api/books/{book_id}/chapters/{chap_id}/pages", json={"text": "<p>x</p>"}
    ).json()

    png = (
        b"\x89PNG\r\n\x1a\n" + b"0" * 32
    )
    files = {"file": ("bild.png", io.BytesIO(png), "image/png")}
    ref = client.post(f"/api/books/{book_id}/media", files=files).json()
    assert ref["kind"] == "image"

    updated = client.put(
        f"/api/books/{book_id}/chapters/{chap_id}/pages/{page['id']}",
        json={"text": "<p>x</p>", "media": [ref]},
    ).json()
    assert updated["media"][0]["id"] == ref["id"]

    media = client.get(f"/api/books/{book_id}/media/{ref['id']}")
    assert media.status_code == 200

    prev = client.get(f"/api/books/{book_id}/preview")
    assert f"/api/books/{book_id}/media/{ref['id']}" in prev.text


def test_export_epub(client) -> None:
    book_id = client.post("/api/books", json={"title": "Export"}).json()["id"]
    chap_id = client.post(
        f"/api/books/{book_id}/chapters", json={"title": "K"}
    ).json()["id"]
    client.post(
        f"/api/books/{book_id}/chapters/{chap_id}/pages", json={"text": "<p>hi</p>"}
    )
    resp = client.post(f"/api/books/{book_id}/export/epub")
    assert resp.status_code == 200
    assert resp.content[:2] == b"PK"
    assert "attachment" in resp.headers["content-disposition"]
