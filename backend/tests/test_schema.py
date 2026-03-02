from app.schemas import RecipeData


def test_recipe_schema_validation():
    payload = {
        "title": "Tomato Pasta",
        "servings": 2,
        "total_time_minutes": 20,
        "ingredients": [{"item": "pasta", "quantity": 200, "unit": "g", "prep": None}],
        "steps": [{"n": 1, "text": "Boil pasta", "timer_seconds": 600}],
        "equipment": ["pot"],
        "notes": ["Salt water generously"],
    }
    recipe = RecipeData.model_validate(payload)
    assert recipe.title == "Tomato Pasta"
    assert recipe.ingredients[0].item == "pasta"
