from django.shortcuts import get_object_or_404
from recipes.models import Recipe
from rest_framework import status
from rest_framework.response import Response

from .serializers import RecipeReadSerializer


class AddRemoveMixin:
    model = None

    def add_or_remove(self, request, pk, add, model):
        if not model:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if add:
            obj, _ = model.objects.get_or_create(
                recipe=recipe, user=user
            )
        else:
            obj = model.objects.filter(
                recipe=recipe, user=user
            ).first()
            if obj:
                obj.delete()

        serializer_context = {'request': request}
        serializer = RecipeReadSerializer(
            recipe,
            context=serializer_context
        )
        return Response(serializer.data)
