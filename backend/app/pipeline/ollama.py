import json

import httpx
from pydantic import ValidationError

from app.config import settings
from app.pipeline.recipe_prompts import SYSTEM_PROMPT, build_repair_prompt, build_user_prompt
from app.schemas import RecipeData


def _call_ollama(prompt: str) -> str:
    payload = {
        "model": settings.RECIPE_MODEL,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
    }
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(f"{settings.OLLAMA_HOST}/api/generate", json=payload)
    resp.raise_for_status()
    data = resp.json()
    return (data.get("response") or "").strip()


def generate_recipe_json(transcript: str) -> RecipeData:
    first = _call_ollama(build_user_prompt(transcript))
    try:
        return RecipeData.model_validate(json.loads(first))
    except (json.JSONDecodeError, ValidationError):
        repaired = _call_ollama(build_repair_prompt(first))
        try:
            return RecipeData.model_validate(json.loads(repaired))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise RuntimeError(f"Ollama returned invalid JSON after retry: {exc}") from exc
