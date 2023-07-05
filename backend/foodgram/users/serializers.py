from django.contrib.auth.password_validation import validate_password
from djoser.serializers import (SetPasswordSerializer, UserCreateSerializer,
                                UserSerializer)
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import User
from recipes.models import Recipe


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed',)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated and user != obj:
            return obj.following.filter(user=user).exists()
        return False


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name',
            'last_name', 'password'
        )


class CustomSetPasswordSerializer(SetPasswordSerializer):
    default_error_messages = {
        'invalid_password': 'Текущий пароль введен неверно.',
        'password_mismatch': 'Пароли не должны совпадать.'
    }

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        current_password = attrs.get('current_password')

        user = self.context['request'].user
        if not user.check_password(current_password):
            self.fail('current_password')

        elif new_password == current_password:
            self.fail('password_mismatch')

        try:
            validate_password(new_password)
        except ValidationError:
            raise serializers.ValidationError

        return attrs


class SubscribeListSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes_count', 'recipes')
        read_only_fields = ('email', 'username', 'first_name', 'last_name')

    def validate(self, data):
        request = self.context.get('request')
        author_id = request.parser_context['kwargs'].get('id')
        author = get_object_or_404(User, id=author_id)
        user = request.user
        if user.follower.filter(author=author_id).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise PermissionDenied("Нельзя подписаться на самого себя")
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeShortSerializer(recipes, many=True,
                                           context={'request': request})
        return serializer.data
