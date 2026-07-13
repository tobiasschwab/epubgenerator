from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings, get_settings
from app.repositories import BookRepository


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    get_settings.cache_clear()
    s = Settings(data_dir=tmp_path / "data")
    s.books_dir.mkdir(parents=True, exist_ok=True)
    return s


@pytest.fixture
def repo(settings: Settings) -> BookRepository:
    return BookRepository(settings)


@pytest.fixture
def client(settings: Settings, monkeypatch: pytest.MonkeyPatch):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("EPUB_DATA_DIR", str(settings.data_dir))
    get_settings.cache_clear()

    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()
