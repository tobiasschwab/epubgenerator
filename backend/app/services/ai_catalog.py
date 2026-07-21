"""Kuratierter Katalog wählbarer Gemini-Modelle (Stand 2026).

Die *Defaults* kommen aus den Settings; dieser Katalog liefert nur die
Auswahlliste für die Oberfläche. Power-User können per Env auch andere IDs
setzen — die werden dann als zusätzliche Option ergänzt.
"""

from __future__ import annotations

from app.models.ai import ModelOption

TEXT_MODELS: list[ModelOption] = [
    ModelOption(id="gemini-3.5-flash", label="3.5 Flash", tier="standard", cost_hint="wenige Cent/Buch"),
    ModelOption(id="gemini-3.1-flash-lite", label="3.1 Flash-Lite", tier="cheap", cost_hint="günstigste Option"),
    ModelOption(id="gemini-3.1-pro", label="3.1 Pro", tier="premium", cost_hint="höhere Kosten"),
    ModelOption(id="gemini-2.5-flash", label="2.5 Flash", tier="legacy", cost_hint="sehr günstig"),
]

IMAGE_MODELS: list[ModelOption] = [
    ModelOption(id="gemini-3.1-flash-image", label="Nano Banana 2", tier="standard", cost_hint="~7 ct/Bild"),
    ModelOption(id="gemini-3.1-flash-lite-image", label="Nano Banana 2 Lite", tier="cheap", cost_hint="~4 ct/Bild"),
    ModelOption(id="gemini-3-pro-image", label="Nano Banana Pro", tier="premium", cost_hint="~13 ct/Bild"),
    ModelOption(id="gemini-2.5-flash-image", label="2.5 Flash Image", tier="legacy", cost_hint="~4 ct/Bild"),
]

TTS_MODELS: list[ModelOption] = [
    ModelOption(id="gemini-2.5-flash-preview-tts", label="2.5 Flash TTS (Preview)", tier="standard", cost_hint="~1–3 ct/Seite"),
    ModelOption(id="gemini-2.5-pro-preview-tts", label="2.5 Pro TTS (Preview)", tier="premium", cost_hint="~3–6 ct/Seite"),
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
