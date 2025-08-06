from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    RegisterSerializer,
    VerifyCodeSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)
from .utils import generate_and_send_code


class RegisterView(APIView):
    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('Успешная регистрация'),
            400: 'Ошибка валидации'
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "success": True,
                "message": "На адрес электронной почты, который вы указали, должен был прийти четырехзначный код.",
                "email": user.email
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    @swagger_auto_schema(
        request_body=VerifyCodeSerializer,
        responses={
            200: openapi.Response('Успешная верификация'),
            400: 'Неверный код'
        }
    )
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)

            return Response({
                "success": True,
                "message": "Аккаунт успешно активирован",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                },
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            }, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response('Успешный вход'),
            400: 'Неверные данные'
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            remember = serializer.validated_data.get('remember', False)

            refresh = RefreshToken.for_user(user)

            if remember:
                refresh.set_exp(lifetime=refresh.lifetime * 30)

            return Response({
                "success": True,
                "message": "Добро пожаловать!",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                },
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
            }, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    @swagger_auto_schema(
        request_body=ForgotPasswordSerializer,
        responses={
            200: openapi.Response('Код отправлен'),
            400: 'Email не найден'
        }
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            generate_and_send_code(user)

            return Response({
                "success": True,
                "message": "Код для сброса пароля отправлен на ваш адрес электронной почты",
                "email": email
            }, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    @swagger_auto_schema(
        request_body=ResetPasswordSerializer,
        responses={
            200: openapi.Response('Пароль изменен'),
            400: 'Неверные данные'
        }
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            return Response({
                "success": True,
                "message": "Пароль успешно изменен. Теперь вы можете войти с новым паролем"
            }, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResendCodeView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
            }
        ),
        responses={
            200: openapi.Response('Код отправлен повторно'),
            400: 'Email не найден'
        }
    )
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                "success": False,
                "errors": {"email": ["Email обязателен"]}
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            generate_and_send_code(user)
            return Response({
                "success": True,
                "message": "Код отправлен повторно"
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "errors": {"email": ["Пользователь не найден"]}
            }, status=status.HTTP_400_BAD_REQUEST)
