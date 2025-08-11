from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth.models import User, AnonymousUser
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile, ClassSchedule, Joinclub, Attendance, Payment
from .serializers import UserProfileSerializer, ClassScheduleSerializer, JoinclubSerializer, PaymentSerializer, AttendanceSerializer
import stripe
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

stripe.api_key = "sk_test_51RtraO9OcwNpz5T4gdpVXRnB7HoHB5Cq7rnWEDMjNv8qb4vIlbQyhJrnHSKTtMnbTOJVOpfrohM6B7TwNdLGtyfY00fggb3hd9"  # Замените на ваш секретный ключ

# Здесь предполагается, что ваши сериализаторы и модели находятся в тех же местах
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    VerifyCodeSerializer,
    LoginSerializer,
    UserProfileSerializer,
    TrainerSerializer,
    HallSerializer,
    ClubSerializer,
    AdSerializer,
    ReviewSerializer,
    NotificationSerializer,
    ClientDetailSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    VerifyCodeSerializer,
)
from .models import (
    UserProfile,
    PasswordResetCode,
    Trainer,
    Hall,
    Club,
    Ad,
    Review,
    Notification,
    ClassScheduleSerializer,
    JoinclubSerializer,
    PaymentSerializer,
    AttendanceSerializer
)
from .utils import generate_and_send_code


