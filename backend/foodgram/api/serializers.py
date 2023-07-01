from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.serializers import CustomUserSerializer, RecipeShortSerializer

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id',
                  'name',
                  'measurement_unit',)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class IngredientRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount',)


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeWriteSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        error_messages={'does_not_exist': 'Указанного тега не существует'}
    )
    image = Base64ImageField(max_length=None)
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
        )

    def create_ingredients(self, recipe, ingredients_data):
        ingredients = []
        for ingredient_data in ingredients_data:
            ingredient = IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount'],
            )
            ingredients.append(ingredient)

        with transaction.atomic():
            IngredientInRecipe.objects.bulk_create(ingredients)

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)

        if image:
            recipe.image = image

        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        recipe.save()

        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        instance.tags.set(validated_data.pop('tags'))
        ingredients = validated_data.pop('ingredients')
        self.create_ingredients(instance, ingredients)

        image = validated_data.pop('image', None)
        if image:
            instance.image = image
            instance.save()

        return super().update(instance, validated_data)

    def validate_ingredients(self, data):
        ingredients = data

        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужен хоть один ингредиент для рецепта'})

        seen_ingredients = []

        for ingredient_item in ingredients:
            ingredient_id = ingredient_item['id']

            if ingredient_id in seen_ingredients:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться'
                )

            seen_ingredients.append(ingredient_id)

            amount = int(ingredient_item['amount'])
            if amount < 0:
                raise serializers.ValidationError({
                    'ingredients': ('Убедитесь, что значение количества '
                                    'ингредиента больше 0')
                })

        return data

    def validate_tags(self, tags):
        for tag in tags:

            if not Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(
                    'Указанного тега не существует'
                )
        return tags

    def validate_cooking_time(self, cooking_time):
        if cooking_time < 1:
            raise serializers.ValidationError(
                'Время готовки не должно быть менее 1 минуты'
            )
        return cooking_time

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=False, many=True)
    author = CustomUserSerializer(read_only=True, many=False)
    ingredients = IngredientRecipeSerializer(
        source='ingredienttorecipe',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(max_length=None)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.shopping_list.filter(user=request.user).exists()


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')

        if user and recipe and user.favorites.filter(recipe=recipe).exists():
            raise ValidationError('Рецепт уже добавлен в избранное.')

        return data

    def to_representation(self, instance):
        recipe = instance.recipe
        request = self.context.get('request')
        return RecipeShortSerializer(recipe, context={'request': request}).data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')

        if user and recipe and user.shopping_list.filter(
                recipe=recipe).exists():
            raise ValidationError('Рецепт уже добавлен в корзину.')

        return data

    def to_representation(self, instance):
        recipe = instance.recipe
        request = self.context.get('request')
        return RecipeShortSerializer(recipe, context={'request': request}).data
