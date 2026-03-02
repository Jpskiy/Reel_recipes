import json
import shutil
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, SessionLocal, engine, get_db
from .models import Recipe
from .schemas import RecipeData, RecipeListItem, RecipeResponse, RecipeUpdateRequest, StatusResponse, UploadResponse
from .services import process_recipe, progress_store

app = FastAPI(title="Reel Recipes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
storage_root = Path(__file__).resolve().parents[1] / settings.storage_dir
storage_root.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm"}


def _recipe_to_response(recipe: Recipe) -> RecipeResponse:
    recipe_data = None
    if recipe.recipe_json:
        recipe_data = RecipeData.model_validate(json.loads(recipe.recipe_json))
    return RecipeResponse(
        id=recipe.id,
        created_at=recipe.created_at,
        status=recipe.status,
        source_filename=recipe.source_filename,
        transcript_text=recipe.transcript_text,
        vision_notes=recipe.vision_notes,
        recipe=recipe_data,
        error_message=recipe.error_message,
    )


def _run_pipeline(recipe_id: int, recipe_storage: Path) -> None:
    with SessionLocal() as db:
        process_recipe(recipe_id=recipe_id, storage_dir=recipe_storage, db=db)


@app.post("/api/recipes/upload", response_model=UploadResponse)
async def upload_recipe(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    recipe = Recipe(source_filename=file.filename or "upload", status="uploaded")
    db.add(recipe)
    db.commit()
    db.refresh(recipe)

    recipe_dir = storage_root / str(recipe.id)
    recipe_dir.mkdir(parents=True, exist_ok=True)
    destination = recipe_dir / "input.mp4"
    with destination.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    progress_store[recipe.id] = 0
    background_tasks.add_task(_run_pipeline, recipe.id, recipe_dir)
    return UploadResponse(id=recipe.id, status=recipe.status)


@app.get("/api/recipes/{recipe_id}/status", response_model=StatusResponse)
def get_status(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return StatusResponse(status=recipe.status, progress=progress_store.get(recipe_id, 0), error=recipe.error_message)


@app.get("/api/recipes/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return _recipe_to_response(recipe)


@app.put("/api/recipes/{recipe_id}", response_model=RecipeResponse)
def update_recipe(recipe_id: int, payload: RecipeUpdateRequest, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    recipe.recipe_json = payload.recipe.model_dump_json(indent=2)
    recipe.status = "ready"
    db.commit()
    db.refresh(recipe)
    return _recipe_to_response(recipe)


@app.get("/api/recipes", response_model=list[RecipeListItem])
def list_recipes(db: Session = Depends(get_db)):
    rows = db.scalars(select(Recipe).order_by(Recipe.created_at.desc()).limit(20)).all()
    return [RecipeListItem(id=r.id, created_at=r.created_at, status=r.status, source_filename=r.source_filename) for r in rows]
