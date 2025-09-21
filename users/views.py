from rest_framework import viewsets, permissions, status, mixins, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    UserProfile, Trainer, Hall, Club, Ad, Review, Notification,
    ClassSchedule, Joinclub, UserRole
)
from .serializers import (
    RegisterSerializer, VerifyCodeSerializer, LoginSerializer,
    UserProfileSerializer, TrainerSerializer, HallSerializer, ClubSerializer,
    AdSerializer, ReviewSerializer, NotificationSerializer, ClientDetailSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, ClassScheduleSerializer,
    JoinclubSerializer, RoleTokenSerializer, MyTokenObtainPairSerializer
)
from .utils import generate_and_send_code
from .utils.tokens import create_jwt_tokens_for_user
from .exceptions import AuthenticationFailed, ValidationError, PermissionDenied

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MyLoginView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class AdminChangeUserRoleView(generics.UpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

class GetRoleTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile = request.user.userprofile
        refresh = RefreshToken.for_user(request.user)
        data = {
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'role': user_profile.role
        }
        serializer = RoleTokenSerializer(data)
        return Response(serializer.data)

# -------------------- AUTHENTICATION VIEWS --------------------
class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['🔐 Аутентификация'],
        operation_summary="Регистрация нового пользователя",
        operation_description="""
        Регистрация нового пользователя в системе.
        После успешной регистрации на email приходит код подтверждения.
        """,
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                'Успешная регистрация',
                examples={
                    'application/json': {
                        'message': 'Код подтверждения отправлен на email',
                        'email': 'user@example.com'
                    }
                }
            ),
            400: 'Некорректные данные',
            409: 'Пользователь с таким email уже существует'
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            # Проверяем, существует ли пользователь с таким email
            if User.objects.filter(email=email).exists():
                return Response(
                    {'error': 'Пользователь с таким email уже существует'},
                    status=status.HTTP_409_CONFLICT
                )

            # Создаем пользователя с ролью по умолчанию (USER)
            user = User.objects.create_user(
                username=email,
                email=email,
                password=serializer.validated_data['password'],
                first_name=serializer.validated_data.get('first_name', ''),
                last_name=serializer.validated_data.get('last_name', '')
            )

            # Создаем профиль пользователя с ролью по умолчанию
            UserProfile.objects.create(
                user=user,
                role=UserRole.USER,  # Устанавливаем роль по умолчанию
                phone_number=serializer.validated_data.get('phone_number'),
                birth_date=serializer.validated_data.get('birth_date')
            )

            # Генерируем и отправляем код подтверждения
            code = generate_and_send_code(email)

            return Response(
                {
                    'message': 'Код подтверждения отправлен на email',
                    'email': email
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['🔐 Аутентификация'],
        operation_summary="Подтверждение email по коду",
        operation_description="""
        Подтверждает email пользователя с помощью кода, отправленного при регистрации.
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
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Создаем УНИКАЛЬНЫЕ токены для каждого пользователя
            tokens = create_jwt_tokens_for_user(user)

            return Response({
                'success': True,
                'message': 'Аккаунт успешно активирован',
                'tokens': tokens,
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
    """
    Аутентификация пользователя по email и паролю.
    Возвращает access токен и данные пользователя.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['🔐 Аутентификация'],
        operation_summary="Вход в систему",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                'Успешный вход',
                examples={
                    'application/json': {
                        'access': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                        'user': {
                            'username': 'username',
                            'first_name': 'Имя',
                            'last_name': 'Фамилия',
                            'email': 'email@example.com',
                            'phone_number': '+77001234567',
                            'role': 'user'
                        }
                    }
                }
            ),
            400: 'Неверный формат запроса',
            401: 'Неверные учетные данные',
            403: 'Аккаунт не активирован'
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError({
                'errors': serializer.errors,
                'message': 'Неверный формат запроса'
            })

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed('Неверный email или пароль')

        if not user.check_password(password):
            raise AuthenticationFailed('Неверный email или пароль')

        if not user.is_active:
            raise PermissionDenied('Аккаунт не активирован. Пожалуйста, подтвердите email.')

        refresh = RefreshToken.for_user(user)

        # Определяем роль
        try:
            profile = user.userprofile
            role = profile.role
        except UserProfile.DoesNotExist:
            profile = None
            role = 'admin' if user.is_superuser or user.is_staff else 'user'

        data = {
            "access": str(refresh.access_token),
            "user": {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": getattr(profile, 'phone_number', None) if profile else None,
                "role": role
            }
        }

        return Response(data, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['🔐 Аутентификация'],
        operation_summary="Запрос на восстановление пароля",
        operation_description="""
        Отправляет код подтверждения для сброса пароля на указанный email.
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
        и новый пароль.
        """,
        request_body=ResetPasswordSerializer,
        responses={
            200: openapi.Response('Пароль изменен', examples={
                'application/json': {
                    'success': True,
                    'message': 'Пароль успешно изменен. Теперь вы можете войти с новым паролем'
                }
            }),
            400: openapi.Response('Неверные данные', examples={
                'application/json': {
                    'success': False,
                    'errors': {'code': ['Неверный код верификации']}
                }
            })
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
        Повторно отправляет код верификации на email пользователя.
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
                'application/json': {'success': True, 'message': 'Код отправлен повторно'}
            }),
            400: openapi.Response('Email не найден', examples={
                'application/json': {'success': False, 'errors': {'email': ['Пользователь не найден']}}
            })
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


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['🔐 Аутентификация'],
        operation_summary="Обновление токена доступа",
        operation_description="""
        Обновляет access token с помощью refresh token.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
            }
        ),
        responses={
            200: openapi.Response('Токен обновлен', examples={
                'application/json': {
                    'success': True,
                    'access': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
                }
            }),
            400: openapi.Response('Неверный токен', examples={
                'application/json': {
                    'success': False,
                    'error': 'Неверный refresh token'
                }
            })
        }
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({
                'success': False,
                'error': 'Refresh token обязателен'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Создаем новый access token из refresh token
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            return Response({
                'success': True,
                'access': access_token
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': 'Неверный refresh token'
            }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['🔐 Аутентификация'],
        operation_summary="Выход из системы",
        operation_description="""
        Выход из системы с добавлением refresh token в черный список.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING,
                                          description='Refresh token для добавления в черный список'),
            }
        ),
        responses={
            200: openapi.Response('Успешный выход', examples={
                'application/json': {'success': True, 'message': 'Успешный выход из системы'}
            }),
            400: openapi.Response('Ошибка', examples={
                'application/json': {'success': False, 'error': 'Неверный refresh token'}
            })
        }
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({
                'success': False,
                'error': 'Refresh token обязателен'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Добавляем refresh token в черный список
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                'success': True,
                'message': 'Успешный выход из системы'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'error': 'Неверный refresh token'
            }, status=status.HTTP_400_BAD_REQUEST)


