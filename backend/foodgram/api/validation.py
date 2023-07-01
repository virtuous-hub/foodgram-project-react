from recipes.models import IngredientInRecipe
from rest_framework import serializers


class UniqueRecipeIngredientsValidator:

    def __init__(self, message='Такие ингредиенты уже есть в рецепте'):
        self.message = message

    def validate(self, attrs):
        recipe = attrs.get('recipe')
        ingredients = attrs.get('ingredient')

        if recipe and ingredients:
            existing_ingredients = IngredientInRecipe.objects.filter(
                recipe=recipe, ingredient__in=ingredients
            ).exists()

            if existing_ingredients:
                raise serializers.ValidationError(self.message)

        return attrs