from functools import lru_cache

from faster_whisper import WhisperModel


@lru_cache(maxsize=8)
def _get_model(model_size: str, device: str, compute_type: str) -> WhisperModel:
    return WhisperModel(model_size, device=device, compute_type=compute_type)


def transcribe_wav(path: str, model_size: str, device: str, compute_type: str) -> str:
    try:
        model = _get_model(model_size, device, compute_type)
        segments, _ = model.transcribe(path, vad_filter=True)
        transcript = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
        return transcript
    except Exception as exc:
        raise RuntimeError(f"Transcription failed: {exc}") from exc
