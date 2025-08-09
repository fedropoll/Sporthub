from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth.models import User, AnonymousUser
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

# Здесь предполагается, что ваши сериализаторы и модели находятся в тех же местах
from .serializers import (
    UserSerializer,
    RegisterSerializer,
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
)


class RegisterView(viewsets.ViewSet):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
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


class VerifyCodeView(viewsets.ViewSet):
    serializer_class = VerifyCodeSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
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

    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary='Получить данные профиля'
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @swagger_auto_schema(
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
        operation_description='''
        Запрашивает код для сброса пароля.
        На указанный `email` будет отправлен 4-значный код.
        '''
    )
    @action(detail=False, methods=['post'], url_path='request')
    def request_reset(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = get_object_or_404(User, email=serializer.validated_data['email'])
            code = PasswordResetCode.generate_code()
            PasswordResetCode.objects.create(user=user, code=code)
            return Response({'detail': 'Код сброса пароля успешно отправлен.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=['🔐 Авторизация'],
        operation_summary='Сброс пароля с помощью кода',
        request_body=ResetPasswordSerializer,
        operation_description='''
        Сбрасывает пароль, используя `email`, `code` (полученный по почте) и новый пароль.
        '''
    )
    @action(detail=False, methods=['post'], url_path='confirm')
    def confirm_reset(self, request):
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

    @swagger_auto_schema(
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
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🤸‍♂️ Клубы'],
        operation_summary='Удалить клуб',
        operation_description='''
        Удаляет клуб по его ID. Доступен только для администраторов.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID клуба", type=openapi.TYPE_INTEGER)
        ]
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

    @swagger_auto_schema(
        tags=['💪 Тренеры'],
        operation_summary='Получить список всех тренеров',
        operation_description='''
        Возвращает список всех тренеров. Доступен для всех.
        '''
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['💪 Тренеры'],
        operation_summary='Создать нового тренера',
        operation_description='''
        Создает нового тренера. Доступен только для администраторов.
        ''',
        request_body=TrainerSerializer
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['💪 Тренеры'],
        operation_summary='Получить детали тренера',
        operation_description='''
        Возвращает подробную информацию о конкретном тренере по его ID. Доступен для всех.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID тренера", type=openapi.TYPE_INTEGER)
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

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
    )
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
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['💪 Тренеры'],
        operation_summary='Удалить тренера',
        operation_description='''
        Удаляет тренера по его ID. Доступен только для администраторов.
        ''',
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="ID тренера", type=openapi.TYPE_INTEGER)
        ]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [permissions.AllowAny]
        else:
            self.permission_classes = [permissions.IsAdminUser]
        return super().get_permissions()

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
    )
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