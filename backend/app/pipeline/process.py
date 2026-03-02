import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import RecipeJob
from app.pipeline.ffmpeg_utils import extract_audio
from app.pipeline.ollama import generate_recipe_json
from app.pipeline.transcribe import transcribe_audio


def _update(db: Session, job: RecipeJob, **kwargs):
    for k, v in kwargs.items():
        setattr(job, k, v)
    db.add(job)
    db.commit()
    db.refresh(job)


def process_recipe_job(job_id: str, db_factory):
    db: Session = db_factory()
    try:
        job = db.get(RecipeJob, job_id)
        if not job:
            return

        _update(db, job, status="processing", progress=5)

        job_dir = Path(job.input_path).parent
        audio_path = job_dir / "audio.wav"
        extract_audio(Path(job.input_path), audio_path)
        _update(db, job, audio_path=str(audio_path), progress=30)

        transcript = transcribe_audio(audio_path)
        _update(db, job, transcript_text=transcript, progress=65)

        recipe = generate_recipe_json(transcript)
        _update(db, job, recipe_json=recipe.model_dump_json(), progress=100, status="ready", error_message=None)
    except Exception as exc:
        if 'job' in locals() and job:
            _update(db, job, status="error", error_message=str(exc), progress=100)
    finally:
        db.close()
