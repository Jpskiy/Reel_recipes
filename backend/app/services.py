import json
import logging
import subprocess
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.orm import Session

from .config import settings
from .llm.ollama_client import describe_images, generate_json
from .models import Recipe
from .schemas import RecipeData

progress_store: dict[int, int] = {}
logger = logging.getLogger(__name__)


def _run_ffmpeg(args: list[str]) -> None:
    completed = subprocess.run(args, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {completed.stderr.strip()}")


def _extract_audio(video_path: Path, audio_path: Path) -> None:
    _run_ffmpeg([
        "ffmpeg", "-y", "-i", str(video_path), "-vn", "-ac", "1", "-ar", "16000", str(audio_path)
    ])


def _extract_frames(video_path: Path, frames_dir: Path) -> list[Path]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg([
        "ffmpeg", "-y", "-i", str(video_path), "-vf", "fps=1,scale=640:-1", str(frames_dir / "frame_%04d.jpg")
    ])
    frames = sorted(frames_dir.glob("frame_*.jpg"))
    if len(frames) <= 30:
        return frames
    step = len(frames) / 30
    return [frames[int(i * step)] for i in range(30)]


def _sample_frames(frame_paths: list[Path], sample_count: int = 8) -> list[Path]:
    if len(frame_paths) <= sample_count:
        return frame_paths
    step = (len(frame_paths) - 1) / (sample_count - 1)
    return [frame_paths[round(i * step)] for i in range(sample_count)]


def _transcribe_audio(audio_path: Path) -> str:
    from .transcribe.local_whisper import transcribe_wav

    return transcribe_wav(
        path=str(audio_path),
        model_size=settings.transcription_model_size,
        device=settings.transcription_device,
        compute_type=settings.transcription_compute_type,
    )


def _vision_notes(video_path: Path, frames_dir: Path) -> str:
    if not settings.enable_vision:
        logger.info("Vision disabled; skipping frame analysis.")
        return ""
    try:
        frames = _extract_frames(video_path, frames_dir)
        sampled = _sample_frames(frames, sample_count=8)
        if not sampled:
            return ""
        prompt = (
            "Summarize visible ingredients, actions, cookware, temperatures, and timing clues as concise bullet points. "
            "If the frames are unclear, say so briefly."
        )
        return describe_images(prompt=prompt, frame_paths=sampled, model=settings.vision_model, host=settings.ollama_host)
    except Exception as exc:
        logger.warning("Vision step skipped: %s", exc)
        return ""


def _recipe_prompt(transcript: str, vision_notes: str) -> str:
    schema = json.dumps(RecipeData.model_json_schema(), indent=2)
    vision_section = vision_notes or "No vision notes provided."
    return f"""
You are a recipe extraction system.
Return ONLY JSON. No markdown, no code fences, no commentary.
Use exactly this schema and field names:
{schema}

Rules:
- Return a single JSON object.
- Use null for unknown values.
- Do not add trailing commas.
- Keep step numbering sequential starting at 1.
- Ingredients must be objects with item, quantity, unit, and prep.
- If information is uncertain, keep the value conservative and note the uncertainty in notes.

Transcript:
{transcript}

Vision notes:
{vision_section}
""".strip()


def _repair_prompt(bad_content: str) -> str:
    schema = json.dumps(RecipeData.model_json_schema(), indent=2)
    return f"""
Repair this into strict valid JSON only.
Return a single JSON object with no markdown and no commentary.
Use exactly this schema:
{schema}

Rules:
- Preserve the recipe content when possible.
- Use null for unknown values.
- Remove trailing commas.

Bad content:
{bad_content}
""".strip()


def _parse_recipe(raw: str) -> RecipeData:
    payload = json.loads(raw)
    return RecipeData.model_validate(payload)


def _generate_recipe(transcript: str, vision_notes: str) -> RecipeData:
    prompt = _recipe_prompt(transcript, vision_notes)
    text = generate_json(prompt=prompt, model=settings.recipe_model, host=settings.ollama_host)

    try:
        return _parse_recipe(text)
    except (json.JSONDecodeError, ValidationError):
        fixed = generate_json(prompt=_repair_prompt(text), model=settings.recipe_model, host=settings.ollama_host)
        try:
            return _parse_recipe(fixed)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise RuntimeError(f"Recipe model returned invalid JSON after repair attempt: {exc}") from exc


def process_recipe(recipe_id: int, storage_dir: Path, db: Session) -> None:
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        return
    recipe.status = "processing"
    recipe.error_message = None
    progress_store[recipe_id] = 5
    db.commit()

    try:
        input_video = storage_dir / "input.mp4"
        audio_path = storage_dir / "audio.wav"
        frames_dir = storage_dir / "frames"

        _extract_audio(input_video, audio_path)
        progress_store[recipe_id] = 25

        transcript = _transcribe_audio(audio_path)
        recipe.transcript_text = transcript
        db.commit()
        progress_store[recipe_id] = 55

        vision_notes = _vision_notes(input_video, frames_dir)
        recipe.vision_notes = vision_notes
        db.commit()
        progress_store[recipe_id] = 75

        recipe_data = _generate_recipe(transcript, vision_notes)
        recipe.recipe_json = recipe_data.model_dump_json(indent=2)
        recipe.status = "ready"
        progress_store[recipe_id] = 100
        db.commit()
    except Exception as exc:
        recipe.status = "error"
        recipe.error_message = str(exc)
        progress_store[recipe_id] = 100
        db.commit()
