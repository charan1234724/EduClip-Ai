
import re
from pathlib import Path


def parse_caption_file(file_path):
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension not in {".srt", ".vtt"}:
        raise ValueError("Only SRT and VTT caption files are supported.")

    content = path.read_text(encoding="utf-8-sig")

    # Remove the WebVTT header and metadata.
    if extension == ".vtt":
        content = re.sub(
            r"^\s*WEBVTT[^\n]*\n",
            "",
            content,
            count=1,
        )

    content = re.sub(r"<[^>]+>", "", content)

    timestamp_pattern = re.compile(
        r"(?:(\d{2,}):)?(\d{2}):(\d{2})[,.](\d{3})"
        r"\s*-->\s*"
        r"(?:(\d{2,}):)?(\d{2}):(\d{2})[,.](\d{3})"
    )

    def to_seconds(hours, minutes, seconds, milliseconds):
        return (
            int(hours or 0) * 3600
            + int(minutes) * 60
            + int(seconds)
            + int(milliseconds) / 1000
        )

    lines = content.splitlines()
    segments = []
    index = 0

    while index < len(lines):
        match = timestamp_pattern.search(lines[index])

        if not match:
            index += 1
            continue

        start_time = to_seconds(*match.groups()[:4])
        end_time = to_seconds(*match.groups()[4:])

        index += 1
        text_lines = []

        while index < len(lines) and lines[index].strip():
            if timestamp_pattern.search(lines[index]):
                break

            line = lines[index].strip()

            # Ignore VTT cue settings and numeric SRT sequence lines.
            if not line.isdigit() and not line.startswith("NOTE"):
                text_lines.append(line)

            index += 1

        text = " ".join(text_lines).strip()

        if text and end_time > start_time:
            segments.append({
                "start_time": start_time,
                "end_time": end_time,
                "text": text,
            })

    if not segments:
        raise ValueError(
            "No timestamped captions were found. "
            "Check that the file is a valid SRT or VTT file."
        )

    return segments
