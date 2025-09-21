# users/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions

class PlainJWTAuthentication(JWTAuthentication):
    """
    Принимает токен без префикса Bearer.
    """
    def get_header(self, request):
        """
        Переопределяем получение заголовка.
        Берём токен из 'Authorization' без Bearer.
        """
        auth = request.META.get(self.header_name, b'')
        if isinstance(auth, str):
            auth = auth.encode('utf-8')
        return auth or None

    def get_raw_token(self, header):
        """
        Просто возвращаем заголовок как токен.
        """
        return header.decode('utf-8')
