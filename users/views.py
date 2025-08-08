from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import UserProfile, ClassSchedule, Joinclub, Attendance, Payment
from .serializers import UserProfileSerializer, ClassScheduleSerializer, JoinclubSerializer, PaymentSerializer, AttendanceSerializer

from .serializers import (
    RegisterSerializer,
    VerifyCodeSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ClassScheduleSerializer,
    JoinclubSerializer,
    PaymentSerializer,
    AttendanceSerializer
)
from .utils import generate_and_send_code


class RegisterView(APIView):
    @swagger_auto_schema(
        tags=["Регистрация"],
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
        tags=["Регистрация"],
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
        tags=["Регистрация"],
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
        tags=["Регистрация"],
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
        tags=["Регистрация"],
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
        tags=["Регистрация"],
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

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Профиль'],
        operation_summary="Получить данные профиля пользователя",
        responses={200: openapi.Response('Данные профиля', UserProfileSerializer)}
    )
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
        tags=['Профиль'],
        operation_summary="Редактировать данные профиля пользователя",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response('Обноовленные данные профиля', UserProfileSerializer)
        }
    )
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
    tags=['Расписание'],
    operation_summary="Получить список расписаний",
        responses={
            200: 'Список расписаний',
            404: 'Расписания не найдены'
        }
    )
    def get(self, request):
        schedules = ClassSchedule.objects.all()
        serializer = ClassScheduleSerializer(schedules, many=True)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
    @swagger_auto_schema(
    tags=['Расписание'],
    operation_summary="Создать новое расписание",
        request_body=ClassScheduleSerializer,
        responses={
            201: 'Расписание создано',
            400: 'Неверные данные'
        }
    )
    def post(self, request):
        serializer = ClassScheduleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Расписание успешно создано", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class JoinclubView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        tags=['Записаться на кружок'],
        operation_summary="Получить список записей на кружки",
        responses={
            200: openapi.Response('Список записей', JoinclubSerializer(many=True)),
            404: 'Записи не найдены или профиль отсутствует'
        }
    )
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
        tags=['Записаться на кружок'],
        operation_summary="Создать новую запись на кружок",
        request_body=JoinclubSerializer,
        responses={
            201: openapi.Response('Запись создана', JoinclubSerializer),
            400: 'Неверные данные или запись уже существует'
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
    @swagger_auto_schema(
        tags=['Оплата'],
        operation_summary="Получить список оплат для конкретного Joinclub",
        responses={
            200: openapi.Response('Список оплат', PaymentSerializer(many=True)),
            404: 'Оплаты не найдены или Joinclub не существует'
        }
    )
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
        tags=['Оплата'],
        operation_summary="Создать новую оплату",
        request_body=PaymentSerializer,
        responses={
            201: openapi.Response('Оплата создана', PaymentSerializer),
            400: 'Неверные данные'
        }
    )
    def post(self, request, joinclub_id):
        try:
            joinclub_instance = Joinclub.objects.get(id=joinclub_id, user=request.user.userprofile)
            serializer = PaymentSerializer(data=request.data, context={'joinclub': joinclub_instance})
            if serializer.is_valid():
                payment = serializer.save(joinclub=joinclub_instance)
                joinclub_instance.payment_status = True
                joinclub_instance.payment_amount = payment.amount
                joinclub_instance.save()
                return Response({
                    'success': True,
                    'message': 'Оплата успешно добавлена',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Joinclub.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Запись Joinclub не найдена'
            }, status=status.HTTP_404_NOT_FOUND)

class AttendanceView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        tags=['Cписок посещаемости'],
        operation_summary="Получить список посещаемости",
        responses={
            200: 'Список посещаемости',
            404: 'Запись Joinclub не найдена'
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
    @swagger_auto_schema(
        tags=['Cписок посещаемости'],
        operation_summary="Добавить запись о посещении",
        request_body=AttendanceSerializer,
        responses={
            201: 'Успешно добавлено',
            400: 'Неверные данные'
        }
    )
    def post(self, request, joinclub_id):
        try:
            joinclub_instance = Joinclub.objects.get(id=joinclub_id, user=request.user.userprofile)
            serializer = AttendanceSerializer(data=request.data, context={'joinclub': joinclub_instance})
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Посещение успешно записано',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Joinclub.DoesNotExist:
            return Response({'success': False, 'message': 'Запись Joinclub не найдена'}, status=status.HTTP_404_NOT_FOUND)