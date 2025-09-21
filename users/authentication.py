# users/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication

class PlainJWTAuthentication(JWTAuthentication):
    def get_header(self, request):
        """
        Берёт токен из заголовка Authorization без префикса.
        """
        auth = request.META.get('HTTP_AUTHORIZATION', b'')
        if isinstance(auth, str):
            return auth.encode("utf-8")
        return auth

    def get_raw_token(self, header):
        """
        Просто возвращаем токен как есть, без разбора Bearer.
        """
        return header
