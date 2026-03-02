from pathlib import Path

from faster_whisper import WhisperModel

from app.config import settings


def transcribe_audio(audio_path: Path) -> str:
    model = WhisperModel(
        settings.TRANSCRIPTION_MODEL_SIZE,
        device=settings.TRANSCRIPTION_DEVICE,
        compute_type=settings.TRANSCRIPTION_COMPUTE_TYPE,
    )
    segments, _ = model.transcribe(str(audio_path))
    text = " ".join((s.text or "").strip() for s in segments).strip()
    if not text:
        raise RuntimeError("Transcription returned empty text")
    return text
