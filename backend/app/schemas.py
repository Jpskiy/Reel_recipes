from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    item: str
    quantity: float | None = None
    unit: str | None = None
    prep: str | None = None


class Step(BaseModel):
    n: int
    text: str
    timer_seconds: int | None = None


class RecipeData(BaseModel):
    title: str
    servings: float | None = None
    total_time_minutes: int | None = None
    ingredients: list[Ingredient] = Field(default_factory=list)
    steps: list[Step] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class UploadResponse(BaseModel):
    id: int
    status: str


class StatusResponse(BaseModel):
    status: Literal["uploaded", "processing", "ready", "error"]
    progress: int = Field(ge=0, le=100)
    error: str | None = None


class RecipeResponse(BaseModel):
    id: int
    created_at: datetime
    status: str
    source_filename: str
    transcript_text: str
    vision_notes: str
    recipe: RecipeData | None = None
    error_message: str | None = None


class RecipeUpdateRequest(BaseModel):
    recipe: RecipeData


class RecipeListItem(BaseModel):
    id: int
    created_at: datetime
    status: str
    source_filename: str