class RegisterView(viewsets.ViewSet):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class RegisterView(APIView):
    @swagger_auto_schema(
        tags=["🔐Аутентификация"],
        operation_summary="Регистрация нового пользователя",
        operation_description="""
        Создаёт нового пользователя. После успешной регистрации на указанный адрес электронной почты
        отправляется четырёхзначный код для верификации.
        """,
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('Успешная регистрация', examples={'application/json': {'success': True, 'message': 'На адрес электронной почты, который вы указали, должен был прийти четырехзначный код.', 'email': 'test@example.com'}}),
            400: openapi.Response('Ошибка валидации', examples={'application/json': {'success': False, 'errors': {'email': ['Пользователь с таким email уже существует.']}}})
        }
        tags=['🔐 Авторизация'],
        operation_summary='Регистрация нового пользователя',
        operation_description='''
        Этот эндпоинт используется для регистрации новых пользователей.
        Пользователь должен предоставить `email`, `password`, `confirmPassword`, `firstName`, `lastName`, `phone_number`, `birth_date`.
        После успешной регистрации пользователю будет отправлен код подтверждения на указанный email.
        Пароли должны совпадать и быть не менее 8 символов.
        ''',
        request_body=RegisterSerializer
    )
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                return Response(
                    {"detail": "Регистрация успешна. На почту отправлен код активации."},
                    status=status.HTTP_201_CREATED,
                )
            except IntegrityError:
                return Response(
                    {"email": ["Пользователь с таким email уже существует."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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


class VerifyCodeView(viewsets.ViewSet):
    serializer_class = VerifyCodeSerializer
    permission_classes = [permissions.AllowAny]

class VerifyCodeView(APIView):
    @swagger_auto_schema(
        tags=["🔐Аутентификация"],
        operation_summary="Верификация аккаунта по коду",
        operation_description="""
        Активирует аккаунт пользователя, используя код, полученный на email.
        После успешной верификации возвращает пару JWT-токенов (access и refresh)
        для дальнейшей работы с API.
        """,
        request_body=VerifyCodeSerializer,
        responses={
            200: openapi.Response('Успешная верификация', examples={'application/json': {'success': True, 'message': 'Аккаунт успешно активирован', 'tokens': {'refresh': '...', 'access': '...'}, 'user': {'id': 1, 'email': 'test@example.com', 'first_name': 'Иван', 'last_name': 'Петров'}}}),
            400: openapi.Response('Неверный код или email', examples={'application/json': {'success': False, 'errors': {'code': ['Неверный код верификации']}}})
        }
        tags=['🔐 Авторизация'],
        operation_summary='Подтверждение кода активации',
        operation_description='''
        Этот эндпоинт используется для активации аккаунта после регистрации.
        Необходимо предоставить `email` и `code` (4-значный код, отправленный на почту).
        После успешной активации пользователь может войти в систему.
        ''',
        request_body=VerifyCodeSerializer
    )
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                {"detail": "Аккаунт успешно активирован"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=['🔐 Авторизация'],
        operation_summary='Вход в систему',
        operation_description='''
        Эндпоинт для входа в систему.
        Необходимо предоставить `email` и `password`.
        Возвращает пару токенов (access и refresh) для аутентификации.
        ''',
        request_body=LoginSerializer
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )

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

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch', 'put']
    lookup_field = 'pk'

    def get_object(self):
        return self.request.user.userprofile

    def get_queryset(self):
        if isinstance(self.request.user, AnonymousUser):
            return UserProfile.objects.none()
        if self.action in ['retrieve', 'update', 'partial_update']:
            return UserProfile.objects.filter(user=self.request.user)
        return UserProfile.objects.all()

class LoginView(APIView):
    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary='Получить данные профиля'
        tags=["🔐Аутентификация"],
        operation_summary="Вход пользователя",
        operation_description="""
        Аутентифицирует пользователя по email и паролю. Возвращает JWT-токены
        для авторизованного доступа к API. Если флаг `remember` установлен,
        срок действия refresh-токена будет увеличен.
        """,
        request_body=LoginSerializer,
        responses={
            200: openapi.Response('Успешный вход', examples={'application/json': {'success': True, 'message': 'Добро пожаловать!', 'tokens': {'refresh': '...', 'access': '...'}, 'user': {'id': 1, 'email': 'test@example.com', 'first_name': 'Иван', 'last_name': 'Петров'}}}),
            400: openapi.Response('Неверные данные', examples={'application/json': {'success': False, 'errors': {'detail': 'Неверные учётные данные'}}})
        }
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
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
        tags=["🔐Аутентификация"],
        operation_summary="Отправка кода для сброса пароля",
        operation_description="""
        Отправляет код для сброса пароля на email, если пользователь с таким
        адресом существует.
        """,
        tags=['👤 Профиль пользователя'],
        operation_summary='Обновить данные профиля (частично)',
        operation_description='''
        Частично обновляет данные профиля текущего аутентифицированного пользователя.
        Можно обновить `first_name`, `last_name`, `email`, `phone_number`, `birth_date`, `gender`, `address`.
        ''',
        request_body=UserProfileSerializer
    )
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary='Полное обновление профиля',
        request_body=UserProfileSerializer
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary='Получить список всех профилей (только для администраторов)',
        operation_description='''
        **Внимание: этот эндпоинт доступен только для администраторов.**
        Возвращает список всех профилей пользователей.
        '''
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()


class PasswordResetView(viewsets.ViewSet):
    @swagger_auto_schema(
        tags=['🔐 Авторизация'],
        operation_summary='Запрос на сброс пароля',
        request_body=ForgotPasswordSerializer,
        responses={
            200: openapi.Response('Код отправлен', examples={'application/json': {'success': True, 'message': 'Код для сброса пароля отправлен на ваш адрес электронной почты', 'email': 'test@example.com'}}),
            400: openapi.Response('Email не найден', examples={'application/json': {'success': False, 'errors': {'email': ['Пользователь с таким email не найден.']}}})
        }
        operation_description='''
        Запрашивает код для сброса пароля.
        На указанный `email` будет отправлен 4-значный код.
        '''
    )
    def post(self, request):
    @action(detail=False, methods=['post'], url_path='request')
    def request_reset(self, request):
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
        if serializer.is_valid(raise_exception=True):
            user = get_object_or_404(User, email=serializer.validated_data['email'])
            code = PasswordResetCode.generate_code()
            PasswordResetCode.objects.create(user=user, code=code)
            return Response({'detail': 'Код сброса пароля успешно отправлен.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    @swagger_auto_schema(
        tags=['🔐 Авторизация'],
        operation_summary='Сброс пароля с помощью кода',
        tags=["🔐Аутентификация"],
        operation_summary="Сброс пароля",
        operation_description="""
        Позволяет сбросить пароль пользователя, используя email, код верификации
        и новый пароль. Код должен быть предварительно отправлен через `ForgotPasswordView`.
        """,
        request_body=ResetPasswordSerializer,
        operation_description='''
        Сбрасывает пароль, используя `email`, `code` (полученный по почте) и новый пароль.
        '''
        responses={
            200: openapi.Response('Пароль изменен', examples={'application/json': {'success': True, 'message': 'Пароль успешно изменен. Теперь вы можете войти с новым паролем'}}),
            400: openapi.Response('Неверные данные', examples={'application/json': {'success': False, 'errors': {'code': ['Неверный код верификации']}}})
        }
    )
    @action(detail=False, methods=['post'], url_path='confirm')
    def confirm_reset(self, request):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'detail': 'Пароль успешно изменен.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = ClientDetailSerializer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ['get', 'delete']

    @swagger_auto_schema(
        tags=['👨‍👩‍👧‍👦 Клиенты'],
        operation_summary='Получить список всех клиентов',
        operation_description='''
        Эндпоинт доступен только для администраторов.
        Возвращает полный список всех зарегистрированных клиентов.
        '''
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['👨‍👩‍👧‍👦 Клиенты'],
        operation_summary='Получить детали клиента',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID клиента", type=openapi.TYPE_INTEGER)
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['👨‍👩‍👧‍👦 Клиенты'],
        operation_summary='Удалить клиента',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID клиента", type=openapi.TYPE_INTEGER)
        ]
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user_instance = instance.user
        user_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HallViewSet(viewsets.ModelViewSet):
    queryset = Hall.objects.all()
    serializer_class = HallSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()

    @swagger_auto_schema(
        tags=['🏟️ Залы'],
        operation_summary='Получить список всех залов',
        operation_description='''
        Возвращает список всех спортивных залов. Доступен для всех.
        '''
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Залы'],
        operation_summary='Создать новый зал',
        operation_description='''
        Создает новый спортивный зал. Доступен только для администраторов.
        ''',
        request_body=HallSerializer
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

            return Response({
                "success": True,
                "message": "Пароль успешно изменен. Теперь вы можете войти с новым паролем"
            }, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(
        tags=['🏟️ Залы'],
        operation_summary='Получить детали зала',
        operation_description='''
        Возвращает подробную информацию о конкретном зале по его ID. Доступен для всех.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID зала", type=openapi.TYPE_INTEGER)
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Залы'],
        operation_summary='Обновить зал (полное обновление)',
        operation_description='''
        Полностью обновляет информацию о зале. Доступен только для администраторов.
        ''',
        request_body=HallSerializer,
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID зала", type=openapi.TYPE_INTEGER)
        ]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Залы'],
        operation_summary='Обновить зал (частичное обновление)',
        operation_description='''
        Частично обновляет информацию о зале. Доступен только для администраторов.
        ''',
        request_body=HallSerializer,
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID зала", type=openapi.TYPE_INTEGER)
        ]
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Залы'],
        operation_summary='Удалить зал',
        operation_description='''
        Удаляет зал по его ID. Доступен только для администраторов.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID зала", type=openapi.TYPE_INTEGER)
        ]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ClubViewSet(viewsets.ModelViewSet):
    queryset = Club.objects.all()
    serializer_class = ClubSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()

    @swagger_auto_schema(
        tags=['🤸‍♂️ Клубы'],
        operation_summary='Получить список всех клубов',
        operation_description='''
        Возвращает список всех спортивных клубов. Доступен для всех.
        '''
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🤸‍♂️ Клубы'],
        operation_summary='Создать новый клуб',
        operation_description='''
        Создает новый спортивный клуб. Доступен только для администраторов.
        ''',
        request_body=ClubSerializer
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🤸‍♂️ Клубы'],
        operation_summary='Получить детали клуба',
        operation_description='''
        Возвращает подробную информацию о конкретном клубе по его ID. Доступен для всех.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID клуба", type=openapi.TYPE_INTEGER)
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class ResendCodeView(APIView):
    @swagger_auto_schema(
        tags=["🔐Аутентификация"],
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
            200: openapi.Response('Код отправлен повторно', examples={'application/json': {'success': True, 'message': 'Код отправлен повторно'}}),
            400: openapi.Response('Email не найден', examples={'application/json': {'success': False, 'errors': {'email': ['Пользователь не найден']}}})
        }
        tags=['🤸‍♂️ Клубы'],
        operation_summary='Обновить клуб (полное обновление)',
        operation_description='''
        Полностью обновляет информацию о клубе. Доступен только для администраторов.
        ''',
        request_body=ClubSerializer,
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID клуба", type=openapi.TYPE_INTEGER)
        ]
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

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🤸‍♂️ Клубы'],
        operation_summary='Обновить клуб (частичное обновление)',
        operation_description='''
        Частично обновляет информацию о клубе. Доступен только для администраторов.
        ''',
        request_body=ClubSerializer,
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID клуба", type=openapi.TYPE_INTEGER)
        ]
        tags=['👤Профиль пользователя'],
        operation_summary="Получить данные профиля пользователя",
        operation_description="""
        Возвращает данные профиля (UserProfile) текущего аутентифицированного пользователя.
        Требуется авторизация.
        """,
        responses={
            200: openapi.Response('Данные профиля', UserProfileSerializer),
            401: 'Не авторизован',
            404: openapi.Response('Профиль не найден', examples={'application/json': {'success': False, 'message': 'Профиль не найден'}})
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    def get(self, request):
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(user_profile)
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
        tags=['🤸‍♂️ Клубы'],
        operation_summary='Удалить клуб',
        operation_description='''
        Удаляет клуб по его ID. Доступен только для администраторов.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID клуба", type=openapi.TYPE_INTEGER)
        ]
        tags=['👤Профиль пользователя'],
        operation_summary="Редактировать данные профиля пользователя",
        operation_description="""
        Обновляет данные профиля (UserProfile) текущего аутентифицированного пользователя.
        Используется `partial=True`, что позволяет обновлять только некоторые поля.
        Требуется авторизация.
        """,
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response('Обновленные данные профиля', UserProfileSerializer),
            400: openapi.Response('Ошибка валидации', examples={'application/json': {'success': False, 'errors': {'phone_number': ['Неверный формат номера']}}}),
            401: 'Не авторизован',
            404: openapi.Response('Профиль не найден', examples={'application/json': {'success': False, 'message': 'Профиль не найден'}})
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class TrainerViewSet(viewsets.ModelViewSet):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()
    def put(self, request):
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
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

class ClassScheduleView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        tags=['💪 Тренеры'],
        operation_summary='Получить список всех тренеров',
        operation_description='''
        Возвращает список всех тренеров. Доступен для всех.
        '''
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
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get(self, request):
        schedules = ClassSchedule.objects.all()
        serializer = ClassScheduleSerializer(schedules, many=True)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
    @swagger_auto_schema(
        tags=['💪 Тренеры'],
        operation_summary='Создать нового тренера',
        operation_description='''
        Создает нового тренера. Доступен только для администраторов.
        ''',
        request_body=TrainerSerializer
    tags=['📅Расписание'],
    operation_summary="Создать новое расписание",
    operation_description="""
    Создаёт новую запись в расписании занятий. Требуется авторизация и,
    вероятно, соответствующие права администратора (хотя в коде это явно
    не указано).
    """,
        request_body=ClassScheduleSerializer,
        responses={
            201: openapi.Response('Расписание создано', ClassScheduleSerializer),
            400: openapi.Response('Неверные данные', examples={'application/json': {'success': False, 'errors': {'title': ['Это поле обязательно.']}}}),
            401: 'Не авторизован'
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    def post(self, request):
        serializer = ClassScheduleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Расписание успешно создано", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class JoinclubView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        tags=['💪 Тренеры'],
        operation_summary='Получить детали тренера',
        operation_description='''
        Возвращает подробную информацию о конкретном тренере по его ID. Доступен для всех.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID тренера", type=openapi.TYPE_INTEGER)
        ]
        tags=['✅Записаться на кружок'],
        operation_summary="Получить список записей на кружки",
        operation_description="""
        Возвращает список всех кружков, на которые записан текущий аутентифицированный
        пользователь. Требуется авторизация.
        """,
        responses={
            200: openapi.Response('Список записей', JoinclubSerializer(many=True)),
            401: 'Не авторизован',
            404: openapi.Response('Записи не найдены или профиль отсутствует', examples={'application/json': {'success': False, 'message': 'Профиль пользователя не найден'}})
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    def get(self, request):
        try:
            user_profile = request.user.userprofile
        except UserProfile.DoesNotExist:
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
        tags=['💪 Тренеры'],
        operation_summary='Обновить тренера (полное обновление)',
        operation_description='''
        Полностью обновляет информацию о тренере. Доступен только для администраторов.
        ''',
        request_body=TrainerSerializer,
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID тренера", type=openapi.TYPE_INTEGER)
        ]
        tags=['✅Записаться на кружок'],
        operation_summary="Создать новую запись на кружок",
        operation_description="""
        Позволяет текущему аутентифицированному пользователю записаться на
        выбранное занятие из расписания. Проверяет, что пользователь
        ещё не записан на это занятие. Требуется авторизация.
        """,
        request_body=JoinclubSerializer,
        responses={
            201: openapi.Response('Запись создана', JoinclubSerializer),
            400: openapi.Response('Неверные данные или запись уже существует', examples={'application/json': {'success': False, 'message': 'Запись на этот кружок уже существует'}}),
            401: 'Не авторизован'
        }
    )
    def post(self, request):
        user_profile = request.user.userprofile
        serializer = JoinclubSerializer(data=request.data, context={'user': user_profile})
        if serializer.is_valid():
            schedule_id = request.data.get('schedule')
            if Joinclub.objects.filter(user=user_profile, schedule_id=schedule_id).exists():
                return Response({
                    'success': False,
                    'message': 'Запись на этот кружок уже существует'
                }, status=status.HTTP_400_BAD_REQUEST)
            serializer.save(user=user_profile)
            return Response({
                'success': True,
                'message': 'Запись успешно создана',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)




class PaymentView(APIView):
    permission_classes = [IsAuthenticated]
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['💪 Тренеры'],
        operation_summary='Обновить тренера (частичное обновление)',
        operation_description='''
        Частично обновляет информацию о тренере. Доступен только для администраторов.
        ''',
        request_body=TrainerSerializer,
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID тренера", type=openapi.TYPE_INTEGER)
        ]
        tags=['💳Оплата'],
        operation_summary="Получить список оплат для конкретной записи",
        operation_description="Возвращает список всех оплат, связанных с конкретной записью на кружок (`joinclub`). Требуется авторизация, и пользователь должен быть владельцем `joinclub`.",
        responses={
            200: openapi.Response('Список оплат', PaymentSerializer(many=True)),
            401: 'Не авторизован',
            404: openapi.Response('Joinclub не найден', examples={'application/json': {'success': False, 'message': 'Joinclub не найден'}})
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    def get(self, request, joinclub_id):
        try:
            joinclub_instance = Joinclub.objects.get(id=joinclub_id, user=request.user.userprofile)
            payments = Payment.objects.filter(joinclub=joinclub_instance)
            serializer = PaymentSerializer(payments, many=True)
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Joinclub.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Joinclub не найден'
            }, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        tags=['💪 Тренеры'],
        operation_summary='Удалить тренера',
        operation_description='''
        Удаляет тренера по его ID. Доступен только для администраторов.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID тренера", type=openapi.TYPE_INTEGER)
        ]
        tags=['💳Оплата'],
        operation_summary="Создать новую оплату",
        operation_description="Создаёт новую запись об оплате для конкретной записи на кружок (`joinclub`). Использует Stripe для обработки платежа. Требуется авторизация, и пользователь должен быть владельцем `joinclub`.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['amount', 'stripe_token'],
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Сумма оплаты в валюте'),
                'currency': openapi.Schema(type=openapi.TYPE_STRING, description='Валюта (по умолчанию USD)', default='usd'),
                'stripe_token': openapi.Schema(type=openapi.TYPE_STRING, description='Токен карты от Stripe.js'),
            }
        ),
        responses={
            201: openapi.Response('Оплата создана', examples={'application/json': {'success': True, 'message': 'Оплата успешно инициирована', 'data': {'id': 1, 'amount': '100.00'}, 'clientSecret': '...'}}),
            400: openapi.Response('Неверные данные', examples={'application/json': {'success': False, 'errors': {'amount': ['Это поле обязательно.']}}}),
            401: 'Не авторизован',
            404: openapi.Response('Запись Joinclub не найдена', examples={'application/json': {'success': False, 'message': 'Запись Joinclub не найдена'}})
        }
    )
    def post(self, request, joinclub_id):
        logger.debug("Received data: %s", request.data)
        try:
            joinclub_instance = Joinclub.objects.get(id=joinclub_id, user=request.user.userprofile)
            amount = request.data.get('amount')
            currency = request.data.get('currency', 'usd')
            stripe_token = request.data.get('stripe_token')

            if not amount or not stripe_token:
                return Response({
                    'success': False,
                    'errors': {'amount': ['Это поле обязательно'], 'stripe_token': ['Токен карты обязателен']}
                }, status=status.HTTP_400_BAD_REQUEST)
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

            # Валидация суммы
            try:
                amount_float = float(amount)
                if amount_float <= 0:
                    return Response({
                        'success': False,
                        'errors': {'amount': ['Сумма должна быть положительной']}
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'errors': {'amount': ['Сумма должна быть числом']}
                }, status=status.HTTP_400_BAD_REQUEST)

class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer
            # Создание платежного намерения через Stripe
            intent = stripe.PaymentIntent.create(
                amount=int(amount_float * 100),  # Конвертация в центы
                currency=currency,
                payment_method_data={
                    "type": "card",
                    "card": {
                        "token": stripe_token
                    }
                },
                confirmation_method='manual',
                confirm=True,
                description=f"Оплата за {joinclub_instance.schedule.title}",
                return_url="http://127.0.0.1:8000/swagger/"
            )

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()
            # Проверка статуса платежа
            if intent.status == 'succeeded':
                payment_data = {
                    'joinclub': joinclub_id,  # Передаем ID вместо объекта
                    'amount': amount_float,
                    'stripe_payment_intent_id': intent.id
                }
                serializer = PaymentSerializer(data=payment_data)
                if serializer.is_valid():
                    payment = serializer.save()
                    return Response({
                        'success': True,
                        'message': 'Оплата успешно завершена',
                        'data': serializer.data,
                        'clientSecret': intent.client_secret
                    }, status=status.HTTP_201_CREATED)
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'message': f'Платеж не завершен. Статус: {intent.status}. Попробуйте еще раз.'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Joinclub.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Запись Joinclub не найдена'
            }, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            logger.error("Stripe error: %s", str(e))
            return Response({
                'success': False,
                'errors': {'stripe': [str(e)]}
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Unexpected error: %s", str(e))
            return Response({
                'success': False,
                'errors': {'general': ['Произошла ошибка на сервере']}
            }, status=status.HTTP_400_BAD_REQUEST)

class AttendanceView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        tags=['📣 Объявления'],
        operation_summary='Получить список всех объявлений',
        operation_description='''
        Возвращает список всех активных объявлений. Доступен для всех.
        '''
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📣 Объявления'],
        operation_summary='Создать новое объявление',
        operation_description='''
        Создает новое объявление. Доступен только для администраторов.
        ''',
        request_body=AdSerializer
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📣 Объявления'],
        operation_summary='Получить детали объявления',
        operation_description='''
        Возвращает подробную информацию о конкретном объявлении по его ID. Доступен для всех.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID объявления", type=openapi.TYPE_INTEGER)
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📣 Объявления'],
        operation_summary='Обновить объявление (полное обновление)',
        operation_description='''
        Полностью обновляет информацию об объявлении. Доступен только для администраторов.
        ''',
        request_body=AdSerializer,
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID объявления", type=openapi.TYPE_INTEGER)
        ]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📣 Объявления'],
        operation_summary='Обновить объявление (частичное обновление)',
        operation_description='''
        Частично обновляет информацию об объявлении. Доступен только для администраторов.
        ''',
        request_body=AdSerializer,
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID объявления", type=openapi.TYPE_INTEGER)
        ]
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📣 Объявления'],
        operation_summary='Удалить объявление',
        operation_description='''
        Удаляет объявление по его ID. Доступен только для администраторов.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID объявления", type=openapi.TYPE_INTEGER)
        ]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['list', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser]
        elif self.action == 'retrieve':
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()

    @swagger_auto_schema(
        tags=['💬 Отзывы'],
        operation_summary='Получить список всех отзывов',
        operation_description='''
        Возвращает список всех отзывов. Доступен только для администраторов.
        '''
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['💬 Отзывы'],
        operation_summary='Создать новый отзыв',
        operation_description='''
        Создает новый отзыв. Требуется аутентификация пользователя.
        ''',
        request_body=ReviewSerializer
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['💬 Отзывы'],
        operation_summary='Получить детали отзыва',
        operation_description='''
        Возвращает подробную информацию о конкретном отзыве по его ID. Доступен для всех.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID отзыва", type=openapi.TYPE_INTEGER)
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['💬 Отзывы'],
        operation_summary='Обновить отзыв (полное обновление)',
        operation_description='''
        Полностью обновляет информацию об отзыве. Доступен только для администраторов.
        ''',
        request_body=ReviewSerializer,
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID отзыва", type=openapi.TYPE_INTEGER)
        ]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['💬 Отзывы'],
        operation_summary='Обновить отзыв (частичное обновление)',
        operation_description='''
        Частично обновляет информацию об отзыве. Доступен только для администраторов.
        ''',
        request_body=ReviewSerializer,
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID отзыва", type=openapi.TYPE_INTEGER)
        ]
        tags=['📊Cписок посещаемости'],
        operation_summary="Получить список посещаемости и сводку",
        operation_description="""
        Возвращает список всех записей о посещаемости для конкретной записи на кружок (`joinclub`).
        Также включает сводку посещаемости (количество присутствий, отсутствий и общее количество).
        Требуется авторизация, и пользователь должен быть владельцем `joinclub`.
        """,
        responses={
            200: openapi.Response('Список посещаемости', AttendanceSerializer(many=True)),
            401: 'Не авторизован',
            404: openapi.Response('Запись Joinclub не найдена', examples={'application/json': {'success': False, 'message': 'Запись Joinclub не найдена'}})
        }
    )
    def get(self, request, joinclub_id):
        try:
            joinclub_instance = Joinclub.objects.get(id=joinclub_id, user=request.user.userprofile)
            attendances = Attendance.objects.filter(joinclub=joinclub_instance)
            serializer = AttendanceSerializer(attendances, many=True)
            summary = attendances.first().get_attendance_summary if attendances.exists() else {'present': 0, 'absent': 0, 'total': 0}
            return Response({
                'success': True,
                'data': serializer.data,
                'summary': {
                    'present_count': summary['present'],
                    'absent_count': summary['absent'],
                    'total_count': summary['total']
                }
            }, status=status.HTTP_200_OK)
        except Joinclub.DoesNotExist:
            return Response({'success': False, 'message': 'Запись Joinclub не найдена'}, status=status.HTTP_404_NOT_FOUND)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['💬 Отзывы'],
        operation_summary='Удалить отзыв',
        operation_description='''
        Удаляет отзыв по его ID. Доступен только для администраторов.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID отзыва", type=openapi.TYPE_INTEGER)
        ]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ['get', 'delete']

    @swagger_auto_schema(
        tags=['🔔 Уведомления'],
        operation_summary='Получить список всех уведомлений',
        operation_description='''
        Возвращает список всех уведомлений. Доступен только для администраторов.
        '''
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🔔 Уведомления'],
        operation_summary='Получить детали уведомления',
        operation_description='''
        Возвращает подробную информацию о конкретном уведомлении по его ID. Доступен только для администраторов.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID уведомления", type=openapi.TYPE_INTEGER)
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🔔 Уведомления'],
        operation_summary='Удалить уведомление',
        operation_description='''
        Удаляет уведомление по его ID. Доступен только для администраторов.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID уведомления", type=openapi.TYPE_INTEGER)
        ]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)