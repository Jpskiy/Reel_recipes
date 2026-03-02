import base64
import json
import subprocess
from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .config import settings
from .models import Recipe
from .schemas import RecipeData

progress_store: dict[int, int] = {}


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


def _transcribe_audio(client: OpenAI, audio_path: Path) -> str:
    with audio_path.open("rb") as audio_file:
        transcript = client.audio.transcriptions.create(model=settings.transcription_model, file=audio_file)
    return transcript.text.strip()


def _vision_notes(client: OpenAI, frame_paths: list[Path]) -> str:
    if not frame_paths:
        return ""
    sampled = frame_paths[:10]
    content = [{"type": "input_text", "text": "Summarize visible ingredients, actions, cookware, temperatures, and timing clues as bullet points."}]
    for frame in sampled:
        image_b64 = base64.b64encode(frame.read_bytes()).decode("utf-8")
        content.append({"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_b64}"})
    try:
        resp = client.responses.create(model=settings.vision_model, input=[{"role": "user", "content": content}])
        return (resp.output_text or "").strip()
    except Exception:
        return ""


def _recipe_prompt(transcript: str, vision_notes: str) -> str:
    return f"""
You are a recipe extraction system. Return STRICT JSON ONLY with this schema:
{{
  "title": string,
  "servings": number|null,
  "total_time_minutes": number|null,
  "ingredients": [{{"item": string, "quantity": number|null, "unit": string|null, "prep": string|null}}],
  "steps": [{{"n": number, "text": string, "timer_seconds": number|null}}],
  "equipment": [string],
  "notes": [string]
}}
No markdown, no prose.

Transcript:
{transcript}

Vision notes:
{vision_notes}
""".strip()


def _generate_recipe(client: OpenAI, transcript: str, vision_notes: str) -> RecipeData:
    prompt = _recipe_prompt(transcript, vision_notes)
    resp = client.responses.create(model=settings.recipe_model, input=prompt)
    text = (resp.output_text or "").strip()

    def parse_recipe(raw: str) -> RecipeData:
        payload = json.loads(raw)
        return RecipeData.model_validate(payload)

    try:
        return parse_recipe(text)
    except (json.JSONDecodeError, ValidationError):
        fix_prompt = f"Fix this into strict valid JSON for the schema only. Return JSON only.\nSchema: {RecipeData.model_json_schema()}\nBad content:\n{text}"
        fixed = client.responses.create(model=settings.recipe_model, input=fix_prompt)
        return parse_recipe((fixed.output_text or "").strip())


def process_recipe(recipe_id: int, storage_dir: Path, db: Session) -> None:
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        return
    recipe.status = "processing"
    recipe.error_message = None
    progress_store[recipe_id] = 5
    db.commit()

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        input_video = storage_dir / "input.mp4"
        audio_path = storage_dir / "audio.wav"
        frames_dir = storage_dir / "frames"

        _extract_audio(input_video, audio_path)
        progress_store[recipe_id] = 25
        frames = _extract_frames(input_video, frames_dir)
        progress_store[recipe_id] = 45

        transcript = _transcribe_audio(client, audio_path)
        recipe.transcript_text = transcript
        db.commit()
        progress_store[recipe_id] = 65

        vision_notes = _vision_notes(client, frames)
        recipe.vision_notes = vision_notes
        db.commit()
        progress_store[recipe_id] = 80

        recipe_data = _generate_recipe(client, transcript, vision_notes)
        recipe.recipe_json = recipe_data.model_dump_json(indent=2)
        recipe.status = "ready"
        progress_store[recipe_id] = 100
        db.commit()
    except Exception as exc:
        recipe.status = "error"
        recipe.error_message = str(exc)
        progress_store[recipe_id] = 100
        db.commit()
