from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TagViewSet, RecipeViewSet
from users.views import UserViewSet, ChangePasswordView, Token

router = DefaultRouter()

router.register('users', UserViewSet, basename='users'),
router.register('tags', TagViewSet, basename='tags'),
router.register(r'recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('set_password/', ChangePasswordView.as_view(), name='change_password'),
    path('auth/token/login', Token.as_view(), name='generate_token'),
]
