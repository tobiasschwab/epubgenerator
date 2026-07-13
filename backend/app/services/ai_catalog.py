"""Kuratierter Katalog wählbarer Gemini-Modelle (Stand 2026).

Die *Defaults* kommen aus den Settings; dieser Katalog liefert nur die
Auswahlliste für die Oberfläche. Power-User können per Env auch andere IDs
setzen — die werden dann als zusätzliche Option ergänzt.
"""

from __future__ import annotations

from app.models.ai import ModelOption

TEXT_MODELS: list[ModelOption] = [
    ModelOption(id="gemini-3.5-flash", label="3.5 Flash", tier="standard"),
    ModelOption(id="gemini-3.1-flash-lite", label="3.1 Flash-Lite", tier="cheap"),
    ModelOption(id="gemini-3.1-pro", label="3.1 Pro", tier="premium"),
    ModelOption(id="gemini-2.5-flash", label="2.5 Flash", tier="legacy"),
]

IMAGE_MODELS: list[ModelOption] = [
    ModelOption(id="gemini-3.1-flash-image", label="Nano Banana 2", tier="standard"),
    ModelOption(id="gemini-3.1-flash-lite-image", label="Nano Banana 2 Lite", tier="cheap"),
    ModelOption(id="gemini-3-pro-image", label="Nano Banana Pro", tier="premium"),
    ModelOption(id="gemini-2.5-flash-image", label="2.5 Flash Image", tier="legacy"),
]

TTS_MODELS: list[ModelOption] = [
    ModelOption(id="gemini-2.5-flash-preview-tts", label="2.5 Flash TTS (Preview)", tier="standard"),
    ModelOption(id="gemini-2.5-pro-preview-tts", label="2.5 Pro TTS (Preview)", tier="premium"),
]

# Auswahl gängiger vorgefertigter Gemini-TTS-Stimmen.
TTS_VOICES: list[str] = [
    "Kore",
    "Puck",
    "Charon",
    "Zephyr",
    "Fenrir",
    "Aoede",
    "Leda",
    "Orus",
]
