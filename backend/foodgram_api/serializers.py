from rest_framework import serializers
from .models import Ingredient, IngredientInRecipe, Recipe, Tag, RecipeTag

from users.models import User
from users.serializers import UserSerializer

class TokenSerializer(serializers.Serializer):
    """Сериализатор для получения токена."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    class Meta:
        model = User
        fields = ('email')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients',
            'name', 'text', 'cooking_time', 'tags'
        )