# -------------------- RESOURCE VIEWS --------------------
# Остальные view остаются без изменений, так как они используют стандартную
# аутентификацию JWT, которая теперь будет работать правильно

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary="Получить данные профиля пользователя",
        operation_description="""
        Возвращает данные профиля текущего аутентифицированного пользователя.
        """,
        responses={
            200: openapi.Response('Данные профиля', UserProfileSerializer),
            401: 'Не авторизован',
            404: openapi.Response('Профиль не найден', examples={
                'application/json': {'success': False, 'message': 'Профиль не найден'}
            })
        }
    )
    def retrieve(self, request, pk=None):
        try:
            user_profile = get_object_or_404(UserProfile, user=request.user)
            serializer = self.get_serializer(user_profile)
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Профиль не найден'
            }, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary="Редактировать данные профиля пользователя",
        operation_description="""
        Обновляет данные профиля текущего аутентифицированного пользователя.
        """,
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response('Обновленные данные профиля', UserProfileSerializer),
            400: openapi.Response('Ошибка валидации', examples={
                'application/json': {'success': False, 'errors': {'phone_number': ['Неверный формат номера']}}
            }),
            401: 'Не авторизован',
            404: openapi.Response('Профиль не найден', examples={
                'application/json': {'success': False, 'message': 'Профиль не найден'}
            })
        }
    )
    def update(self, request, pk=None):
        try:
            user_profile = get_object_or_404(UserProfile, user=request.user)
            serializer = self.get_serializer(user_profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Профиль успешно обновлен',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Профиль не найден'
            }, status=status.HTTP_404_NOT_FOUND)

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)


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
    permission_classes = [IsAdminUser]

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
        operation_summary='Обновить информацию о клиенте',
        operation_description="""
        Полное обновление информации о клиенте.
        
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
        Частичное обновление информации о клиенте.
        
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
        if self.action in []:
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
class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    @swagger_auto_schema(
        tags=['🔔 Уведомления'],
        operation_summary="Получить все уведомления",
        operation_description="Возвращает список уведомлений для текущего пользователя",
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description='Поиск по тексту уведомления',
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description='Номер страницы для пагинации',
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: openapi.Response('Список уведомлений', NotificationSerializer(many=True)),
            401: openapi.Response('Не авторизован')
        }
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Применяем поиск если указан параметр search
        search_query = request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(message__icontains=search_query)

        # Применяем пагинацию
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
        operation_summary="Получить список записей на кружки",
        operation_description="""
           Возвращает список всех кружков, на которые записан текущий
           аутентифицированный пользователь. Требуется авторизация.
           """,
        responses={
            200: openapi.Response('Список записей', JoinclubSerializer(many=True)),
            401: 'Не авторизован',
            404: openapi.Response('Записи не найдены или профиль отсутствует', examples={
                'application/json': {'success': False, 'message': 'Профиль пользователя не найден'}})
        }
    )
    def get(self, request):
        try:
            user_profile = get_object_or_404(UserProfile, user=request.user)
        except ObjectDoesNotExist:
            return Response({
                'success': False,
                'message': 'Профиль пользователя не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        joinclubs = Joinclub.objects.filter(user=user_profile)
        serializer = JoinclubSerializer(joinclubs, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

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


class AttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['✅ Посещаемость'],
        operation_summary="Получить статистику посещаемости для всех занятий пользователя",
        operation_description="""
        Возвращает сводку посещаемости для всех занятий, на которые записан текущий
        аутентифицированный пользователь.
        """,
        responses={
            200: openapi.Response('Список сводок посещаемости', examples={
                'application/json': {
                    'success': True,
                    'data': [
                        {'joinclub_id': 1, 'title': 'Волейбол', 'summary': {'present': 10, 'absent': 2, 'total': 12}},
                        {'joinclub_id': 2, 'title': 'Таэквондо', 'summary': {'present': 15, 'absent': 0, 'total': 15}}
                    ]
                }
            }),
            401: 'Не авторизован'
        }
    )
    def get(self, request):
        # Используем get_object_or_404 для получения профиля.
        # Если профиль не существует, DRF автоматически вернет 404.
        user_profile = get_object_or_404(UserProfile, user=request.user)

        # Получаем все записи (joinclub) для текущего пользователя
        # Запрос к базе данных выполняется один раз
        joinclubs = Joinclub.objects.filter(user=user_profile)

        attendance_data = []
        for joinclub in joinclubs:
            # Для каждой записи получаем сводку, используя уже существующий метод
            summary = joinclub.get_attendance_summary
            attendance_data.append({
                'joinclub_id': joinclub.id,
                'title': joinclub.schedule.title,
                'summary': summary
            })

        return Response({
            'success': True,
            'data': attendance_data
        }, status=status.HTTP_200_OK)


def create_jwt_tokens_for_user(user):
    """
    Генерация JWT токенов с информацией о роли пользователя
    """
    refresh = RefreshToken.for_user(user)

    # Добавляем информацию о пользователе в токен
    if hasattr(user, 'userprofile'):
        refresh['role'] = user.userprofile.role
        refresh['first_name'] = user.first_name
        refresh['last_name'] = user.last_name

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
