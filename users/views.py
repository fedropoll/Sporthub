from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User, AnonymousUser
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import (
    UserProfile, PasswordResetCode, Trainer, Hall, Club, Ad, Review, Notification,
    ClassSchedule, Joinclub, Payment, Attendance
)
from .serializers import (
    UserSerializer, RegisterSerializer, VerifyCodeSerializer, LoginSerializer,
    UserProfileSerializer, TrainerSerializer, HallSerializer, ClubSerializer,
    AdSerializer, ReviewSerializer, NotificationSerializer, ClientDetailSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, ClassScheduleSerializer,
    JoinclubSerializer, PaymentSerializer, AttendanceSerializer
)
from .utils import generate_and_send_code

import logging
import stripe
import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

stripe.api_key = "sk_test_51RtraO9OcwNpz5T4gdpVXRnB7HoHB5Cq7rnWEDMjNv8qb4vIlbQyhJrnHSKTtMnbTOJVOpfrohM6B7TwNdLGtyfY00fggb3hd9"


# -------------------- AUTHENTICATION VIEWS --------------------
class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['🔐 Аутентификация'],
        operation_summary="Регистрация нового пользователя",
        operation_description="""
        Создаёт нового пользователя в системе. После успешной регистрации
        на указанный email отправляется код подтверждения.
        
        ### Обязательные поля:
        - `email` - адрес электронной почты
        - `password` - пароль (минимум 8 символов)
        - `first_name` - имя пользователя
        - `last_name` - фамилия пользователя
        
        ### Ответ при успехе:
        - `success: true`
        - `message` - сообщение об успешной регистрации
        - `email` - email, на который отправлен код подтверждения
        """,
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                'Успешная регистрация',
                examples={
                    'application/json': {
                        'success': True,
                        'message': 'Код подтверждения отправлен на ваш email',
                        'email': 'user@example.com'
                    }
                }
            ),
            400: openapi.Response(
                'Ошибка валидации',
                examples={
                    'application/json': {
                        'success': False,
                        'errors': {'email': ['Этот email уже зарегистрирован']}
                    }
                }
            )
        }
    )
    def post(self, request):
        """
        Обрабатывает запрос на регистрацию нового пользователя.
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "success": True,
                "message": "Код подтверждения отправлен на ваш email",
                "email": user.email
            }, status=status.HTTP_201_CREATED)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['🔐 Аутентификация'],
        operation_summary="Подтверждение email по коду",
        operation_description="""
        Подтверждает email пользователя с помощью кода, отправленного при регистрации.
        
        ### Обязательные поля:
        - `email` - email, на который был отправлен код
        - `code` - 4-значный код подтверждения
        
        ### Ответ при успехе:
        - `success: true`
        - `message` - сообщение об успешной активации
        - `tokens` - JWT токены для аутентификации
        - `user` - данные пользователя
        """,
        request_body=VerifyCodeSerializer,
        responses={
            200: openapi.Response(
                'Успешная верификация',
                examples={
                    'application/json': {
                        'success': True,
                        'message': 'Аккаунт успешно активирован',
                        'tokens': {
                            'refresh': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                            'access': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
                        },
                        'user': {
                            'id': 1,
                            'email': 'user@example.com',
                            'first_name': 'Иван',
                            'last_name': 'Иванов'
                        }
                    }
                }
            ),
            400: openapi.Response(
                'Ошибка валидации',
                examples={
                    'application/json': {
                        'success': False,
                        'errors': {'code': ['Неверный код подтверждения']}
                    }
                }
            )
        }
    )
    def post(self, request):
        """
        Обрабатывает запрос на подтверждение email по коду.
        """
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'success': True,
                'message': 'Аккаунт успешно активирован',
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['🔐 Аутентификация'],
        operation_summary="Вход в аккаунт",
        operation_description="""
        Аутентификация пользователя по email и паролю.
        
        ### Обязательные поля:
        - `email` - адрес электронной почты
        - `password` - пароль
        
        ### Ответ при успехе:
        - `success: true`
        - `tokens` - JWT токены для аутентификации
        - `user` - данные пользователя
        """,
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                'Успешная аутентификация',
                examples={
                    'application/json': {
                        'success': True,
                        'tokens': {
                            'refresh': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                            'access': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
                        },
                        'user': {
                            'id': 1,
                            'email': 'user@example.com',
                            'first_name': 'Иван',
                            'last_name': 'Иванов',
                            'is_active': True,
                            'is_staff': False
                        }
                    }
                }
            ),
            400: openapi.Response(
                'Ошибка аутентификации',
                examples={
                    'application/json': {
                        'success': False,
                        'error': 'Неверный email или пароль'
                    }
                }
            )
        }
    )
    def post(self, request):
        """
        Обрабатывает запрос на вход в аккаунт.
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'success': True,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff
                }
            })
        return Response({
            'success': False,
            'error': 'Неверный email или пароль'
        }, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['🔐 Аутентификация'],
        operation_summary="Запрос на восстановление пароля",
        operation_description="""
        Отправляет код подтверждения для сброса пароля на указанный email.
        
        ### Обязательные поля:
        - `email` - адрес электронной почты
        
        ### Ответ при успехе:
        - `success: true`
        - `message` - сообщение об отправке кода
        - `email` - email, на который отправлен код
        """,
        request_body=ForgotPasswordSerializer,
        responses={
            200: openapi.Response(
                'Код отправлен',
                examples={
                    'application/json': {
                        'success': True,
                        'message': 'Код подтверждения отправлен на ваш email',
                        'email': 'user@example.com'
                    }
                }
            ),
            404: openapi.Response(
                'Пользователь не найден',
                examples={
                    'application/json': {
                        'success': False,
                        'error': 'Пользователь с таким email не найден'
                    }
                }
            )
        }
    )
    def post(self, request):
        """
        Обрабатывает запрос на восстановление пароля.
        """
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                # Здесь должна быть логика отправки кода подтверждения
                return Response({
                    'success': True,
                    'message': 'Код подтверждения отправлен на ваш email',
                    'email': email
                })
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Пользователь с таким email не найден'
                }, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['🔐 Аутентификация'],
        operation_summary="Сброс пароля",
        operation_description="""
        Позволяет сбросить пароль пользователя, используя email, код верификации
        и новый пароль. Код должен быть предварительно отправлен через `ForgotPasswordView`.
        """,
        request_body=ResetPasswordSerializer,
        responses={
            200: openapi.Response('Пароль изменен', examples={'application/json': {'success': True,
                                                                                   'message': 'Пароль успешно изменен. Теперь вы можете войти с новым паролем'}}),
            400: openapi.Response('Неверные данные', examples={
                'application/json': {'success': False, 'errors': {'code': ['Неверный код верификации']}}})
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
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['🔐 Аутентификация'],
        operation_summary="Повторная отправка кода верификации",
        operation_description="""
        Повторно отправляет код верификации на email пользователя. Может
        использоваться как для активации аккаунта, так и для сброса пароля.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Email пользователя'),
            }
        ),
        responses={
            200: openapi.Response('Код отправлен повторно', examples={
                'application/json': {'success': True, 'message': 'Код отправлен повторно'}}),
            400: openapi.Response('Email не найден', examples={
                'application/json': {'success': False, 'errors': {'email': ['Пользователь не найден']}}})
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


# -------------------- RESOURCE VIEWS --------------------
class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary='оплзователи',
    )
    def get_permissions(self):
        """
        Переопределение прав доступа в зависимости от действия.
        """
        if self.action in ['list']:
            return [IsAdminUser()]
        elif self.action in ['retrieve']:
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrReadOnly()]
        return super().get_permissions()

    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary='Список профилей (только для администраторов)',
        operation_description="""
        Возвращает список всех профилей пользователей.
        
        ### Фильтрация:
        - `user__email` - фильтр по email пользователя
        - `phone` - фильтр по номеру телефона
        - `birth_date` - фильтр по дате рождения
        
        ### Сортировка:
        - `?ordering=user__first_name` - сортировка по имени
        - `?ordering=-created_at` - сортировка по дате создания (новые сначала)
        """,
        manual_parameters=[
            openapi.Parameter('user__email', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Фильтр по email'),
            openapi.Parameter('phone', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Фильтр по номеру телефона'),
            openapi.Parameter('birth_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, format='date', description='Фильтр по дате рождения (YYYY-MM-DD)')
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary='Детали профиля',
        operation_description="""
        Возвращает детальную информацию о профиле пользователя.
        
        ### Ответ содержит:
        - Основная информация о пользователе (имя, email, телефон и т.д.)
        - Ссылки на аватар
        - Дополнительные данные профиля
        """
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary='Обновление профиля',
        operation_description="""
        Полное обновление данных профиля.
        
        ### Доступные поля для обновления:
        - `phone` - номер телефона
        - `birth_date` - дата рождения (YYYY-MM-DD)
        - `gender` - пол (M - мужской, F - женский)
        - `avatar` - аватар пользователя (изображение)
        - `address` - адрес проживания
        
        ### Примечания:
        - Для загрузки аватара используйте `multipart/form-data`
        - Все поля, кроме аватара, можно обновлять по отдельности
        """
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary='Частичное обновление профиля',
        operation_description="""
        Частичное обновление данных профиля.
        
        Позволяет обновить только указанные поля профиля.
        
        ### Пример запроса:
        ```json
        {
            "phone": "+77771234567",
            "address": "г. Алматы, ул. Примерная, 123"
        }
        ```
        """
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary='Удаление профиля (только для администраторов)',
        operation_description="""
        Удаление профиля пользователя.
        
        ### Внимание:
        - Удаление профиля необратимо
        - Удаляются все связанные данные пользователя
        - Доступно только администраторам
        """
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """
        Возвращает queryset в зависимости от прав пользователя.
        """
        queryset = super().get_queryset()

        # Админы видят все профили
        if self.request.user.is_staff:
            return queryset

        # Обычные пользователи видят только свой профиль
        return queryset.filter(user=self.request.user)


class ClientViewSet(viewsets.ModelViewSet):
    """
    API для управления клиентами.

    ### Разрешения:
    - `list`: Доступно только администраторам и тренерам
    - `create`: Только администраторы
    - `retrieve/update/partial_update/destroy`: Только администраторы

    ### Фильтрация:
    - `user__email` - фильтр по email клиента
    - `phone` - фильтр по номеру телефона
    """
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = ClientDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Настройка прав доступа в зависимости от действия.
        """
        if self.action in ['list']:
            return [IsAdminUser()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @swagger_auto_schema(
        tags=['👥 Управление клиентами'],
        operation_summary='Список клиентов',
        operation_description="""
        Возвращает список клиентов.
        
        ### Доступ:
        - Администраторы видят всех клиентов
        - Тренеры видят только своих клиентов
        
        ### Фильтрация:
        - `user__email` - фильтр по email
        - `phone` - фильтр по номеру телефона
        - `trainer` - ID тренера (для администраторов)
        """,
        manual_parameters=[
            openapi.Parameter('user__email', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Фильтр по email'),
            openapi.Parameter('phone', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Фильтр по номеру телефона'),
            openapi.Parameter('trainer', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='ID тренера (только для администраторов)')
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['👥 Управление клиентами'],
        operation_summary='Добавление нового клиента',
        operation_description="""
        Создание нового клиента.
        
        ### Обязательные поля:
        - `user` - ID пользователя
        - `phone` - номер телефона
        - `birth_date` - дата рождения (YYYY-MM-DD)
        
        ### Опциональные поля:
        - `address` - адрес проживания
        - `notes` - примечания
        - `trainer` - ID тренера (если не указан, будет назначен текущий пользователь)
        """
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['👥 Управление клиентами'],
        operation_summary='Детали клиента',
        operation_description="""
        Возвращает детальную информацию о клиенте.
        
        ### Включает:
        - Основные данные клиента
        - Историю посещений
        - Активные абонементы
        - Примечания
        """
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['👥 Управление клиентами'],
        operation_summary='Обновление данных клиента',
        operation_description="""
        Полное обновление данных клиента.
        
        ### Внимание:
        - Все поля, кроме указанных, будут перезаписаны значениями по умолчанию
        - Для частичного обновления используйте PATCH
        """
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['👥 Управление клиентами'],
        operation_summary='Частичное обновление клиента',
        operation_description="""
        Частичное обновление данных клиента.
        
        ### Пример запроса:
        ```json
        {
            "phone": "+77771234567",
            "notes": "Предпочитает утренние тренировки"
        }
        ```
        """
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['👥 Управление клиентами'],
        operation_summary='Удаление клиента',
        operation_description="""
        Удаление клиента из системы.
        
        ### Внимание:
        - Удаление клиента необратимо
        - Будут также удалены все связанные записи о посещениях и абонементах
        - Доступно только администраторам
        """
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """
        Возвращает queryset в зависимости от прав пользователя.
        """
        queryset = super().get_queryset()

        # Администраторы видят всех клиентов
        if self.request.user.is_staff:
            return queryset

        if hasattr(self.request.user, 'trainer_profile'):
            return queryset.filter(trainer=self.request.user.trainer_profile)

        # Обычные пользователи не видят клиентов
        return queryset.none()


class HallViewSet(viewsets.ModelViewSet):
    queryset = Hall.objects.all()
    serializer_class = HallSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    @swagger_auto_schema(
        tags=['🏟️ Залы (для админа)'],
        operation_summary='Получить список залов',
        operation_description='Возвращает список всех залов. Доступно всем пользователям.'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Залы (для админа)'],
        operation_summary='Получить детали зала',
        operation_description='Возвращает детальную информацию о конкретном зале. Доступно всем пользователям.'
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Залы (для админа)'],
        operation_summary='Создать новый зал',
        operation_description='Создаёт новый зал. Доступно только администраторам.'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Залы (для админа)'],
        operation_summary='Обновить информацию о зале',
        operation_description='Полностью обновляет информацию о зале. Доступно только администраторам.'
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Залы (для админа)'],
        operation_summary='Частично обновить информацию о зале',
        operation_description='Частично обновляет информацию о зале. Доступно только администраторам.'
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Залы (для админа)'],
        operation_summary='Удалить зал',
        operation_description='Удаляет зал. Доступно только администраторам.'
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# Клубы
class ClubViewSet(viewsets.ModelViewSet):
    queryset = Club.objects.all()
    serializer_class = ClubSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    @swagger_auto_schema(tags=['🏀 Клубы (для админа)'],operation_summary='Получить список клубов', operation_description='Возвращает список всех клубов.')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=['🏀 Клубы (для админа)'], operation_summary='Получить детали клуба', operation_description='Возвращает детальную информацию о конкретном клубе.')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=['🏀 Клубы (для админа)'], operation_summary='Создать новый клуб', operation_description='Создает новый клуб. Доступно только администраторам.')
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=['🏀 Клубы (для админа)'], operation_summary='Обновить информацию о клубе', operation_description='Полное обновление информации о клубе. Доступно только администраторам.')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['🏀 Клубы (для админа)'], operation_summary='Частично обновить клуб', operation_description='Частичное обновление информации о клубе. Доступно только администраторам.')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['🏀 Клубы (для админа)'], operation_summary='Удалить клуб', operation_description='Удаляет клуб. Доступно только администраторам.')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# Тренеры
class TrainerViewSet(viewsets.ModelViewSet):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    @swagger_auto_schema(tags=['🏋️ Тренеры (для админа)'],operation_summary='Получить список тренеров', operation_description='Возвращает список всех тренеров.')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=['🏋️ Тренеры (для админа)'], operation_summary='Получить детали тренера', operation_description='Возвращает детальную информацию о конкретном тренере.')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=['🏋️ Тренеры (для админа)'], operation_summary='Создать нового тренера', operation_description='Создает нового тренера. Доступно только администраторам.')
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=['🏋️ Тренеры (для админа)'], operation_summary='Обновить информацию о тренере', operation_description='Полное обновление информации о тренере. Доступно только администраторам.')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['🏋️ Тренеры (для админа)'], operation_summary='Частично обновить данные тренера', operation_description='Частичное обновление информации о тренере. Доступно только администраторам.')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['🏋️ Тренеры (для админа)'], operation_summary='Удалить тренера', operation_description='Удаляет тренера. Доступно только администраторам.')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# Объявления
class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    @swagger_auto_schema(tags=['📢 Объявления (для админа)'], operation_summary='Получить список объявлений', operation_description='Возвращает список всех объявлений. Доступно всем.')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=['📢 Объявления (для админа)'], operation_summary='Получить детали объявления', operation_description='Возвращает детальную информацию о конкретном объявлении. Доступно всем.')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=['📢 Объявления (для админа)'], operation_summary='Создать новое объявление', operation_description='Создает новое объявление. Доступно только администраторам.')
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=['📢 Объявления (для админа)'], operation_summary='Обновить объявление', operation_description='Полное обновление объявления. Доступно только администраторам.')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['📢 Объявления (для админа)'], operation_summary='Частично обновить объявление', operation_description='Частичное обновление объявления. Доступно только администраторам.')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['📢 Объявления (для админа)'], operation_summary='Удалить объявление', operation_description='Удаляет объявление. Доступно только администраторам.')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# Отзывы
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminUser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    @swagger_auto_schema(tags=['📝 Отзывы (для админа)'], operation_summary='Получить список отзывов', operation_description='Возвращает список всех отзывов. Доступно всем.')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=['📝 Отзывы (для админа)'],operation_summary='Получить детали отзыва', operation_description='Возвращает детальную информацию об отзыве. Доступно всем.')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы (для админа)'],
        operation_summary='Создать новый отзыв',
        operation_description='Создает новый отзыв от имени текущего пользователя. Доступно только администраторам.'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=['📝 Отзывы (для админа)'], operation_summary='Обновить отзыв', operation_description='Полное обновление отзыва. Доступно только администраторам.')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['📝 Отзывы (для админа)'], operation_summary='Частично обновить отзыв', operation_description='Частичное обновление отзыва. Доступно только администраторам.')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=['📝 Отзывы (для админа)'], operation_summary='Удалить отзыв', operation_description='Удаляет отзыв. Доступно только администраторам.')
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


