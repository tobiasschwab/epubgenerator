"""Dünne Kapselung der Google-Gemini-Aufrufe.

Als Protocol definiert, damit die AIService-Logik ohne echten Netzzugriff
testbar ist (Fake-Gateway). Der echte Gateway importiert `google-genai` erst
bei Bedarf, sodass die App auch ohne installiertes SDK/Key startet.
"""

from __future__ import annotations

import io
import wave
from typing import Any, Protocol, runtime_checkable

_TTS_SAMPLE_RATE = 24000  # Gemini-TTS liefert 24 kHz, 16-bit, mono PCM.


@runtime_checkable
class GeminiGateway(Protocol):
    def generate_structured(
        self, *, model: str, system_instruction: str, prompt: str, schema: type
    ) -> Any: ...

    def generate_image(self, *, model: str, prompt: str) -> tuple[bytes, str]: ...

    def generate_pcm_audio(
        self, *, model: str, text: str, voice: str
    ) -> tuple[bytes, int]: ...


def pcm_to_wav(pcm: bytes, sample_rate: int = _TTS_SAMPLE_RATE) -> bytes:
    """Rohes 16-bit-Mono-PCM in einen WAV-Container verpacken."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)
    return buffer.getvalue()


class RealGeminiGateway:
    """Echte Anbindung an die Gemini-API via `google-genai`."""

    def __init__(self, api_key: str) -> None:
        from google import genai  # lazy import

        self._client = genai.Client(api_key=api_key)

    def generate_structured(
        self, *, model: str, system_instruction: str, prompt: str, schema: type
    ) -> Any:
        from google.genai import types

        resp = self._client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        parsed = getattr(resp, "parsed", None)
        if parsed is not None:
            return parsed
        return schema.model_validate_json(resp.text)  # type: ignore[attr-defined]

    def generate_image(self, *, model: str, prompt: str) -> tuple[bytes, str]:
        from google.genai import types

        resp = self._client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )
        for part in _iter_parts(resp):
            inline = getattr(part, "inline_data", None)
            if inline and inline.data and (inline.mime_type or "").startswith("image/"):
                return inline.data, inline.mime_type
        raise ValueError("Keine Bilddaten in der Gemini-Antwort")

    def generate_pcm_audio(
        self, *, model: str, text: str, voice: str
    ) -> tuple[bytes, int]:
        from google.genai import types

        resp = self._client.models.generate_content(
            model=model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                    )
                ),
            ),
        )
        for part in _iter_parts(resp):
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                return inline.data, _TTS_SAMPLE_RATE
        raise ValueError("Keine Audiodaten in der Gemini-Antwort")


def _iter_parts(resp: Any):
    for candidate in getattr(resp, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            yield part
