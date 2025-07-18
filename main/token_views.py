from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("username")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Нет пользователя с таким email")

        if not user.check_password(password):
            raise AuthenticationFailed("Неверный пароль")

        if not user.is_active:
            raise AuthenticationFailed("Пользователь не активен")

        # Получаем токены по username, который связан с email
        data = super().validate({
            "username": user.username,
            "password": password
        })
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
