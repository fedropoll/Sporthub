from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User, AnonymousUser
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
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
        tags=["🔐Аутентификация"],
        operation_summary="Регистрация нового пользователя",
        operation_description="""
        Создаёт нового пользователя. После успешной регистрации на указанный адрес электронной почты
        отправляется четырёхзначный код для верификации.
        """,
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('Успешная регистрация', examples={'application/json': {'success': True,
                                                                                         'message': 'На адрес электронной почты, который вы указали, должен был прийти четырехзначный код.',
                                                                                         'email': 'test@example.com'}}),
            400: openapi.Response('Ошибка валидации', examples={'application/json': {'success': False, 'errors': {
                'email': ['Пользователь с таким email уже существует.']}}})
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
    permission_classes = [AllowAny]

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
            200: openapi.Response('Успешная верификация', examples={
                'application/json': {'success': True, 'message': 'Аккаунт успешно активирован',
                                     'tokens': {'refresh': '...', 'access': '...'},
                                     'user': {'id': 1, 'email': 'test@example.com', 'first_name': 'Иван',
                                              'last_name': 'Петров'}}}),
            400: openapi.Response('Неверный код или email', examples={
                'application/json': {'success': False, 'errors': {'code': ['Неверный код верификации']}}})
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
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=["🔐Аутентификация"],
        operation_summary="Вход пользователя",
        operation_description="""
        Аутентифицирует пользователя по email и паролю. Возвращает JWT-токены
        для авторизованного доступа к API. Если флаг `remember` установлен,
        срок действия refresh-токена будет увеличен.
        """,
        request_body=LoginSerializer,
        responses={
            200: openapi.Response('Успешный вход', examples={
                'application/json': {'success': True, 'message': 'Добро пожаловать!',
                                     'tokens': {'refresh': '...', 'access': '...'},
                                     'user': {'id': 1, 'email': 'test@example.com', 'first_name': 'Иван',
                                              'last_name': 'Петров'}}}),
            400: openapi.Response('Неверные данные', examples={
                'application/json': {'success': False, 'errors': {'detail': 'Неверные учётные данные'}}})
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            remember = serializer.validated_data.get('remember', False)

            refresh = RefreshToken.for_user(user)
            if remember:
                # Устанавливаем срок действия refresh-токена на 30 дней
                refresh.set_exp(lifetime=datetime.timedelta(days=30))

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
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=["🔐Аутентификация"],
        operation_summary="Отправка кода для сброса пароля",
        operation_description="""
        Отправляет код для сброса пароля на email, если пользователь с таким
        адресом существует.
        """,
        request_body=ForgotPasswordSerializer,
        responses={
            200: openapi.Response('Код отправлен', examples={'application/json': {'success': True,
                                                                                  'message': 'Код для сброса пароля отправлен на ваш адрес электронной почты',
                                                                                  'email': 'test@example.com'}}),
            400: openapi.Response('Email не найден', examples={
                'application/json': {'success': False, 'errors': {'email': ['Пользователь с таким email не найден.']}}})
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
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=["🔐Аутентификация"],
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
    http_method_names = ['get', 'patch', 'put']
    lookup_field = 'pk'

    def get_object(self):
        """
        Возвращает профиль текущего пользователя, если он не администратор.
        """
        if self.request.user.is_authenticated and not self.request.user.is_staff:
            return get_object_or_404(UserProfile, user=self.request.user)
        return super().get_object()

    def get_permissions(self):
        """
        Разрешает администраторам просматривать все профили,
        а обычным пользователям — только свой.
        """
        if self.action == 'list':
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary='Получить данные профиля',
        operation_description='''
        Возвращает данные профиля текущего аутентифицированного пользователя.
        Администраторы могут получить любой профиль по его ID.
        '''
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary='Обновить данные профиля (частично)',
        operation_description='''
        Частично обновляет данные профиля текущего аутентифицированного пользователя.
        ''',
        request_body=UserProfileSerializer
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['👤 Профиль пользователя'],
        operation_summary='Полное обновление профиля',
        operation_description='''
        Полностью обновляет информацию о профиле. Доступно для авторизованных пользователей.
        ''',
        request_body=UserProfileSerializer
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

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


class ClientViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = ClientDetailSerializer
    permission_classes = [IsAdminUser]
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
            return [AllowAny()]
        return [IsAdminUser()]


class ClubViewSet(viewsets.ModelViewSet):
    queryset = Club.objects.all()
    serializer_class = ClubSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class TrainerViewSet(viewsets.ModelViewSet):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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