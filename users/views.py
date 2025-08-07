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
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)
from .utils import generate_and_send_code

class RegisterOrLoginView(APIView):
    @swagger_auto_schema(
        tags=['🔐 Authentication API'],
        operation_summary='регистрация/авторизация',
        operation_description=(
            "Регистрация нового пользователя или вход, если пользователь уже существует.\n\n"
            "- Если email не зарегистрирован — создаётся новый пользователь и отправляется код подтверждения.\n"
            "- Если пользователь уже есть и пароль верный — происходит вход.\n"
            "- Если пользователь есть, но не активирован — код отправляется повторно."
        ),
        request_body=RegisterSerializer,
        responses={
            200: openapi.Response('Успешный вход'),
            201: openapi.Response('Успешная регистрация'),
            400: 'Ошибка валидации или неверные данные'
        }
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        remember = request.data.get('remember', False)

        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response({
                    "success": False,
                    "errors": {"password": "Неверный пароль"}
                }, status=status.HTTP_400_BAD_REQUEST)

            if not user.is_active:
                generate_and_send_code(user)
                return Response({
                    "success": False,
                    "message": "Аккаунт не активирован. Код отправлен повторно на почту.",
                    "email": user.email
                }, status=status.HTTP_400_BAD_REQUEST)

            refresh = RefreshToken.for_user(user)
            if remember:
                from datetime import timedelta
                refresh.set_exp(lifetime=timedelta(days=30))

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

        except User.DoesNotExist:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                return Response({
                    "success": True,
                    "message": "На почту отправлен код подтверждения.",
                    "email": user.email
                }, status=status.HTTP_201_CREATED)
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    @swagger_auto_schema(
        tags=['🔐 Authentication API'],
        operation_summary='подверждение кода',
        operation_description=(
            "Подтверждение кода, отправленного на email. После успешной верификации аккаунт активируется и выдаются токены."
        ),
        request_body=VerifyCodeSerializer,
        responses={
            200: openapi.Response('Успешная верификация'),
            400: 'Неверный код',
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


class ForgotPasswordView(APIView):
    @swagger_auto_schema(
        tags=['🔐 Authentication API'],
        operation_summary= 'отправка кода для сброса пароля',
        operation_description=(
            "Отправка кода для сброса пароля на указанный email. "
            "Код можно использовать для восстановления доступа."
        ),
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
        tags=['🔐 Authentication API'],
        operation_summary='меняет пароль аккаунта',
        operation_description=(
            "Сброс пароля по email и коду подтверждения. "
            "После успешного сброса можно войти с новым паролем."
        ),
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
        tags=['🔐 Authentication API'],
        operation_summary='повторное отправка кода для регистрации',
        operation_description=(
            "Повторная отправка кода подтверждения на email. "
            "Используется, если предыдущий код не дошёл или истёк."
        ),
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

class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=404)

        if user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response({'error': 'Неверный пароль'}, status=400)