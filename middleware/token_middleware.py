from django.utils.deprecation import MiddlewareMixin
from users.utils.tokens import get_user_from_token


class TokenValidationMiddleware(MiddlewareMixin):
    """
    Middleware для дополнительной валидации JWT токенов
    """

    def process_request(self, request):
        # Пропускаем анонимные запросы и запросы без авторизации
        if not request.user.is_authenticated and 'HTTP_AUTHORIZATION' in request.META:
            user = get_user_from_token(request)
            if user:
                request.user = user