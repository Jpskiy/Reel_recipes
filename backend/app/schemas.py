from typing import Literal

from pydantic import BaseModel, Field


class RecipeData(BaseModel):
    title: str = "Untitled Recipe"
    description: str = ""
    ingredients: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    servings: int | None = None
    notes: str = ""


class RecipeStatusResponse(BaseModel):
    status: Literal["queued", "processing", "ready", "error"]
    progress: float = Field(ge=0, le=100)
    error_message: str | None = None


class RecipeUploadResponse(BaseModel):
    id: str
    status: str


class RecipeRecordResponse(BaseModel):
    id: str
    status: str
    progress: float
    error_message: str | None
    recipe_json: RecipeData | None
    created_at: str
    updated_at: str


class RecipeListItem(BaseModel):
    id: str
    status: str
    progress: float
    created_at: str
