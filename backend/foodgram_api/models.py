from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint
from users.models import User


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=200)
    quantity = models.CharField('Единица измерения', max_length=200)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name}, {self.quantity}'


class Recipe(models.Model):
    name = models.CharField('Название рецепта', max_length=200)
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(Ingredient,
                                         related_name='ingredients',
                                         through='IngredientInRecipe',
                                         verbose_name='Список ингредиентов')
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    cooking_time = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1, 'Значение не может быть меньше 1')],
        verbose_name='Время готовки (мин..)',
    )
    #USERNAME_FIELD = 'author'
    #REQUIRED_FIELDS = ['ingredients', 'tags', 'image', 'name', 'text', 'cooking_time']

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'Значение',
        default=1,
        validators=[
            MinValueValidator(1, 'Значение не может быть меньше 1')]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'


class Tag(models.Model):
    """ Модель тега. """

    name = models.CharField('Название тега', unique=True, max_length=200)
    color = models.CharField('Цвет', unique=True, max_length=7)
    slug = models.SlugField('Slug', unique=True, max_length=200)

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    """ Модель связи тега и рецепта. """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'tag'],
                name='recipe_tag_unique'
            )
        ]
