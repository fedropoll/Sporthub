from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()


def create_jwt_tokens_for_user(user):
    """
    Создает уникальные JWT токены для конкретного пользователя
    """
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def get_user_from_token(request):
    """
    Извлекает пользователя из JWT токена
    """
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from rest_framework import exceptions

    jwt_authenticator = JWTAuthentication()

    try:
        # Получаем сырой токен из заголовка
        raw_token = jwt_authenticator.get_raw_token(request)
        if not raw_token:
            return None

        # Валидируем токен
        validated_token = jwt_authenticator.get_validated_token(raw_token)

        # Получаем пользователя из токена
        user = jwt_authenticator.get_user(validated_token)
        return user

    except (exceptions.AuthenticationFailed, AttributeError, TypeError):
        return None


def verify_token_validity(token):
    """
    Проверяет валидность JWT токена
    """
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from rest_framework import exceptions

    jwt_authenticator = JWTAuthentication()

    try:
        validated_token = jwt_authenticator.get_validated_token(token)
        return True, validated_token
    except exceptions.AuthenticationFailed:
        return False, None