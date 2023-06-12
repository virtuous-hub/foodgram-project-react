from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import permissions, status, viewsets
from foodgram_api.serializers import TokenSerializer
from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ChangePasswordView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not user.check_password(current_password):
            return Response({'Ошибка': 'Текущий пароль введен неверно'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.password = make_password(new_password)
        user.save()

        return Response({'message': 'Пароль успешно изменен'},
                        status=status.HTTP_204_NO_CONTENT)


class Token(CreateAPIView):
    serializer_class = TokenSerializer
    permission_classes = (AllowAny, )

    def create(self, request, *args, **kwargs):
        """Выдает токен."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = request.data.get('password')
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'Ошибка': 'Неверный email или пароль'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(password):
            return Response({'Ошибка': 'Неверный email или пароль'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {'auth_token': str(AccessToken.for_user(user))},
            status=status.HTTP_200_OK)
