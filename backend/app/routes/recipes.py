import json
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal, get_db
from app.models import RecipeJob
from app.pipeline.process import process_recipe_job
from app.schemas import RecipeData, RecipeListItem, RecipeRecordResponse, RecipeStatusResponse, RecipeUploadResponse

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


def _job_to_record(job: RecipeJob) -> RecipeRecordResponse:
    parsed = RecipeData.model_validate(json.loads(job.recipe_json)) if job.recipe_json else None
    return RecipeRecordResponse(
        id=job.id,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        recipe_json=parsed,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
    )


@router.post("/upload", response_model=RecipeUploadResponse)
async def upload_recipe(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Upload exceeds MAX_UPLOAD_MB ({settings.MAX_UPLOAD_MB})")

    job = RecipeJob(status="queued", progress=0, input_path="")
    db.add(job)
    db.commit()
    db.refresh(job)

    job_dir = Path(settings.STORAGE_DIR) / job.id
    job_dir.mkdir(parents=True, exist_ok=True)
    input_path = job_dir / "input.mp4"
    input_path.write_bytes(data)

    job.input_path = str(input_path)
    db.add(job)
    db.commit()

    background_tasks.add_task(process_recipe_job, job.id, SessionLocal)
    return RecipeUploadResponse(id=job.id, status=job.status)


@router.get("/{recipe_id}/status", response_model=RecipeStatusResponse)
def get_recipe_status(recipe_id: str, db: Session = Depends(get_db)):
    job = db.get(RecipeJob, recipe_id)
    if not job:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return RecipeStatusResponse(status=job.status, progress=job.progress, error_message=job.error_message)


@router.get("/{recipe_id}", response_model=RecipeRecordResponse)
def get_recipe(recipe_id: str, db: Session = Depends(get_db)):
    job = db.get(RecipeJob, recipe_id)
    if not job:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return _job_to_record(job)


@router.put("/{recipe_id}", response_model=RecipeRecordResponse)
def update_recipe(recipe_id: str, payload: RecipeData, db: Session = Depends(get_db)):
    job = db.get(RecipeJob, recipe_id)
    if not job:
        raise HTTPException(status_code=404, detail="Recipe not found")
    job.recipe_json = payload.model_dump_json()
    db.add(job)
    db.commit()
    db.refresh(job)
    return _job_to_record(job)


@router.get("", response_model=list[RecipeListItem])
def list_recipes(db: Session = Depends(get_db)):
    jobs = db.query(RecipeJob).order_by(desc(RecipeJob.created_at)).limit(25).all()
    return [
        RecipeListItem(id=j.id, status=j.status, progress=j.progress, created_at=j.created_at.isoformat())
        for j in jobs
    ]
