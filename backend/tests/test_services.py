from __future__ import annotations

import pytest

from app.config import Settings
from app.errors import NotFoundError
from app.models import BookCreate, BookUpdate, ChapterCreate, MediaKind, PageCreate, PageUpdate
from app.repositories import BookRepository
from app.services import BookService, ChapterService, MediaService, PageService


def test_book_crud_roundtrip(repo: BookRepository) -> None:
    books = BookService(repo)
    created = books.create(BookCreate(title="Titel", description="d"))
    assert created.id
    fetched = books.get(created.id)
    assert fetched.title == "Titel"
    updated = books.update(created.id, BookUpdate(title="Neu", description="x"))
    assert updated.title == "Neu"
    assert any(b.id == created.id for b in books.list())
    books.delete(created.id)
    with pytest.raises(NotFoundError):
        books.get(created.id)


def test_chapter_move(repo: BookRepository) -> None:
    books = BookService(repo)
    chapters = ChapterService(repo)
    book = books.create(BookCreate(title="B"))
    c1 = chapters.create(book.id, ChapterCreate(title="Eins"))
    c2 = chapters.create(book.id, ChapterCreate(title="Zwei"))
    chapters.create(book.id, ChapterCreate(title="Drei"))

    chapters.move(book.id, c2.id, 0)
    titles = [c.title for c in chapters.list(book.id)]
    assert titles == ["Zwei", "Eins", "Drei"]

    chapters.move(book.id, c1.id, 99)  # über Ende → ans Ende
    titles = [c.title for c in chapters.list(book.id)]
    assert titles[-1] == "Eins"


def test_page_move_cross_chapter(repo: BookRepository) -> None:
    books = BookService(repo)
    chapters = ChapterService(repo)
    pages = PageService(repo)
    book = books.create(BookCreate(title="B"))
    c1 = chapters.create(book.id, ChapterCreate(title="C1"))
    c2 = chapters.create(book.id, ChapterCreate(title="C2"))
    p1 = pages.create(book.id, c1.id, PageCreate(text="<p>1</p>"))
    pages.create(book.id, c1.id, PageCreate(text="<p>2</p>"))

    pages.move(book.id, c1.id, p1.id, 0, target_chapter_id=c2.id)

    c1_pages = pages.list(book.id, c1.id)
    c2_pages = pages.list(book.id, c2.id)
    assert len(c1_pages) == 1
    assert len(c2_pages) == 1
    assert c2_pages[0].id == p1.id


def test_media_cleanup_removes_only_unreferenced(
    repo: BookRepository, settings: Settings
) -> None:
    books = BookService(repo)
    chapters = ChapterService(repo)
    pages = PageService(repo)
    media = MediaService(repo, settings)

    book = books.create(BookCreate(title="B"))
    chapter = chapters.create(book.id, ChapterCreate(title="C"))
    page = pages.create(book.id, chapter.id, PageCreate(text="<p>x</p>"))

    attached = media.upload(book.id, "a.png", "image/png", b"\x89PNG\r\n\x1a\n1234")
    orphan = media.upload(book.id, "b.png", "image/png", b"\x89PNG\r\n\x1a\n5678")
    pages.update(
        book.id,
        chapter.id,
        page.id,
        PageUpdate(text="<p>x</p>", media=[attached]),
    )

    # Karenzzeit 0 => frische Orphans werden entfernt, referenzierte bleiben.
    removed = media.cleanup_orphans(book.id, grace_seconds=0)
    assert removed == [orphan.id]
    assert repo.find_media_file(book.id, attached.id) is not None
    assert repo.find_media_file(book.id, orphan.id) is None


def test_media_cleanup_grace_protects_fresh_files(
    repo: BookRepository, settings: Settings
) -> None:
    books = BookService(repo)
    media = MediaService(repo, settings)
    book = books.create(BookCreate(title="B"))
    ref = media.upload(book.id, "b.png", "image/png", b"\x89PNG\r\n\x1a\n5678")
    assert ref.kind == MediaKind.image

    # Große Karenzzeit => frisch erzeugte (unangehängte) Datei bleibt erhalten.
    removed = media.cleanup_orphans(book.id, grace_seconds=3600)
    assert removed == []
    assert repo.find_media_file(book.id, ref.id) is not None


def test_atomic_write_survives(repo: BookRepository) -> None:
    books = BookService(repo)
    book = books.create(BookCreate(title="A"))
    path = repo.book_dir(book.id) / "book.json"
    assert path.exists()
    # Kein temporäres .tmp bleibt zurück.
    leftovers = list(path.parent.glob("*.tmp"))
    assert leftovers == []