# Уведомления
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create', 'mark_as_read']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        tags=['🔔 Уведомления'],
        operation_summary='Получить список уведомлений',
        operation_description='Возвращает список уведомлений для текущего пользователя. Доступно только авторизованным пользователям.')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🔔 Уведомления'],
        operation_summary='Получить детали уведомления',
        operation_description='Возвращает детальную информацию об уведомлении для текущего пользователя. Доступно только авторизованным пользователям.')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🔔 Уведомления'],
        operation_summary='Создать уведомление',
        operation_description='Создает новое уведомление для текущего пользователя. Доступно только авторизованным пользователям.')
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🔔 Уведомления'],
        operation_summary='Отметить уведомление как прочитанное',
        operation_description='Помечает конкретное уведомление как прочитанное. Доступно только авторизованным пользователям.',
        responses={200: 'Уведомление успешно помечено как прочитанное.'}
    )
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(status=status.HTTP_200_OK)
class ClassScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['📅Расписание'],
        operation_summary="Получить список расписаний",
        operation_description="""
        Возвращает список всех доступных расписаний занятий. Требуется авторизация.
        """,
        responses={
            200: openapi.Response('Список расписаний', ClassScheduleSerializer(many=True)),
            401: 'Не авторизован'
        }
    )
    def get(self, request):
        schedules = ClassSchedule.objects.all()
        serializer = ClassScheduleSerializer(schedules, many=True)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['📅Расписание'],
        operation_summary="Создать новое расписание",
        operation_description="""
        Создаёт новую запись в расписании занятий. Доступно только для администраторов.
        """,
        request_body=ClassScheduleSerializer,
        responses={
            201: openapi.Response('Расписание создано', ClassScheduleSerializer),
            400: openapi.Response('Неверные данные', examples={
                'application/json': {'success': False, 'errors': {'title': ['Это поле обязательно.']}}}),
            401: 'Не авторизован'
        }
    )
    def post(self, request):
        if not request.user.is_staff:
            return Response({"detail": "У вас нет прав для выполнения этого действия."},
                            status=status.HTTP_403_FORBIDDEN)
        serializer = ClassScheduleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class JoinclubView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['🎉 Записи на занятия'],
        operation_summary="Записаться на занятие",
        operation_description="""
        Записывает текущего пользователя на выбранное занятие. Требуется авторизация.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['schedule'],
            properties={
                'schedule': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID расписания'),
                'age_group': openapi.Schema(type=openapi.TYPE_STRING,
                                            description='Возрастная группа (Adult, Teen, Child)'),
            }
        ),
        responses={
            201: openapi.Response('Успешная запись', examples={
                'application/json': {'success': True, 'message': 'Вы успешно записаны на занятие!'}}),
            400: 'Ошибка валидации',
            401: 'Не авторизован',
            409: openapi.Response('Конфликт', examples={
                'application/json': {'success': False, 'message': 'Вы уже записаны на это занятие.'}})
        }
    )
    def post(self, request):
        user_profile = get_object_or_404(UserProfile, user=request.user)
        schedule_id = request.data.get('schedule')
        age_group = request.data.get('age_group', 'Adult')

        schedule = get_object_or_404(ClassSchedule, pk=schedule_id)
        if Joinclub.objects.filter(user=user_profile, schedule=schedule).exists():
            return Response({"success": False, "message": "Вы уже записаны на это занятие."},
                            status=status.HTTP_409_CONFLICT)

        joinclub = Joinclub.objects.create(user=user_profile, schedule=schedule, age_group=age_group)
        return Response({"success": True, "message": "Вы успешно записаны на занятие!", "joinclub_id": joinclub.id},
                        status=status.HTTP_201_CREATED)


class PaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['💳 Оплата'],
        operation_summary="Провести оплату",
        operation_description="""
        Создаёт платёжный намерение через Stripe и возвращает `client_secret`.
        После успешной оплаты создаётся запись об оплате.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['amount', 'payment_method_id'],
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Сумма оплаты'),
                'payment_method_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                    description='ID платежного метода Stripe'),
            }
        ),
        responses={
            200: openapi.Response('Оплата успешна', examples={
                'application/json': {'success': True, 'message': 'Оплата прошла успешно', 'payment_intent_id': 'pi_...'}
                }),
            400: 'Неверные данные',
            401: 'Не авторизован',
            404: 'Запись не найдена'
        }
    )
    def post(self, request, joinclub_id):
        joinclub = get_object_or_404(Joinclub, pk=joinclub_id, user__user=request.user)
        amount = request.data.get('amount')
        payment_method_id = request.data.get('payment_method_id')

        if not all([amount, payment_method_id]):
            return Response({"success": False, "errors": "Необходимо указать сумму и ID платежного метода."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount),
                currency='usd',  # Можно изменить на 'kgs' или другую валюту
                payment_method=payment_method_id,
                confirm=True,
                off_session=False,
            )

            Payment.objects.create(
                joinclub=joinclub,
                stripe_payment_intent_id=intent.id,
                amount=amount,
            )
            return Response({"success": True, "message": "Оплата прошла успешно", "payment_intent_id": intent.id},
                            status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({"success": False, "errors": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['✅ Посещаемость'],
        operation_summary="Получить статистику посещаемости",
        operation_description="""
        Возвращает сводку посещаемости для конкретной записи на занятие (`joinclub_id`).
        """,
        responses={
            200: openapi.Response('Сводка посещаемости', examples={
                'application/json': {'success': True, 'data': {'present': 10, 'absent': 2, 'total': 12}}}),
            401: 'Не авторизован',
            404: 'Запись на занятие не найдена'
        }
    )
    def get(self, request, joinclub_id):
        joinclub = get_object_or_404(Joinclub, pk=joinclub_id, user__user=request.user)
        summary = joinclub.get_attendance_summary
        return Response({"success": True, "data": summary}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['✅ Посещаемость'],
        operation_summary="Отметить посещаемость",
        operation_description="""
        Создаёт новую запись о посещении для конкретного занятия. Доступно только для администраторов.
        """,
        request_body=AttendanceSerializer,
        responses={
            201: openapi.Response('Посещение отмечено', AttendanceSerializer),
            400: 'Ошибка валидации',
            401: 'Не авторизован',
            403: 'Нет прав доступа'
        }
    )
    def post(self, request, joinclub_id):
        if not request.user.is_staff:
            return Response({"detail": "У вас нет прав для выполнения этого действия."},
                            status=status.HTTP_403_FORBIDDEN)

        joinclub = get_object_or_404(Joinclub, pk=joinclub_id)
        serializer = AttendanceSerializer(data=request.data, context={'joinclub': joinclub})
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)