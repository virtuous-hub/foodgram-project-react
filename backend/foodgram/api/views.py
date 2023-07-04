import collections

from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from typing import Tuple

from .filters import FilterRecipe, IngredientSearchFilter
from .mixins import AddRemoveMixin
from .pagination import LargeResultsSetPagination
from .permissions import AuthorPermission
from .serializers import (CreateRecipeSerializer, IngredientSerializer,
                          RecipeReadSerializer, TagSerializer)
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet, AddRemoveMixin):
    queryset = Recipe.objects.all()
    permission_classes = (AuthorPermission, IsAuthenticatedOrReadOnly,)
    pagination_class = LargeResultsSetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterRecipe
    serializer_class = CreateRecipeSerializer

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return CreateRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_list__user=request.user
        ).order_by('ingredient__name').values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))

        ingredient_totals: collections.defaultdict[int] = collections.defaultdict(int)
        for ingredient in ingredients:
            key: Tuple[str, str] = (ingredient['ingredient__name'], ingredient['ingredient__measurement_unit'])
            ingredient_totals[key] += ingredient['total_amount']

        ingredient_list = [f"{name} - {int(amount)} {measurement_unit}" for (name, measurement_unit), amount in
                           ingredient_totals.items()]

        shopping_cart = f'{request.user.username}, Ваш список ингредиентов:\n'
        shopping_cart += "\n".join(ingredient_list)

        filename = f"{request.user.username}_shopping.txt"
        response = HttpResponse(shopping_cart, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        return self.add_or_remove(request, pk, request.method == 'POST', Favorite)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        return self.add_or_remove(request, pk, request.method == 'POST', ShoppingCart)
#