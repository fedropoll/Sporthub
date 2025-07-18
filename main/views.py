from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    RegisterSerializer,
    VerifyCodeSerializer,
    CustomTokenObtainPairSerializer
)

class RegisterView(APIView):
    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('Код отправлен', examples={'application/json': {"message": "Код отправлен на почту."}}),
            400: 'Ошибка валидации'
        },
        operation_summary="Регистрация пользователя"
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Код отправлен на почту."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    @swagger_auto_schema(
        request_body=VerifyCodeSerializer,
        responses={
            200: openapi.Response('Подтверждено', examples={'application/json': {"message": "Пользователь подтвержден."}}),
            400: 'Неверный или просроченный код'
        },
        operation_summary="Подтверждение email кода"
    )
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "Пользователь подтвержден."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_summary="Получение JWT токена",
        operation_description="Выдаёт токен по email и паролю",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING),
                "password": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={200: openapi.Response("Успешно")}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
