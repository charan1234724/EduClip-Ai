
"""Text-to-speech service for EduClip AI."""
import asyncio
import re
import uuid
from pathlib import Path

import edge_tts
from django.conf import settings


DEFAULT_VOICE = "en-US-AriaNeural"


class TTSServiceError(Exception):
    """Raised when narration generation fails."""


def generate_narration(text: str, voice: str = DEFAULT_VOICE) -> dict:
    """Generate an MP3 narration from text and save it under MEDIA_ROOT."""

    text = (text or "").strip()
    if not text:
        raise TTSServiceError("Please provide text for narration.")

    if len(text) > 10000:
        raise TTSServiceError(
            "Narration text is too long. Please use 10,000 characters or fewer."
        )

    if not re.fullmatch(r"[A-Za-z0-9-]+", voice or ""):
        raise TTSServiceError("Invalid voice name.")

    output_dir = Path(settings.MEDIA_ROOT) / "narrations"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"narration_{uuid.uuid4().hex}.mp3"
    output_path = output_dir / filename

    async def _save_audio():
        communicator = edge_tts.Communicate(text, voice)
        await communicator.save(str(output_path))

    try:
        asyncio.run(_save_audio())
    except Exception as exc:
        output_path.unlink(missing_ok=True)
        raise TTSServiceError(
            "Could not generate narration. Check your internet connection and try again."
        ) from exc

    if not output_path.exists() or output_path.stat().st_size == 0:
        output_path.unlink(missing_ok=True)
        raise TTSServiceError("Narration generation returned an empty audio file.")

    return {
        "file_path": str(output_path),
        "relative_path": str(output_path.relative_to(Path(settings.MEDIA_ROOT))),
        "size_bytes": output_path.stat().st_size,
        "voice": voice,
    }
