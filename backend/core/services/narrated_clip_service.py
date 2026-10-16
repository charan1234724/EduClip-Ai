
"""Combine video footage with generated narration using FFmpeg."""

import re
import shutil
import subprocess
import uuid
from pathlib import Path

from django.conf import settings


class NarratedClipError(Exception):
    """Raised when narrated video generation fails."""



def create_narrated_clip(
    video_path: str,
    audio_path: str,
    output_name: str = "educational-clip",
    start_time: float = 0,
    end_time: float | None = None,
) -> dict:
    """Create an MP4 from a selected video segment with generated narration."""

    video = Path(video_path).resolve()
    audio = Path(audio_path).resolve()

    if not video.is_file():
        raise NarratedClipError("The source video file was not found.")

    if not audio.is_file():
        raise NarratedClipError("The narration audio file was not found.")

    try:
        start_time = float(start_time)
        end_time = float(end_time) if end_time is not None else None
    except (TypeError, ValueError) as exc:
        raise NarratedClipError("Start and end times must be valid numbers.") from exc

    if start_time < 0:
        raise NarratedClipError("Start time cannot be negative.")

    if end_time is not None and end_time <= start_time:
        raise NarratedClipError("End time must be greater than start time.")

    ffmpeg = getattr(
        settings,
        "FFMPEG_BINARY",
        r"C:\ffmpeg\bin\ffmpeg.exe",
    )

    if not Path(ffmpeg).is_file():
        ffmpeg = shutil.which("ffmpeg")

    if not ffmpeg:
        raise NarratedClipError(
            "FFmpeg was not found. Check C:\\ffmpeg\\bin\\ffmpeg.exe."
        )

    safe_name = re.sub(
        r"[^A-Za-z0-9_-]+", "_", output_name or "educational-clip"
    ).strip("_")[:60] or "educational-clip"

    output_dir = Path(settings.MEDIA_ROOT) / "narrated_clips"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{safe_name}_{uuid.uuid4().hex[:8]}.mp4"
    output_path = output_dir / filename

    # Trim the source video to the selected interval before encoding.
    command = [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-ss", str(start_time),
        "-i", str(video),
    ]

    if end_time is not None:
        command.extend(["-t", str(end_time - start_time)])

    command.extend([
        "-i", str(audio),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ])

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )

        if result.returncode != 0:
            output_path.unlink(missing_ok=True)
            details = (result.stderr or "").strip()[-1500:]
            raise NarratedClipError(
                f"FFmpeg could not create the narrated clip: {details}"
            )

    except subprocess.TimeoutExpired as exc:
        output_path.unlink(missing_ok=True)
        raise NarratedClipError(
            "Video processing took too long. Try a smaller source video."
        ) from exc

    except OSError as exc:
        output_path.unlink(missing_ok=True)
        raise NarratedClipError(f"Could not start FFmpeg: {exc}") from exc

    if not output_path.is_file() or output_path.stat().st_size == 0:
        output_path.unlink(missing_ok=True)
        raise NarratedClipError("FFmpeg produced an empty output file.")

    return {
        "file_path": str(output_path),
        "relative_path": str(
            output_path.relative_to(Path(settings.MEDIA_ROOT))
        ),
        "size_bytes": output_path.stat().st_size,
        "filename": filename,
    }
