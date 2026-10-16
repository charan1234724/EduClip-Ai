
import subprocess
from pathlib import Path


FFMPEG_PATH = Path(r"C:\ffmpeg\bin\ffmpeg.exe")
FFPROBE_PATH = Path(r"C:\ffmpeg\bin\ffprobe.exe")


def check_ffmpeg():
    """Check that FFmpeg and FFprobe can be executed."""
    if not FFMPEG_PATH.is_file():
        raise FileNotFoundError(
            f"FFmpeg executable not found: {FFMPEG_PATH}"
        )

    if not FFPROBE_PATH.is_file():
        raise FileNotFoundError(
            f"FFprobe executable not found: {FFPROBE_PATH}"
        )

    result = subprocess.run(
        [str(FFMPEG_PATH), "-version"],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )

    return result.stdout.splitlines()[0]


def extract_audio(video_path, output_path):
    """
    Extract audio from a permitted local video file into MP3 format.
    The caller must provide paths to existing input and intended output.
    """
    source = Path(video_path).resolve()
    destination = Path(output_path).resolve()

    if not source.is_file():
        raise FileNotFoundError("Source video file does not exist.")

    if source == destination:
        raise ValueError("Input and output paths must be different.")

    destination.parent.mkdir(parents=True, exist_ok=True)

    command = [
        str(FFMPEG_PATH),
        "-nostdin",
        "-y",
        "-i", str(source),
        "-vn",
        "-codec:a", "libmp3lame",
        "-q:a", "2",
        str(destination),
    ]

    subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=600,
        check=True,
    )

    if not destination.is_file() or destination.stat().st_size == 0:
        raise RuntimeError("Audio extraction did not produce a valid file.")

    return destination


import os
import subprocess
from pathlib import Path


FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"


def generate_video_clip(
    input_path,
    start_time,
    end_time,
    output_path,
):
    """
    Generate an MP4 clip from an existing local video.

    start_time and end_time are measured in seconds.
    """
    input_file = Path(input_path).resolve()
    output_file = Path(output_path).resolve()

    if not os.path.isfile(FFMPEG_PATH):
        raise FileNotFoundError(
            f"FFmpeg executable not found: {FFMPEG_PATH}"
        )

    if not input_file.is_file():
        raise FileNotFoundError(
            f"Input video not found: {input_file}"
        )

    start_time = float(start_time)
    end_time = float(end_time)

    if start_time < 0 or end_time <= start_time:
        raise ValueError(
            "End time must be greater than start time, "
            "and start time cannot be negative."
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    command = [
        FFMPEG_PATH,
        "-y",
        "-ss", str(start_time),
        "-i", str(input_file),
        "-t", str(end_time - start_time),
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(output_file),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )

    if result.returncode != 0:
        if output_file.exists():
            output_file.unlink()

        raise RuntimeError(
            "FFmpeg clip generation failed: "
            + result.stderr[-3000:]
        )

    if not output_file.is_file() or output_file.stat().st_size == 0:
        raise RuntimeError(
            "FFmpeg did not produce a valid output video."
        )

    return str(output_file)
