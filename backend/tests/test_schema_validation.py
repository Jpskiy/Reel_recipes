import pytest
from pydantic import ValidationError

from app.schemas import RecipeData


def test_recipe_data_validates():
    data = RecipeData.model_validate({"title": "Soup", "ingredients": ["water"], "steps": ["boil"]})
    assert data.title == "Soup"


def test_recipe_data_rejects_wrong_types():
    with pytest.raises(ValidationError):
        RecipeData.model_validate({"title": "Soup", "ingredients": "water", "steps": ["boil"]})
