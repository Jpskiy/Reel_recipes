from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import Base, engine
from app.routes.recipes import router as recipes_router

app = FastAPI(title="Reel Recipes Local MVP")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    Path(settings.STORAGE_DIR).mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(recipes_router)
