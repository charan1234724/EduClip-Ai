
from pathlib import Path
from faster_whisper import WhisperModel

MODEL_SIZE = "base"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

_model = None


def get_whisper_model():
    """Load the Whisper model once and reuse it."""
    global _model

    if _model is None:
        _model = WhisperModel(
            MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
        )

    return _model


def transcribe_audio(audio_path):
    """
    Transcribe a local audio file and return timestamped segments.
    Each segment includes its start time, end time, and text.
    """
    audio_file = Path(audio_path).resolve()

    if not audio_file.is_file():
        raise FileNotFoundError(
            f"Audio file not found: {audio_file}"
        )

    model = get_whisper_model()

    segments, info = model.transcribe(
        str(audio_file),
        beam_size=5,
        vad_filter=True,
        word_timestamps=True,
    )

    timestamped_segments = []
    full_text_parts = []

    for segment in segments:
        text = segment.text.strip()

        if not text:
            continue

        words = []

        if segment.words:
            for word in segment.words:
                word_text = word.word.strip()

                if not word_text:
                    continue

                words.append({
                    "start_time": round(word.start, 3),
                    "end_time": round(word.end, 3),
                    "text": word_text,
                })

        timestamped_segments.append({
            "start_time": round(segment.start, 3),
            "end_time": round(segment.end, 3),
            "text": text,
            "words": words,
        })

        full_text_parts.append(text)

    return {
        "language": info.language,
        "language_probability": round(
            info.language_probability, 4
        ),
        "full_text": " ".join(full_text_parts),
        "segments": timestamped_segments,
    }
