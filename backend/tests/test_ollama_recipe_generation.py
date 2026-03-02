from app import services
from app.schemas import RecipeData


def test_generate_recipe_retries_once_on_invalid_json(monkeypatch):
    calls: list[str] = []
    valid_payload = RecipeData(
        title="Fixed Pasta",
        servings=2,
        total_time_minutes=15,
        ingredients=[{"item": "pasta", "quantity": 200, "unit": "g", "prep": None}],
        steps=[{"n": 1, "text": "Boil water.", "timer_seconds": 600}],
        equipment=["pot"],
        notes=[],
    ).model_dump_json()

    def fake_generate_json(prompt: str, model: str, host: str) -> str:
        calls.append(prompt)
        if len(calls) == 1:
            return '{"title": "Broken",'
        return valid_payload

    monkeypatch.setattr(services, "generate_json", fake_generate_json)

    recipe = services._generate_recipe("boil pasta", "")

    assert recipe.title == "Fixed Pasta"
    assert len(calls) == 2
    assert "Repair this into strict valid JSON only." in calls[1]
