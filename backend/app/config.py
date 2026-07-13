from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Anwendungs-Settings. Werte kommen aus Umgebungsvariablen (Prefix EPUB_)."""

    model_config = SettingsConfigDict(env_prefix="EPUB_", env_file=".env", extra="ignore")

    data_dir: Path = Path("data")
    # Erlaubte Origins für CORS (Dev-Frontend). Kommagetrennt via Env.
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    # Maximale Uploadgröße für Medien in Bytes (Default 50 MB).
    max_upload_bytes: int = 50 * 1024 * 1024

    # --- KI (Google Gemini) ---
    # Leerer Key => KI-Funktionen sind deaktiviert (App läuft trotzdem).
    gemini_api_key: str = ""
    gemini_text_model: str = "gemini-2.5-flash"
    gemini_image_model: str = "gemini-2.5-flash-image"
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts"
    gemini_tts_voice: str = "Kore"

    @property
    def ai_enabled(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def books_dir(self) -> Path:
        return self.data_dir / "books"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.books_dir.mkdir(parents=True, exist_ok=True)
    return settings
