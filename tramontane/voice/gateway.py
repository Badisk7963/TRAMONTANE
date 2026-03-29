"""Voxtral-Mini voice input gateway.

Uses voxtral-mini-latest for speech-to-text transcription.
Tier 1 pricing at EUR 0.04/1M tokens — cheap enough for all pipelines.
Supports wav, mp3, ogg, m4a input formats.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)

_SUPPORTED_FORMATS = {".wav", ".mp3", ".ogg", ".m4a", ".flac", ".webm"}


class VoiceInput(BaseModel):
    """Result of a voice transcription."""

    transcript: str
    confidence: float
    language: str
    duration_seconds: float
    cost_eur: float


class VoiceGateway:
    """Transcribes audio to text using Voxtral-Mini.

    Lazy-creates the Mistral client on first use.
    """

    def __init__(
        self,
        api_key: str | None = None,
        language: str = "auto",
    ) -> None:
        self._api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        self._language = language
        self._client: Any = None

    def _get_client(self) -> Any:
        """Return (and cache) the Mistral client."""
        if self._client is None:
            from mistralai import Mistral

            self._client = Mistral(api_key=self._api_key)
        return self._client

    async def transcribe_file(self, audio_path: str) -> VoiceInput:
        """Transcribe an audio file to text.

        Reads the file, base64-encodes it, and sends to Voxtral-Mini.
        """
        path = Path(audio_path)
        if path.suffix.lower() not in _SUPPORTED_FORMATS:
            msg = (
                f"Unsupported format: {path.suffix}. "
                f"Supported: {', '.join(sorted(_SUPPORTED_FORMATS))}"
            )
            raise ValueError(msg)

        audio_bytes = path.read_bytes()
        return await self.transcribe_bytes(
            audio_bytes, format=path.suffix.lstrip("."),
        )

    async def transcribe_bytes(
        self,
        audio_bytes: bytes,
        format: str = "wav",
    ) -> VoiceInput:
        """Transcribe raw audio bytes to text."""
        client = self._get_client()
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")

        # Estimate duration from file size (rough: wav ~176KB/s at 44.1kHz)
        estimated_duration = len(audio_bytes) / 176_000

        try:
            response = await client.chat.complete_async(
                model="voxtral-mini-latest",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "audio_url",
                                "audio_url": f"data:audio/{format};base64,{audio_b64}",
                            },
                            {
                                "type": "text",
                                "text": "Transcribe this audio exactly.",
                            },
                        ],
                    },
                ],
            )

            transcript = str(response.choices[0].message.content or "")
            tokens_used = 0
            if hasattr(response, "usage") and response.usage:
                tokens_used = (
                    getattr(response.usage, "total_tokens", 0)
                )
            cost = (tokens_used / 1_000_000) * 0.04

            # Detect language from response if auto
            detected_lang = self._language
            if detected_lang == "auto":
                detected_lang = self._detect_language_hint(transcript)

            logger.info(
                "Transcribed %.1fs audio -> '%s...'",
                estimated_duration,
                transcript[:50],
            )

            return VoiceInput(
                transcript=transcript,
                confidence=0.90,
                language=detected_lang,
                duration_seconds=round(estimated_duration, 1),
                cost_eur=cost,
            )

        except Exception:
            logger.warning("Voice transcription failed", exc_info=True)
            return VoiceInput(
                transcript="",
                confidence=0.0,
                language=self._language if self._language != "auto" else "unknown",
                duration_seconds=round(estimated_duration, 1),
                cost_eur=0.0,
            )

    def transcribe_file_sync(self, audio_path: str) -> VoiceInput:
        """Synchronous wrapper for transcribe_file()."""
        return asyncio.run(self.transcribe_file(audio_path))

    def is_available(self) -> bool:
        """Check if voice transcription is available."""
        return bool(self._api_key)

    @staticmethod
    def _detect_language_hint(text: str) -> str:
        """Simple language detection from transcript content."""
        from tramontane.router.classifier import _detect_language

        return _detect_language(text)
